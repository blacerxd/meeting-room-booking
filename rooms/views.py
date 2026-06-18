import logging

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.db import models, DatabaseError
from django.core.exceptions import ValidationError, PermissionDenied
from .models import Room
from bookings.models import RoomEntry, Booking
from access_control.models import RoomAccessPolicy
from django.contrib import messages
from django.utils.dateparse import parse_datetime

logger = logging.getLogger('rooms')


@login_required
def qr_scanner(request):
    """Страница с QR сканером для входа в комнаты"""
    logger.debug("User %s opened QR scanner page", request.user)
    return render(request, 'rooms/qr_scanner.html')


@login_required
@require_http_methods(["POST"])
def process_qr_code(request):
    """Обработка отсканированного QR кода"""
    qr_code = request.POST.get('qr_code', '').strip()

    if not qr_code:
        logger.warning("User %s submitted empty QR code", request.user)
        return JsonResponse({'success': False, 'message': 'QR код не распознан'})

    try:
        room = Room.objects.get(qr_code_id=qr_code)
        logger.debug("User %s scanned QR for room %s (qr_code=%s)", request.user, room.name, qr_code)
    except Room.DoesNotExist:
        logger.warning("User %s scanned unknown QR code: %s", request.user, qr_code)
        return JsonResponse({
            'success': False,
            'message': 'Комната не найдена'
        })
    except DatabaseError as e:
        logger.error("Database error looking up room by QR code %s: %s", qr_code, e, exc_info=True)
        return JsonResponse({
            'success': False,
            'message': 'Ошибка при поиске комнаты'
        })

    # Для суперпользователей — доступ без проверок
    if request.user.is_superuser:
        booking = None
        # Создаём запись о входе
        try:
            entry = RoomEntry.objects.create(
                user=request.user,
                room=room,
                booking=None,
                is_authorized=True,
            )
            logger.info("Superuser %s entered room %s (entry #%d)", request.user, room.name, entry.id)
        except (DatabaseError, ValidationError) as e:
            logger.error("Error creating room entry for superuser %s in room %s: %s", request.user, room.name, e, exc_info=True)
            return JsonResponse({'success': False, 'message': 'Ошибка при регистрации входа'})
        return JsonResponse({
            'success': True,
            'message': f'Добро пожаловать в {room.name}!',
            'room': {'id': room.id, 'name': room.name, 'capacity': room.capacity, 'location': room.location},
            'entry_id': entry.id,
        })

    # Сначала проверяем бронирование (включая доступ за 10 минут до начала)
    try:
        booking = get_active_booking(request.user, room)
    except DatabaseError as e:
        logger.error("Database error checking active booking for user %s in room %s: %s", request.user, room.name, e, exc_info=True)
        return JsonResponse({'success': False, 'message': 'Ошибка при проверке бронирования'})

    # Если есть бронирование — доступ разрешён
    if booking:
        try:
            entry = RoomEntry.objects.create(
                user=request.user,
                room=room,
                booking=booking,
                is_authorized=True,
            )
            logger.info("User %s entered room %s via booking #%d (entry #%d)", request.user, room.name, booking.id, entry.id)
        except (DatabaseError, ValidationError) as e:
            logger.error("Error creating room entry for user %s in room %s: %s", request.user, room.name, e, exc_info=True)
            return JsonResponse({'success': False, 'message': 'Ошибка при регистрации входа'})
        return JsonResponse({
            'success': True,
            'message': f'Добро пожаловать в {room.name}!',
            'room': {'id': room.id, 'name': room.name, 'capacity': room.capacity, 'location': room.location},
            'entry_id': entry.id,
        })

    # Если бронирования нет — проверяем политику доступа
    if not has_room_access(request.user, room):
        logger.warning("User %s denied access to room %s — no active booking and no access policy", request.user, room.name)
        return JsonResponse({
            'success': False,
            'message': 'У вас нет доступа к этой комнате. Забронируйте комнату сначала.'
        })
    else:
        booking = None

    try:
        # Создаём запись о входе
        entry = RoomEntry.objects.create(
            user=request.user,
            room=room,
            booking=booking,
            is_authorized=True,
        )
        logger.info(
            "User %s entered room %s (entry #%d, booking=%s)",
            request.user, room.name, entry.id, booking.id if booking else None
        )
    except (DatabaseError, ValidationError) as e:
        logger.error("Error creating room entry for user %s in room %s: %s", request.user, room.name, e, exc_info=True)
        return JsonResponse({
            'success': False,
            'message': 'Ошибка при регистрации входа'
        })

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
    try:
        entry = get_object_or_404(RoomEntry, id=entry_id, user=request.user)
    except DatabaseError as e:
        logger.error("Database error fetching entry #%d for user %s: %s", entry_id, request.user, e, exc_info=True)
        return JsonResponse({
            'success': False,
            'message': 'Ошибка при поиске записи входа'
        })

    if entry.exit_time is not None:
        logger.warning("User %s tried to exit entry #%d which already has exit_time=%s", request.user, entry_id, entry.exit_time)
        return JsonResponse({
            'success': False,
            'message': 'Выход уже зафиксирован'
        })

    try:
        entry.exit_time = timezone.now()
        entry.save()
        logger.info("User %s exited room %s (entry #%d)", request.user, entry.room.name, entry.id)
    except (DatabaseError, ValidationError) as e:
        logger.error("Error saving exit for entry #%d by user %s: %s", entry_id, request.user, e, exc_info=True)
        return JsonResponse({
            'success': False,
            'message': 'Ошибка при фиксации выхода'
        })

    return JsonResponse({
        'success': True,
        'message': f'Вы вышли из комнаты {entry.room.name}'
    })


