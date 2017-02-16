from django.test import TestCase
from match.models import UserProfile
from django.contrib.auth.models import User

class UserProfileModelTests(TestCase):

    def test_user_created(self):
        User.objects.create_user(username="test@example.com", email="test@example.com", password="hunter2", last_name="Smith", first_name="John")
        user = User.objects.get(email="test@example.com")
        self.assertEqual(user.last_name, "Smith")

    # Ensure a user profile is created when a user is created.
    def test_user_profile_created(self):
        User.objects.create_user(username="test@example.com", email="test@example.com", password="hunter2", last_name="Smith", first_name="John")
        userProfile = User.objects.get(email="test@example.com").userprofile
        self.assertIsNotNone(userProfile)
