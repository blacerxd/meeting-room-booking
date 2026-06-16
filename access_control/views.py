from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import RoomAccessPolicy
from rooms.models import Room
from django.contrib.auth import get_user_model

User = get_user_model()


def staff_required(view_func):
	return user_passes_test(lambda u: u.is_active and u.is_staff)(view_func)


@login_required
@staff_required
def policies_list(request):
	policies = RoomAccessPolicy.objects.select_related('room', 'user').all()
	return render(request, 'access/policies_list.html', {'policies': policies})


@login_required
@staff_required
def assign_policy(request):
	if request.method == 'POST':
		room_id = request.POST.get('room')
		user_id = request.POST.get('user')
		access = request.POST.get('access_level', 'book')

		room = get_object_or_404(Room, id=room_id)
		user = get_object_or_404(User, id=user_id)

		policy, created = RoomAccessPolicy.objects.update_or_create(
			room=room, user=user,
			defaults={'access_level': access, 'is_active': True}
		)
		messages.success(request, 'Политика сохранена')
		return redirect('access:policies_list')

	rooms = Room.objects.all()
	users = User.objects.all()
	return render(request, 'access/assign.html', {'rooms': rooms, 'users': users})
