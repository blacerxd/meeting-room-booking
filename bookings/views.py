import logging

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.contrib import messages
from django.db import DatabaseError
from django.core.exceptions import ValidationError

from .models import Booking
from rooms.models import Room

logger = logging.getLogger('bookings')


@login_required
def booking_list(request):
    try:
        bookings = Booking.objects.filter(user=request.user).order_by('-start_time')
        logger.debug("User %s viewed their bookings list (found %d)", request.user, bookings.count())
        return render(request, 'bookings/list.html', {'bookings': bookings})
    except DatabaseError as e:
        logger.error("Database error when fetching bookings for user %s: %s", request.user, e, exc_info=True)
        messages.error(request, 'Произошла ошибка при загрузке списка бронирований.')
        return render(request, 'bookings/list.html', {'bookings': []})


@login_required
def booking_detail(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    logger.debug("User %s viewed booking #%d", request.user, booking.id)
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
        try:
            now = timezone.now()
            booking.status = 'cancelled'
            booking.cancelled_at = now
            booking.save()
            logger.info(
                "User %s cancelled booking #%d (room: %s, status was: %s)",
                request.user, booking.id, booking.room.name, booking.status
            )
            messages.success(request, 'Бронирование успешно отменено.')
        except (DatabaseError, ValidationError) as e:
            logger.error("Error cancelling booking #%d by user %s: %s", booking.id, request.user, e, exc_info=True)
            messages.error(request, 'Ошибка при отмене бронирования. Попробуйте позже.')
        return redirect('bookings:booking_detail', booking_id=booking.id)

    return render(request, 'bookings/cancel_confirm.html', {'booking': booking})


@login_required
def booking_create(request, room_id):
    room = get_object_or_404(Room, id=room_id)
    logger.debug("User %s opening booking creation for room %s", request.user, room.name)

    if request.method == 'POST':
        start = request.POST.get('start_time')
        end = request.POST.get('end_time')
        participants = request.POST.get('participants_count') or 1
        purpose = request.POST.get('purpose', '')

        try:
            start_dt = parse_datetime(start)
            end_dt = parse_datetime(end)
        except Exception as e:
            logger.warning("User %s provided invalid datetime format: start=%s, end=%s, error=%s", request.user, start, end, e)
            messages.error(request, 'Неверный формат даты/времени')
            return redirect('bookings:booking_create', room_id=room.id)

        if not start_dt or not end_dt:
            logger.warning("User %s provided empty datetime: start=%s, end=%s", request.user, start, end)
            messages.error(request, 'Дата и время обязательны для бронирования')
            return redirect('bookings:booking_create', room_id=room.id)

        if start_dt >= end_dt:
            logger.warning("User %s provided invalid time range: start=%s, end=%s", request.user, start_dt, end_dt)
            messages.error(request, 'Время начала должно быть раньше времени окончания')
            return redirect('bookings:booking_create', room_id=room.id)

        if start_dt <= timezone.now():
            logger.warning("User %s tried to book in the past: start=%s, now=%s", request.user, start_dt, timezone.now())
            messages.error(request, 'Нельзя бронировать на прошедшее время')
            return redirect('bookings:booking_create', room_id=room.id)

        try:
            conflict = Booking.objects.filter(
                room=room,
                start_time__lt=end_dt,
                end_time__gt=start_dt,
                status__in=['pending', 'confirmed', 'active'],
            ).exists()
        except DatabaseError as e:
            logger.error("Database error checking booking conflicts for room %s: %s", room.name, e, exc_info=True)
            messages.error(request, 'Ошибка при проверке доступности комнаты.')
            return redirect('bookings:booking_create', room_id=room.id)

        if conflict:
            logger.info("Booking conflict for user %s on room %s: %s - %s", request.user, room.name, start_dt, end_dt)
            messages.error(request, 'В выбранный интервал уже есть бронирование')
            return redirect('bookings:booking_create', room_id=room.id)

        try:
            booking = Booking.objects.create(
                user=request.user,
                room=room,
                start_time=start_dt,
                end_time=end_dt,
                participants_count=int(participants),
                purpose=purpose,
                status='confirmed'
            )
            logger.info(
                "User %s created booking #%d for room %s: %s - %s, participants=%s",
                request.user, booking.id, room.name, start_dt, end_dt, participants
            )
            messages.success(request, 'Бронирование создано')
            return redirect('bookings:booking_detail', booking_id=booking.id)
        except (DatabaseError, ValidationError, ValueError) as e:
            logger.error("Error creating booking for user %s on room %s: %s", request.user, room.name, e, exc_info=True)
            messages.error(request, 'Ошибка при создании бронирования. Попробуйте позже.')
            return redirect('bookings:booking_create', room_id=room.id)

    return render(request, 'bookings/create.html', {'room': room})