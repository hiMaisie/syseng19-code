from django.test import TestCase
from django.utils import timezone
from match.models import Cohort,Participant,Programme,Tag
from match.serializers import ParticipantSerializer,UserSerializer
from datetime import timedelta
import json

class ParticipantSerializerTests(TestCase):

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
        self.cohort = Cohort.objects.create(
            programme = self.programme,
            createdBy = self.user
        )

    def test_serializer_valid_participant(self):
        data = {
            'isMentor': False
        }
        serializer = ParticipantSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        participant = serializer.save(user=self.user, cohort=self.cohort)
        self.assertFalse(participant.isMatched)
        self.assertTrue(participant.signUpDate <= timezone.now())

    def test_serializer_include_existing_tags(self):
        data = {
            'isMentor': True,
            'tags': [
                {'name': 'node.js'},
                {'name': 'sports'}
            ]
        }
        Tag.objects.create(name="node.js")
        Tag.objects.create(name="sports")
        serializer = ParticipantSerializer(data=data)
        if not serializer.is_valid():
            print(serializer.errors)
            self.fail()
        participant = serializer.save(user=self.user, cohort=self.cohort)
        self.assertTrue(len(participant.tags), 2)

    def test_serializer_include_nonexisting_tags(self):
        data = {
            'isMentor': True,
            'tags': [
                {'name': 'node.js'},
                {'name': 'sports'},
                {'name': 'something'}
            ]
        }
        Tag.objects.create(name="node.js")
        Tag.objects.create(name="sports")
        serializer = ParticipantSerializer(data=data)
        if not serializer.is_valid():
            print(serializer.errors)
            self.fail()
        participant = serializer.save(user=self.user, cohort=self.cohort)
        self.assertTrue(len(participant.tags), 3)

    def test_serializer_ignore_duplicate_tags(self):
        data = {
            'isMentor': True,
            'tags': [
                {'name': 'node.js'},
                {'name': 'sports'},
                {'name': 'sports'}
            ]
        }
        Tag.objects.create(name="node.js")
        Tag.objects.create(name="sports")
        serializer = ParticipantSerializer(data=data)
        if not serializer.is_valid():
            print(serializer.errors)
            self.fail()
        participant = serializer.save(user=self.user, cohort=self.cohort)
        self.assertTrue(len(participant.tags), 2)

    def test_serializer_is_mentor_not_set(self):
        data = {}
        serializer = ParticipantSerializer(data=data)
        self.assertFalse(serializer.is_valid())
