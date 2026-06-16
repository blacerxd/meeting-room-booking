from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from .forms import CustomUserCreationForm, CustomUserChangeForm
from django.contrib import messages
from django.contrib.auth import logout


def register(request):
	if request.method == 'POST':
		form = CustomUserCreationForm(request.POST)
		if form.is_valid():
			user = form.save()
			login(request, user)
			messages.success(request, 'Добро пожаловать! Ваш аккаунт создан.')
			return redirect('home')
	else:
		form = CustomUserCreationForm()
	return render(request, 'users/register.html', {'form': form})


@login_required
def profile(request):
	return render(request, 'users/profile.html')


@login_required
def profile_edit(request):
	if request.method == 'POST':
		form = CustomUserChangeForm(request.POST, instance=request.user)
		if form.is_valid():
			form.save()
			messages.success(request, 'Профиль обновлён')
			return redirect('users:profile')
	else:
		form = CustomUserChangeForm(instance=request.user)
	return render(request, 'users/edit.html', {'form': form})


@login_required
def logout_view(request):
	logout(request)
	messages.info(request, 'Вы вышли из аккаунта')
	return redirect('home')
