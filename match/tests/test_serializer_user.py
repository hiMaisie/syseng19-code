from django.contrib.auth.models import User
from django.test import TestCase
from match.serializers import UserSerializer
import json

class UserSerializerTests(TestCase):

    def test_serialize_valid_user(self):
        data = {
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
        }
        serializer = UserSerializer(data=data)
        if not serializer.is_valid():
            self.fail(serializer.errors)
        serializer.save()
        user = User.objects.get(email='test@example.com')
        self.assertTrue(user)
        self.assertEqual(user.username, 'test@example.com')

    # should fail.
    def test_serializer_user_no_profile(self):
        data = {
            'email': 'test@example.com',
            'first_name': 'John',
            'last_name': 'Smith',
            'password': 'hunter2'
        }
        serializer = UserSerializer(data=data)
        if serializer.is_valid():
            self.fail("Profie not present, should have failed")

    def test_serializer_user_password_hashed(self):
        data = {
            'email': 'test@example.com',
            'first_name': 'John',
            'last_name': 'Smith',
            'password': 'hunter2',
            'profile': {}
        }
        serializer = UserSerializer(data=data)
        if not serializer.is_valid():
            self.fail(serializer.errors)
        serializer.save()
        user = User.objects.get(email='test@example.com')
        self.assertTrue(user)
        self.assertTrue(user.password)
        self.assertNotEqual(user.password, 'hunter2')
