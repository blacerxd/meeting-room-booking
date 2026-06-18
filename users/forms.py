from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth import password_validation
from .models import User


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    password1 = forms.CharField(
        label='Пароль',
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
        help_text='<ul class="password-requirements">'
                  '<li>Пароль не должен быть слишком похож на другие ваши персональные данные.</li>'
                  '<li>Пароль должен содержать минимум 8 символов.</li>'
                  '<li>Пароль не должен быть слишком простым и распространённым.</li>'
                  '<li>Пароль не может состоять только из цифр.</li>'
                  '</ul>',
    )

    password2 = forms.CharField(
        label='Подтверждение пароля',
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
        help_text='Введите тот же пароль ещё раз, чтобы избежать ошибок.',
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'phone')


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'phone')
