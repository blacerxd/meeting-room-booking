import logging

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db import DatabaseError, IntegrityError
from django.core.exceptions import ValidationError, PermissionDenied

from .models import RoomAccessPolicy
from rooms.models import Room
from django.contrib.auth import get_user_model

User = get_user_model()
logger = logging.getLogger('access_control')


def staff_required(view_func):
    return user_passes_test(lambda u: u.is_active and u.is_staff)(view_func)


@login_required
@staff_required
def policies_list(request):
    try:
        policies = RoomAccessPolicy.objects.select_related('room', 'user').all()
        logger.debug("Staff user %s viewed all access policies (found %d)", request.user, policies.count())
        return render(request, 'access/policies_list.html', {'policies': policies})
    except DatabaseError as e:
        logger.error("Database error fetching access policies: %s", e, exc_info=True)
        messages.error(request, 'Ошибка при загрузке политик доступа.')
        return render(request, 'access/policies_list.html', {'policies': []})


@login_required
@staff_required
def assign_policy(request):
    if request.method == 'POST':
        room_id = request.POST.get('room')
        user_id = request.POST.get('user')
        access = request.POST.get('access_level', 'book')

        try:
            room = get_object_or_404(Room, id=room_id)
            target_user = get_object_or_404(User, id=user_id)

            policy, created = RoomAccessPolicy.objects.update_or_create(
                room=room, user=target_user,
                defaults={'access_level': access, 'is_active': True}
            )

            if created:
                logger.info(
                    "Staff user %s created access policy for user %s on room %s (level=%s)",
                    request.user, target_user.username, room.name, access
                )
            else:
                logger.info(
                    "Staff user %s updated access policy for user %s on room %s (level=%s)",
                    request.user, target_user.username, room.name, access
                )

            messages.success(request, 'Политика сохранена')
            return redirect('access:policies_list')

        except (DatabaseError, IntegrityError, ValidationError) as e:
            logger.error(
                "Error saving access policy by staff %s for user_id=%s, room_id=%s: %s",
                request.user, user_id, room_id, e, exc_info=True
            )
            messages.error(request, 'Ошибка при сохранении политики доступа.')

    try:
        rooms = Room.objects.all()
        users = User.objects.all()
    except DatabaseError as e:
        logger.error("Database error fetching rooms/users for policy assign: %s", e, exc_info=True)
        messages.error(request, 'Ошибка при загрузке данных.')
        return render(request, 'access/assign.html', {'rooms': [], 'users': []})

    return render(request, 'access/assign.html', {'rooms': rooms, 'users': users})