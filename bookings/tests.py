from django.test import TestCase
from django.utils import timezone
from datetime import timedelta

from users.models import User
from rooms.models import Room
from bookings.models import Booking


class BookingModelTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="nikita",
            password="12345678"
        )

        self.room = Room.objects.create(
            name="Room 1",
            capacity=10
        )

    def test_create_booking(self):
        booking = Booking.objects.create(user=self.user, room=self.room, start_time=timezone.now() + timedelta(minutes=5), end_time=timezone.now() + timedelta(hours=1))

        self.assertEqual(booking.user, self.user)
        self.assertEqual(booking.room, self.room)
# Create your tests here.
