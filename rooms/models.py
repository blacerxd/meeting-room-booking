from django.db import models
import uuid
import os


class Room(models.Model):
    ROOM_STATUS = (
        ('available', 'Доступна'),
        ('maintenance', 'На обслуживании'),
        ('unavailable', 'Недоступна'),
    )

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    capacity = models.PositiveIntegerField()
    location = models.CharField(max_length=200, blank=True)
    image = models.ImageField(upload_to='rooms/', blank=True, null=True, help_text='Фотография переговорной комнаты')

    qr_code_id = models.CharField(max_length=36, unique=True, default=uuid.uuid4)
    status = models.CharField(max_length=20, choices=ROOM_STATUS, default='available')
    image = models.ImageField(upload_to='rooms/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Переговорная'
        verbose_name_plural = 'Переговорные'
        ordering = ('name',)

    def __str__(self):
        return f"{self.name} (вместимость: {self.capacity})"


