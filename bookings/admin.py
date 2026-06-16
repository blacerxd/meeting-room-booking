from django.contrib import admin
from .models import Booking, RoomEntry


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'room',
        'start_time',
        'end_time',
        'status',
        'participants_count',
    )

    fieldsets = (
        ('Основная информация', {
            'fields': (
                'user',
                'room',
            )
        }),
        ('Время бронирования', {
            'fields': (
                'start_time',
                'end_time',
            )
        }),
        ('Детали', {
            'fields': (
                'purpose',
                'participants_count',
                'status',
            )
        }),
        ('Действия', {
            'fields': (
                'cancelled_at',
            )
        }),
        ('Технические данные', {
            'fields': (
                'created_at',
                'updated_at',
            ),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = (
        'created_at',
        'updated_at',
    )

    search_fields = (
        'user__username',
        'room__name',
        'purpose',
    )

    list_filter = (
        'status',
        'start_time',
        'room',
    )

    date_hierarchy = 'start_time'


@admin.register(RoomEntry)
class RoomEntryAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'room',
        'entry_time',
        'exit_time',
        'is_authorized',
    )

    fieldsets = (
        ('Информация о входе', {
            'fields': (
                'user',
                'room',
                'booking',
            )
        }),
        ('Время', {
            'fields': (
                'entry_time',
                'exit_time',
            )
        }),
        ('Статус', {
            'fields': (
                'is_authorized',
                'reason',
            )
        }),
        ('Сеть', {
            'fields': (
                'ip_address',
            ),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = (
        'entry_time',
        'room',
        'user',
    )

    search_fields = (
        'user__username',
        'room__name',
        'ip_address',
    )

    list_filter = (
        'is_authorized',
        'entry_time',
        'room',
    )

    date_hierarchy = 'entry_time'
