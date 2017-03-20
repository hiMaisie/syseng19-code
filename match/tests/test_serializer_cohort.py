from django.test import TestCase
from django.utils import timezone
from match.models import Cohort,Programme
from match.serializers import CohortSerializer,UserSerializer
from datetime import timedelta
import json

class UserSerializerTests(TestCase):

    def setUp(self):
        user_s = UserSerializer(data={
            'email': 'test@example.com',
            'first_name': 'John',
            'last_name': 'Smith',
            'password': 'hunter2',
            'profile': {
                'position': 'Consultant',
                'department': 'HR',
                'dateOfBirth': '2000-11-30',
                'joinDate': '2016-01-03',
                'bio': 'I like people, places and things'
            }
        })
        user_s.is_valid()
        self.user = user_s.save()
        self.programme = Programme.objects.create(
            name = 'Test Programme',
            description = 'This is a test programme.',
            defaultCohortSize = 100,
            createdBy = self.user)

    def test_serializer_valid_cohort(self):
        data = {
            'cohortSize': 200,
        }
        serializer = CohortSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        # since it's only me developing I won't worry too much about the 
        # ease of use for now
        cohort = serializer.save(createdBy=self.user, programme=self.programme)
        self.assertTrue(cohort.openDate, timezone.now())
        self.assertTrue(cohort.closeDate, timezone.now() + timedelta(days=14))
        self.assertTrue(cohort.matchDate, timezone.now() + timedelta(days=21))