def has_room_access(user, room):
    """Проверяет, есть ли у пользователя доступ к комнате"""
    if user.is_superuser:
        return True

    try:
        policy = RoomAccessPolicy.objects.filter(
            user=user,
            room=room,
            is_active=True
        ).first()
    except DatabaseError as e:
        logger.error("Database error checking access policy for user %s in room %s: %s", user, room.name, e, exc_info=True)
        return False

    if policy:
        now = timezone.now()
        if policy.valid_from and policy.valid_from > now:
            logger.debug("Access policy for user %s in room %s is not yet valid (valid_from=%s)", user, room.name, policy.valid_from)
            return False
        if policy.valid_until and policy.valid_until < now:
            logger.debug("Access policy for user %s in room %s has expired (valid_until=%s)", user, room.name, policy.valid_until)
            return False
        return True

    logger.debug("No access policy found for user %s in room %s", user, room.name)
    return False


def get_active_booking(user, room):
    """Получает активное бронирование пользователя в комнате.
    Доступ открывается за 10 минут до начала бронирования."""
    now = timezone.now()
    from django.utils.timezone import timedelta
    try:
        # Разрешаем вход за 10 минут до начала бронирования
        # start_time <= now + 10min  → можно войти за 10 мин до начала
        # end_time >= now            → бронирование ещё не закончилось
        early_access_threshold = now + timedelta(minutes=10)
        logger.debug(
            "Checking booking for user %s in room %s: now=%s, early_access_threshold=%s",
            user, room.name, now, early_access_threshold
        )
        booking = Booking.objects.filter(
            user=user,
            room=room,
            status__in=['confirmed', 'active'],
            start_time__lte=early_access_threshold,
            end_time__gte=now,
        ).first()
    except DatabaseError as e:
        logger.error("Database error fetching active booking for user %s in room %s: %s", user, room.name, e, exc_info=True)
        return None

    if booking:
        logger.info(
            "User %s can access room %s: booking #%d from %s to %s (early_access=10min)",
            user, room.name, booking.id, booking.start_time, booking.end_time
        )
        try:
            booking.status = 'active'
            booking.save()
            logger.debug("Updated booking #%d status to 'active' for user %s in room %s", booking.id, user, room.name)
        except (DatabaseError, ValidationError) as e:
            logger.error("Error updating booking #%d status to active: %s", booking.id, e, exc_info=True)
    else:
        logger.debug(
            "User %s has NO active booking for room %s (now=%s, threshold=%s)",
            user, room.name, now, early_access_threshold
        )

    return booking


