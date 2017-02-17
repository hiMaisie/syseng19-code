from django.contrib.auth.models import User
from django.test import TestCase
from match.models import Programme

class ProgrammeModelTests(TestCase):
    def setUp(self):
        User.objects.create_user(
            username="test@example.com",
            email="test@example.com",
            password="hunter2",
            last_name="Smith",
            first_name="John"
        )
        self._userprofile = User.objects.get(email="test@example.com").userprofile

    def test_programme_created(self):
        Programme.objects.create(
            name="Test programme",
            description="A test programme",
            createdBy = self._userprofile
        )

        self.assertTrue(Programme.objects.get(name="Test programme"))
