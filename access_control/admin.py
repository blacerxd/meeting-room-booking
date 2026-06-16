from django.contrib import admin
from .models import RoomAccessPolicy


@admin.register(RoomAccessPolicy)
class RoomAccessPolicyAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'room',
        'access_level',
        'is_active',
        'valid_from',
        'valid_until',
    )

    fieldsets = (
        ('Основная информация', {
            'fields': (
                'user',
                'room',
            )
        }),
        ('Права доступа', {
            'fields': (
                'access_level',
                'is_active',
            )
        }),
        ('Период действия', {
            'fields': (
                'valid_from',
                'valid_until',
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
    )

    list_filter = (
        'access_level',
        'is_active',
        'room',
    )
