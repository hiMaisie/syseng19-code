from datetime import date,timedelta
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
        userProfile = user.profile
        self.assertIsNotNone(userProfile)

    def test_user_profile_join_date_set_correctly(self):
        user = self._create_test_user()
        try:
            user.profile.joinDate = date.today() - timedelta(days=365)
            user.profile.full_clean()
        except ValidationError:
            self.fail("Error validating")

    def test_user_profile_join_date_set_in_future(self):
        user = self._create_test_user()
        with self.assertRaises(ValidationError):
            user.profile.joinDate = date.today() + timedelta(days=30)
            user.profile.full_clean()

    def test_user_profile_years_worked_calculated_correctly(self):
        profile = self._create_test_user().profile
        profile.joinDate = date.today() - timedelta(days=(366*2))
        self.assertEqual(profile.getYearsWorked(), 2)

    def test_user_profile_years_worked_less_than_one_year(self):
        profile = self._create_test_user().profile
        profile.joinDate = date.today() - timedelta(days=(20))
        self.assertEqual(profile.getYearsWorked(), 0)

    def test_user_profile_years_worked_null_when_join_date_null(self):
        profile = self._create_test_user().profile
        self.assertFalse(profile.getYearsWorked())

    def test_user_profile_dob_set_correctly(self):
        profile = self._create_test_user().profile
        try:
            profile.dateOfBirth = date.today() - timedelta(days=365)
            profile.full_clean()
        except ValidationError:
            self.fail("Date of birth validation failing valid input")

    # Users should not be able to be born in the future. Yet.
    def test_user_profile_dob_set_in_future(self):
        profile = self._create_test_user().profile
        with self.assertRaises(ValidationError):
            profile.dateOfBirth = date.today() + timedelta(days=1)
            profile.full_clean()

    def test_user_profile_age_calculated_correctly(self):
        profile = self._create_test_user().profile
        # set dob to >1 year ago. so age should be 1
        profile.dateOfBirth = date.today() - timedelta(days=368)
        self.assertEqual(profile.getAge(), 1)

    def test_user_profile_age_null_when_dob_null(self):
        profile = self._create_test_user().profile
        self.assertFalse(profile.getAge())

    def test_user_profile_deleted_on_user_deleted(self):
        user = self._create_test_user()
        User.objects.get(email="test@example.com")
        user.delete()

        # Test user profile deleted
        self.assertFalse(UserProfile.objects.all().count())

    # Creates a basic test user.
    def _create_test_user(self):
        return User.objects.create_user(username="test@example.com", email="test@example.com", password="hunter2", last_name="Smith", first_name="John")
