from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.db import models
from .models import Room
from bookings.models import RoomEntry, Booking
from access_control.models import RoomAccessPolicy
from django.utils.dateparse import parse_datetime


@login_required
def qr_scanner(request):
    """Страница с QR сканером для входа в комнаты"""
    return render(request, 'rooms/qr_scanner.html')


@login_required
@require_http_methods(["POST"])
def process_qr_code(request):
    """Обработка отсканированного QR кода"""
    qr_code = request.POST.get('qr_code', '').strip()

    if not qr_code:
        return JsonResponse({'success': False, 'message': 'QR код не распознан'})

    try:
        # Ищем комнату по QR коду
        room = Room.objects.get(qr_code_id=qr_code)
    except Room.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Комната не найдена'
        })

    # Проверяем, есть ли у пользователя доступ к комнате
    if not has_room_access(request.user, room):
        return JsonResponse({
            'success': False,
            'message': 'У вас нет доступа к этой комнате'
        })

    # Проверяем, есть ли активное бронирование
    booking = get_active_booking(request.user, room)

    # Создаём запись о входе
    entry = RoomEntry.objects.create(
        user=request.user,
        room=room,
        booking=booking,
        is_authorized=True,
    )

    return JsonResponse({
        'success': True,
        'message': f'Добро пожаловать в {room.name}!',
        'room': {
            'id': room.id,
            'name': room.name,
            'capacity': room.capacity,
            'location': room.location,
        },
        'entry_id': entry.id,
    })


@login_required
@require_http_methods(["POST"])
def exit_room(request, entry_id):
    """Фиксирует выход пользователя из комнаты"""
    entry = get_object_or_404(RoomEntry, id=entry_id, user=request.user)

    if entry.exit_time is not None:
        return JsonResponse({
            'success': False,
            'message': 'Выход уже зафиксирован'
        })

    entry.exit_time = timezone.now()
    entry.save()

    return JsonResponse({
        'success': True,
        'message': f'Вы вышли из комнаты {entry.room.name}'
    })


def has_room_access(user, room):
    """Проверяет, есть ли у пользователя доступ к комнате"""
    if user.is_superuser:
        return True

    # Проверяем политику доступа
    policy = RoomAccessPolicy.objects.filter(
        user=user,
        room=room,
        is_active=True
    ).first()

    if policy:
        # Проверяем период действия
        now = timezone.now()
        if policy.valid_from and policy.valid_from > now:
            return False
        if policy.valid_until and policy.valid_until < now:
            return False
        return True

    return False


def get_active_booking(user, room):
    """Получает активное бронирование пользователя в комнате"""
    now = timezone.now()
    booking = Booking.objects.filter(
        user=user,
        room=room,
        status__in=['confirmed', 'active'],
        start_time__lte=now,
        end_time__gte=now,
    ).first()

    if booking:
        booking.status = 'active'
        booking.save()

    return booking


@login_required
def room_list(request):
    """Список доступных комнат"""
    rooms = Room.objects.filter(status='available')

    # Применяем фильтры из GET: start, end, capacity, q
    start = request.GET.get('start')
    end = request.GET.get('end')
    capacity = request.GET.get('capacity')
    q = request.GET.get('q')

    # Фильтр по вместимости
    if capacity:
        try:
            cap = int(capacity)
            rooms = rooms.filter(capacity__gte=cap)
        except ValueError:
            pass

    # Фильтр по текстовому запросу (в описании/названии)
    if q:
        rooms = rooms.filter(models.Q(name__icontains=q) | models.Q(description__icontains=q))

    # Фильтр по доступности во времени: исключаем комнаты с конфликтующими бронированиями
    available_rooms = []
    start_dt = parse_datetime(start) if start else None
    end_dt = parse_datetime(end) if end else None

    for room in rooms:
        if not has_room_access(request.user, room):
            continue

        conflict = False
        if start_dt and end_dt:
            conflict = Booking.objects.filter(
                room=room,
                start_time__lt=end_dt,
                end_time__gt=start_dt,
                status__in=['confirmed', 'active']
            ).exists()

        if not conflict:
            available_rooms.append(room)

    return render(request, 'rooms/room_list.html', {
        'rooms': available_rooms,
    })


@login_required
def room_detail(request, room_id):
    """Детали комнаты и история входов"""
    room = get_object_or_404(Room, id=room_id)

    if not has_room_access(request.user, room):
        return redirect('rooms:room_list')

    entries = RoomEntry.objects.filter(room=room).order_by('-entry_time')[:50]
    bookings = Booking.objects.filter(room=room).order_by('-start_time')[:20]

    return render(request, 'rooms/room_detail.html', {
        'room': room,
        'entries': entries,
        'bookings': bookings,
    })


@login_required
def user_entries_api(request):
    """API для получения входов пользователя"""
    entries = RoomEntry.objects.filter(user=request.user).order_by('-entry_time')[:20]

    entries_data = []
    for entry in entries:
        entries_data.append({
            'id': entry.id,
            'room_name': entry.room.name,
            'location': entry.room.location,
            'entry_time': entry.entry_time.strftime('%d.%m.%Y %H:%M'),
            'exit_time': entry.exit_time.strftime('%d.%m.%Y %H:%M') if entry.exit_time else None,
        })

    return JsonResponse({'entries': entries_data})
