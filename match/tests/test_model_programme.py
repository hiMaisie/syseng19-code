from django.contrib.auth.models import User
from django.db.utils import IntegrityError
from django.test import TestCase
from django.utils import timezone
from match.models import Programme
from datetime import timedelta

class ProgrammeModelTests(TestCase):
    def setUp(self):
        self._user = User.objects.create_user(
            username="test@example.com",
            email="test@example.com",
            password="hunter2",
            last_name="Smith",
            first_name="John"
        )

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

    # activeCohort tests
    def test_active_cohort_is_none_when_no_cohorts(self):
        p = self._create_test_programme()
        self.assertIsNone(p.activeCohort)

    def test_active_cohort_is_set_when_open_cohort_with_spaces(self):
        p = self._create_test_programme()
        c1 = p.cohorts.create(
            openDate=timezone.now() - timedelta(days=7),
            createdBy=self._user
        )
        self.assertEqual(p.activeCohort, c1)
    
    def test_active_cohort_is_set_when_open_cohort_with_no_spaces(self):
        p = self._create_test_programme()
        c1 = p.cohorts.create(
            openDate=timezone.now() - timedelta(days=7),
            cohortSize=1,
            createdBy=self._user
        )
        c1.participants.create(
            user=self._user,
            isMentor=True
        )
        self.assertEqual(p.activeCohort, c1)

    def test_active_cohort_is_none_when_cohort_not_yet_open(self):
        p = self._create_test_programme()
        c1 = p.cohorts.create(
            openDate=timezone.now() + timedelta(days=2),
            createdBy=self._user
        )
        self.assertIsNone(p.activeCohort)   

    def test_active_cohort_is_none_when_cohort_closed(self):
        p = self._create_test_programme()
        c1 = p.cohorts.create(
            openDate=timezone.now() - timedelta(days=2),
            closeDate=timezone.now() - timedelta(days=1),
            createdBy=self._user
        )
        self.assertIsNone(p.activeCohort)
    
    def test_active_cohort_is_second_when_first_cohort_full(self):
        p = self._create_test_programme()
        c1 = p.cohorts.create(
            openDate=timezone.now() - timedelta(days=2),
            closeDate=timezone.now() + timedelta(days=7),
            cohortSize=1,
            createdBy=self._user
        )
        c2 = p.cohorts.create(
            openDate=timezone.now() - timedelta(days=2),
            closeDate=timezone.now() + timedelta(days=7),
            cohortSize=1,
            createdBy=self._user
        )
        c1.participants.create(
            user=self._user,
            isMentor=True,
        )
        self.assertEqual(p.activeCohort, c2)

    def test_active_cohort_is_earliest_when_more_than_one(self):
        p = self._create_test_programme()
        c1 = p.cohorts.create(
            openDate=timezone.now() - timedelta(days=7),
            closeDate=timezone.now() + timedelta(days=7),
            cohortSize=1,
            createdBy=self._user
        )
        c2 = p.cohorts.create(
            openDate=timezone.now() - timedelta(days=2),
            closeDate=timezone.now() + timedelta(days=7),
            cohortSize=1,
            createdBy=self._user
        )
        self.assertEqual(p.activeCohort, c1)
    
    def test_active_cohort_is_earliest_when_more_than_one_and_earliest_not_full(self):
        p = self._create_test_programme()
        c1 = p.cohorts.create(
            openDate=timezone.now() - timedelta(days=7),
            cohortSize=2,
            createdBy=self._user
        )
        c2 = p.cohorts.create(
            openDate=timezone.now() - timedelta(days=2),
            cohortSize=1,
            createdBy=self._user
        )
        c1.participants.create(
            user=self._user,
            isMentor=True
        )
        self.assertEqual(p.activeCohort, c1)

    def test_active_cohort_is_second_when_first_is_closed(self):
        p = self._create_test_programme()
        c1 = p.cohorts.create(
            openDate=timezone.now() - timedelta(days=7),
            closeDate=timezone.now() - timedelta(days=2),
            cohortSize=1,
            createdBy=self._user
        )
        c2 = p.cohorts.create(
            openDate=timezone.now() - timedelta(days=2),
            closeDate=timezone.now() + timedelta(days=7),
            cohortSize=1,
            createdBy=self._user
        )
        self.assertEqual(p.activeCohort, c2)

    def test_active_cohort_is_second_when_first_is_closed_and_second_is_full(self):
        p = self._create_test_programme()
        c1 = p.cohorts.create(
            openDate=timezone.now() - timedelta(days=7),
            closeDate=timezone.now() - timedelta(days=2),
            cohortSize=1,
            createdBy=self._user
        )
        c2 = p.cohorts.create(
            openDate=timezone.now() - timedelta(days=2),
            closeDate=timezone.now() + timedelta(days=7),
            cohortSize=1,
            createdBy=self._user
        )
        c2.participants.create(
            user=self._user,
            isMentor=True
        )
        self.assertEqual(p.activeCohort, c2)

    def test_active_cohort_is_second_when_both_active_and_second_opens_earlier(self):
        p = self._create_test_programme()
        c1 = p.cohorts.create(
            openDate=timezone.now() + timedelta(days=7),
            closeDate=timezone.now() + timedelta(days=2),
            cohortSize=1,
            createdBy=self._user
        )
        c2 = p.cohorts.create(
            openDate=timezone.now() - timedelta(days=9),
            closeDate=timezone.now() + timedelta(days=2),
            cohortSize=1,
            createdBy=self._user
        )
        self.assertEqual(p.activeCohort, c2)

    def test_active_cohort_is_second_when_first_is_not_open_and_second_is_full(self):
        p = self._create_test_programme()
        c1 = p.cohorts.create(
            openDate=timezone.now() + timedelta(days=2),
            closeDate=timezone.now() + timedelta(days=7),
            cohortSize=1,
            createdBy=self._user
        )
        c2 = p.cohorts.create(
            openDate=timezone.now() - timedelta(days=2),
            closeDate=timezone.now() + timedelta(days=7),
            cohortSize=1,
            createdBy=self._user
        )
        c2.participants.create(
            user=self._user,
            isMentor=True
        )
        self.assertEqual(p.activeCohort, c2)

    def test_active_cohort_is_none_when_no_cohorts_are_open(self):
        p = self._create_test_programme()
        c1 = p.cohorts.create(
            openDate=timezone.now() + timedelta(days=2),
            closeDate=timezone.now() + timedelta(days=7),
            cohortSize=1,
            createdBy=self._user
        )
        c2 = p.cohorts.create(
            openDate=timezone.now() + timedelta(days=2),
            closeDate=timezone.now() + timedelta(days=5),
            cohortSize=1,
            createdBy=self._user
        )
        self.assertIsNone(p.activeCohort)

    def test_active_cohort_is_earliest_when_both_are_full(self):
        p = self._create_test_programme()
        c1 = p.cohorts.create(
            openDate=timezone.now() - timedelta(days=2),
            closeDate=timezone.now() + timedelta(days=7),
            cohortSize=1,
            createdBy=self._user
        )
        c2 = p.cohorts.create(
            openDate=timezone.now() - timedelta(days=3),
            closeDate=timezone.now() + timedelta(days=5),
            cohortSize=1,
            createdBy=self._user
        )
        c1.participants.create(
            user=self._user,
            isMentor=True
        )
        c2.participants.create(
            user=self._user,
            isMentor=True
        )
        self.assertEqual(p.activeCohort, c2)

    # Creates a generic programme
    def _create_test_programme(self):
        return Programme.objects.create(
            name="Test programme",
            description="A test programme, used to unit test the programme model.",
            createdBy = self._user)
