from django.db import models
from django.contrib.auth import get_user_model
from rooms.models import Room

User = get_user_model()


class RoomAccessPolicy(models.Model):
    """
    Политика доступа к комнатам.
    Определяет, какие пользователи или группы имеют доступ к конкретным комнатам.
    """

    ACCESS_LEVEL = (
        ('view', 'Только просмотр'),
        ('book', 'Бронирование'),
        ('manage', 'Управление'),
    )

    id = models.AutoField(primary_key=True)
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='access_policies')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='room_access_policies')

    # Уровень доступа
    access_level = models.CharField(max_length=20, choices=ACCESS_LEVEL, default='book')

    # Активна ли политика
    is_active = models.BooleanField(default=True)

    # Период действия (опционально)
    valid_from = models.DateTimeField(null=True, blank=True)
    valid_until = models.DateTimeField(null=True, blank=True)

    # Технические поля
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Политика доступа'
        verbose_name_plural = 'Политики доступа'
        unique_together = ('room', 'user')
        ordering = ('room', 'user')

    def __str__(self):
        return f"{self.user.username} -> {self.room.name} ({self.access_level})"
