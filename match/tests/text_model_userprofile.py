from django.test import TestCase
from match.models import UserProfile
from django.contrib.auth.models import User

class UserProfileModelTests(TestCase):
    def test_user_creation(self):
        
