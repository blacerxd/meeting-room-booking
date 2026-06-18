from django.contrib import admin
from django.utils.html import format_html
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
        'image_preview',
    )

    fieldsets = (
        ('Основная информация', {
            'fields': (
                'name',
                'description',
                'capacity',
                'location',
                'image',
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
        'image_preview',
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

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height: 60px; border-radius: 8px; object-fit: cover;" />', obj.image.url)
        return format_html('<span style="color: #8d98b6;">Нет фото</span>')
    image_preview.short_description = 'Фото'
    image_preview.allow_tags = True
