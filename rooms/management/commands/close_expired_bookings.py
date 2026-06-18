"""
Management command для автоматического закрытия истекших бронирований
и фиксации выхода из переговорной по окончании времени бронирования.

Запуск: python manage.py close_expired_bookings
Рекомендуется добавить в cron: */1 * * * * (каждую минуту)
"""
import logging
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import DatabaseError
from django.db.models import Q

from bookings.models import Booking, RoomEntry

logger = logging.getLogger('bookings')


class Command(BaseCommand):
    help = 'Закрывает истекшие бронирования и фиксирует автоматический выход из комнаты'

    def handle(self, *args, **options):
        now = timezone.now()
        self.stdout.write(f"[{now.strftime('%d.%m.%Y %H:%M:%S')}] Проверка истекших бронирований...")

        # 1. Находим все активные/подтверждённые бронирования, время которых истекло
        expired_bookings = Booking.objects.filter(
            status__in=['active', 'confirmed'],
            end_time__lte=now,
        )

        expired_count = expired_bookings.count()
        self.stdout.write(f"  Найдено истекших бронирований: {expired_count}")

        if expired_count == 0:
            return

        for booking in expired_bookings:
            try:
                # 2. Меняем статус бронирования на 'completed'
                old_status = booking.status
                booking.status = 'completed'
                booking.save(update_fields=['status'])
                logger.info(
                    "Booking #%d auto-completed (status changed: %s -> completed, "
                    "end_time=%s, now=%s)",
                    booking.id, old_status, booking.end_time, now
                )
                self.stdout.write(
                    f"  ✓ Бронирование #{booking.id} ({booking.room.name}) "
                    f"завершено (статус: {old_status} -> completed)"
                )

                # 3. Находим все входы в комнату по этому бронированию без выхода
                open_entries = RoomEntry.objects.filter(
                    booking=booking,
                    exit_time__isnull=True,
                )

                for entry in open_entries:
                    # Ставим exit_time = end_time бронирования
                    # Если пользователь зашёл, но не вышел — выход в момент окончания брони
                    auto_exit_time = booking.end_time
                    entry.exit_time = auto_exit_time
                    entry.save(update_fields=['exit_time'])
                    logger.info(
                        "RoomEntry #%d auto-exit set to %s for booking #%d",
                        entry.id, auto_exit_time, booking.id
                    )
                    self.stdout.write(
                        f"    → Вход #{entry.id} (user: {entry.user}) "
                        f"закрыт, exit_time = {auto_exit_time}"
                    )

            except DatabaseError as e:
                logger.error(
                    "Error auto-closing booking #%d: %s",
                    booking.id, e, exc_info=True
                )
                self.stdout.write(
                    self.style.ERROR(
                        f"  ✗ Ошибка при закрытии бронирования #{booking.id}: {e}"
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"Обработано бронирований: {expired_count}"
            )
        )