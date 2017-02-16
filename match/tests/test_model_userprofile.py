from datetime import timedelta
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone
from match.models import UserProfile

class UserProfileModelTests(TestCase):

    def test_user_created(self):
        user = self._create_test_user()
        self.assertEqual(user.last_name, "Smith")

    # Ensure a user profile is created when a user is created.
    def test_user_profile_created(self):
        user = self._create_test_user()
        userProfile = user.userprofile
        self.assertIsNotNone(userProfile)

    def test_user_profile_join_date_set_correctly(self):
        user = self._create_test_user()
        try:
            user.userprofile.joinDate = timezone.now() - timedelta(days=365)
            user.userprofile.full_clean()
        except ValidationError:
            self.fail("Error validating")

    def test_user_profile_join_date_set_in_future(self):
        user = self._create_test_user()
        with self.assertRaises(ValidationError):
            user.userprofile.joinDate = timezone.now() + timedelta(days=30)
            user.userprofile.full_clean()

    def test_user_profile_dob_set_correctly(self):
        userprofile = self._create_test_user().userprofile
        try:
            userprofile.dateOfBirth = timezone.now() - timedelta(days=365)
            userprofile.full_clean()
        except ValidationError:
            self.fail("Date of birth validation failing valid input")

    # Users should not be able to be born in the future. Yet.
    def test_user_profile_dob_set_in_future(self):
        userprofile = self._create_test_user().userprofile
        with self.assertRaises(ValidationError):
            userprofile.dateOfBirth = timezone.now() + timedelta(days=1)
            userprofile.full_clean()

    def test_user_profile_deleted_on_user_deleted(self):
        user = self._create_test_user()
        User.objects.get(email="test@example.com")
        user.delete()

        # Test user profile deleted
        self.assertFalse(UserProfile.objects.all().count())

    # Creates a basic test user.
    def _create_test_user(self):
        User.objects.create_user(username="test@example.com", email="test@example.com", password="hunter2", last_name="Smith", first_name="John")
        return User.objects.get(email="test@example.com")
