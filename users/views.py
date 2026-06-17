import logging

from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import DatabaseError
from django.core.exceptions import ValidationError

from .forms import CustomUserCreationForm, CustomUserChangeForm

logger = logging.getLogger('users')


def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                login(request, user)
                logger.info("New user registered: %s (email=%s)", user.username, user.email)
                messages.success(request, 'Добро пожаловать! Ваш аккаунт создан.')
                return redirect('home')
            except (DatabaseError, ValidationError) as e:
                logger.error("Error saving new user registration: %s", e, exc_info=True)
                messages.error(request, 'Ошибка при создании аккаунта. Попробуйте позже.')
        else:
            logger.warning(
                "Registration form validation failed: %s",
                dict(form.errors.items())
            )
    else:
        form = CustomUserCreationForm()
    return render(request, 'users/register.html', {'form': form})


@login_required
def profile(request):
    logger.debug("User %s viewed their profile", request.user)
    return render(request, 'users/profile.html')


@login_required
def profile_edit(request):
    if request.method == 'POST':
        form = CustomUserChangeForm(request.POST, instance=request.user)
        if form.is_valid():
            try:
                form.save()
                logger.info("User %s updated their profile", request.user)
                messages.success(request, 'Профиль обновлён')
                return redirect('users:profile')
            except (DatabaseError, ValidationError) as e:
                logger.error("Error updating profile for user %s: %s", request.user, e, exc_info=True)
                messages.error(request, 'Ошибка при обновлении профиля.')
        else:
            logger.warning(
                "User %s profile edit form validation failed: %s",
                request.user,
                dict(form.errors.items())
            )
    else:
        form = CustomUserChangeForm(instance=request.user)
    return render(request, 'users/edit.html', {'form': form})


@login_required
def logout_view(request):
    username = request.user.username
    logout(request)
    logger.info("User %s logged out", username)
    messages.info(request, 'Вы вышли из аккаунта')
    return redirect('home')