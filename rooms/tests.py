from django.test import TestCase

# Create your tests here.
from rooms.models import Room


class RoomModelTest(TestCase):

    def test_room_creation(self):
        room = Room.objects.create(
            name="Переговорная №1",
            capacity=10
        )

        self.assertEqual(room.name, "Переговорная №1")
