from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.contrib import messages

from .models import Booking
from rooms.models import Room

import logging


@login_required
def booking_list(request):
	bookings = Booking.objects.filter(user=request.user).order_by('-start_time')
	return render(request, 'bookings/list.html', {'bookings': bookings})


@login_required
def booking_detail(request, booking_id):
	booking = get_object_or_404(Booking, id=booking_id, user=request.user)
	return render(request, 'bookings/detail.html', {'booking': booking})

@login_required
def booking_cancel(request, booking_id):
	booking = get_object_or_404(
		Booking,
		id=booking_id,
		user=request.user,
		status__in=['pending', 'confirmed', 'active']
	)
	if request.method == 'POST':
		now = timezone.now()
		booking.status = 'cancelled'
		booking.cancelled_at = now
		booking.save()

		messages.success(request, 'Бронирование успешно отменено.')
		return redirect('bookings:booking_detail', booking_id=booking.id)

	return render(request, 'bookings/cancel_confirm.html', {'booking': booking})

@login_required
def booking_create(request, room_id):
	room = get_object_or_404(Room, id=room_id)

	if request.method == 'POST':
		start = request.POST.get('start_time')
		end = request.POST.get('end_time')
		participants = request.POST.get('participants_count') or 1
		purpose = request.POST.get('purpose', '')

		try:
			start_dt = parse_datetime(start)
			end_dt = parse_datetime(end)
		except Exception:
			messages.error(request, 'Неверный формат даты/времени')
			return redirect('bookings:booking_create', room_id=room.id)

		if not start_dt or not end_dt or start_dt >= end_dt:
			messages.error(request, 'Проверьте дату и время бронирования')
			return redirect('bookings:booking_create', room_id=room.id)

		conflict = Booking.objects.filter(room=room, start_time__lt=end_dt, end_time__gt=start_dt).exists()
		if conflict:
			messages.error(request, 'В выбранный интервал уже есть бронирование')
			return redirect('bookings:booking_create', room_id=room.id)

		booking = Booking.objects.create(
			user=request.user,
			room=room,
			start_time=start_dt,
			end_time=end_dt,
			participants_count=int(participants),
			purpose=purpose,
			status='confirmed'
		)

		messages.success(request, 'Бронирование создано')
		return redirect('bookings:booking_detail', booking_id=booking.id)

	return render(request, 'bookings/create.html', {'room': room})

logger = logging.getLogger(__name__) 

def create_booking(request):
    try:
        if request.method == 'POST':
            booking = Booking.objects.create(...)
            logger.info(
                f"Создана бронь #{booking.id} пользователем {request.user.username} "
                f"на комнату {booking.room.name}"
            )
            return redirect('bookings:list')
    except ValueError as e:
        logger.warning(f"Ошибка валидации при бронировании: {e}")
        messages.error(request, "Проверьте введённые данные")
    except Exception as e:
        logger.error(
            f"Ошибка при создании бронирования пользователем {request.user}: {e}",
            exc_info=True
        )
        messages.error(request, "Произошла ошибка. Попробуйте позже.")
    
    return render(request, 'bookings/create.html')


def cancel_booking(request, booking_id):
    try:
        booking = Booking.objects.get(id=booking_id)
        booking.delete()
        logger.info(f"Бронь #{booking_id} отменена пользователем {request.user.username}")
    except Booking.DoesNotExist:
        logger.warning(f"Попытка отмены несуществующей брони #{booking_id}")
    except Exception as e:
        logger.error(f"Ошибка отмены брони #{booking_id}: {e}", exc_info=True)
    
    return redirect('bookings:list')