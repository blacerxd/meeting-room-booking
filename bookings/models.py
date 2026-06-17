from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from rooms.models import Room
from django.core.exceptions import ValidationError

User = get_user_model()


class Booking(models.Model):
    BOOKING_STATUS = (
        ('pending', 'В ожидании'),
        ('confirmed', 'Подтверждена'),
        ('active', 'Активна'),
        ('completed', 'Завершена'),
        ('cancelled', 'Отменена'),
    )

    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='bookings')

    # Время бронирования
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()

    # Статус
    status = models.CharField(max_length=20, choices=BOOKING_STATUS, default='pending')

    # Дополнительная информация
    purpose = models.CharField(max_length=500, blank=True)
    participants_count = models.PositiveIntegerField(default=1)

    # Технические поля
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Бронирование'
        verbose_name_plural = 'Бронирования'
        ordering = ('-start_time',)
        unique_together = ('room', 'start_time', 'end_time')

    def __str__(self):
        return f"{self.user.username} -> {self.room.name} ({self.start_time.strftime('%d.%m %H:%M')})"

    def is_active_now(self):
        """Проверка, активно ли бронирование в данный момент"""
        now = timezone.now()
        return self.start_time <= now <= self.end_time and self.status in ['confirmed', 'active']
    
    def clean(self):
        super().clean()

        if not self.start_time or not self.end_time:
            now = timezone.now()
        
        if self.start_time >= self.end_time:
            raise ValidationError('Время начала не можеть быть позже или равно времени окончания')
        
        if not self.pk and self.start_time < now:
            raise ValidationError('Нельзя забронировать на уже прошедшее время')
        
        if self.room.status != 'available':
            raise ValidationError(f'Комната не достпуна для бронирования (Статус: {self.room.get_status_display()}).')
        
        if self.participants_count > self.room.capacity:
            raise ValidationError(f'Количество участниковв ({self.participants_count})')
        
        conflicts = Booking.objects.filter(
            room=self.room,
            start_time__lt=self.end_time,
            end_time__gt=self.start_time
        ).exclude(status='cancelled')

        if self.pk:
            conflicts = conflicts.exclude(pk=self.pk)

        if conflicts.exists():
            raise ValidationError('В выбраном интервале времени комната уже забронирована')
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class RoomEntry(models.Model):
    """Логирование входов в комнаты через QR коды"""

    id = models.AutoField(primary_key=True)
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='entries')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='room_entries')
    booking = models.ForeignKey(Booking, on_delete=models.SET_NULL, null=True, blank=True, related_name='entries')

    # Время входа и выхода
    entry_time = models.DateTimeField(auto_now_add=True)
    exit_time = models.DateTimeField(null=True, blank=True)

    # IP адрес сканирующего устройства (опционально)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    # Статус входа
    is_authorized = models.BooleanField(default=True)
    reason = models.CharField(max_length=200, blank=True)

    class Meta:
        verbose_name = 'Вход в комнату'
        verbose_name_plural = 'Входы в комнаты'
        ordering = ('-entry_time',)

    def __str__(self):
        user_info = self.user.username if self.user else 'Неизвестный пользователь'
        return f"{user_info} -> {self.room.name} ({self.entry_time.strftime('%d.%m %H:%M')})"
