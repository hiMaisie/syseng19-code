from django.contrib.auth.models import User
from django.db.utils import IntegrityError
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
        self._create_test_programme()
        self.assertTrue(Programme.objects.get(name="Test programme"))

    def test_programme_requires_user(self):
        with self.assertRaises(IntegrityError):
            Programme.objects.create(
                name="Programme",
                description="A test programme"
            )

    def test_default_cohort_size_implicitly_set(self):
        self.assertEqual(self._create_test_programme().defaultCohortSize, 100)

    # Creates a generic programme
    def _create_test_programme(self):
        return Programme.objects.create(
            name="Test programme",
            description="A test programme, used to unit test the programme model.",
            createdBy = self._userprofile
        )
