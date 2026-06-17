
from django.test import TestCase
from users.models import User


class UserModelTest(TestCase):

    def test_create_user(self):
        user = User.objects.create_user(
            username="nikita",
            email="nikita@test.com",
            password="12345678",
            phone="+79991234567"
        )

        self.assertEqual(user.username, "nikita")
        self.assertEqual(user.email, "nikita@test.com")
        self.assertTrue(user.check_password("12345678"))
# Create your tests here.
