from django.contrib import admin
from .models import Room


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'capacity',
        'location',
        'status',
        'qr_code_id',
    )

    fieldsets = (
        ('Основная информация', {
            'fields': (
                'name',
                'description',
                'capacity',
                'location',
            )
        }),
        ('QR код', {
            'fields': (
                'qr_code_id',
            )
        }),
        ('Статус', {
            'fields': (
                'status',
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
        'qr_code_id',
        'created_at',
        'updated_at',
    )

    search_fields = (
        'name',
        'location',
        'qr_code_id',
    )

    list_filter = (
        'status',
        'capacity',
    )

    ordering = ('name',)