@login_required
def room_list(request):
    """Список доступных комнат"""
    try:
        rooms = Room.objects.filter(status='available')
    except DatabaseError as e:
        logger.error("Database error fetching available rooms: %s", e, exc_info=True)
        messages.error(request, 'Ошибка при загрузке списка комнат.')
        return render(request, 'rooms/room_list.html', {'rooms': []})

    start = request.GET.get('start')
    end = request.GET.get('end')
    capacity = request.GET.get('capacity')
    q = request.GET.get('q')

    if capacity:
        try:
            cap = int(capacity)
            rooms = rooms.filter(capacity__gte=cap)
        except ValueError:
            logger.warning("User %s provided invalid capacity filter: %s", request.user, capacity)

    if q:
        rooms = rooms.filter(
            models.Q(name__icontains=q) |
            models.Q(description__icontains=q)
        )
        logger.debug("User %s searched rooms with query: %s", request.user, q)

    available_rooms = []
    start_dt = parse_datetime(start) if start else None
    end_dt = parse_datetime(end) if end else None

    for room in rooms:
        if not has_room_access(request.user, room):
            continue

        conflict = False
        if start_dt and end_dt:
            from django.utils.timezone import timedelta
            try:
                # 10-min buffer for conflict check
                conflict = Booking.objects.filter(
                    room=room,
                    start_time__lt=end_dt + timedelta(minutes=10),
                    end_time__gt=start_dt - timedelta(minutes=10),
                    status__in=['confirmed', 'active']
                ).exists()
            except DatabaseError as e:
                logger.error("Database error checking booking conflict for room %s: %s", room.name, e, exc_info=True)
                continue

        if not conflict:
            available_rooms.append(room)

    logger.debug("User %s viewed room list: found %d available rooms out of %d total", request.user, len(available_rooms), rooms.count())

    return render(request, 'rooms/room_list.html', {
        'rooms': available_rooms,
    })


@login_required
def room_detail(request, room_id):
    """Детали комнаты и история входов"""
    try:
        room = get_object_or_404(Room, id=room_id)
    except DatabaseError as e:
        logger.error("Database error fetching room #%d: %s", room_id, e, exc_info=True)
        messages.error(request, 'Ошибка при загрузке информации о комнате.')
        return redirect('rooms:room_list')

    if not has_room_access(request.user, room):
        logger.warning("User %s tried to access room #%d without permission", request.user, room_id)
        return redirect('rooms:room_list')

    try:
        entries = RoomEntry.objects.filter(room=room).order_by('-entry_time')[:50]
        bookings = Booking.objects.filter(room=room).order_by('-start_time')[:20]
    except DatabaseError as e:
        logger.error("Database error fetching entries/bookings for room %s: %s", room.name, e, exc_info=True)
        messages.error(request, 'Ошибка при загрузке истории.')
        return render(request, 'rooms/room_detail.html', {
            'room': room,
            'entries': [],
            'bookings': [],
        })

    logger.debug("User %s viewed room detail for %s (entries=%d, bookings=%d)", request.user, room.name, len(entries), len(bookings))

    return render(request, 'rooms/room_detail.html', {
        'room': room,
        'entries': entries,
        'bookings': bookings,
    })


@login_required
def user_entries_api(request):
    """API для получения входов пользователя"""
    try:
        entries = RoomEntry.objects.filter(user=request.user).order_by('-entry_time')[:20]
    except DatabaseError as e:
        logger.error("Database error fetching entries for user %s: %s", request.user, e, exc_info=True)
        return JsonResponse({'entries': []})

    entries_data = []
    for entry in entries:
        entries_data.append({
            'id': entry.id,
            'room_name': entry.room.name,
            'location': entry.room.location,
            'entry_time': entry.entry_time.strftime('%d.%m.%Y %H:%M'),
            'exit_time': entry.exit_time.strftime('%d.%m.%Y %H:%M') if entry.exit_time else None,
        })

    logger.debug("User %s requested entries API: returned %d entries", request.user, len(entries_data))
    return JsonResponse({'entries': entries_data})