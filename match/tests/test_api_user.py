from datetime import timedelta
from django.urls import reverse
from django.utils import timezone
import json
from match.models import User
from match.serializers import UserSerializer
from oauth2_provider.compat import urlencode
from oauth2_provider.models import AccessToken, Application
from oauth2_provider.settings import oauth2_settings
from oauth2_provider.tests.test_utils import TestCaseUtils
from rest_framework import status
from rest_framework.test import APITestCase

class UserAPITests(TestCaseUtils, APITestCase):

    def setUp(self):
        self.test_user = User.objects.create_user("test@example.com", "test@example.com", "hunter2")
        self.admin_user = User.objects.create_user("admin@example.com", "admin@example.com", "hunter", is_staff=True)

        self.application = Application(
            name = "Django Test",
            user= self.admin_user,
            client_type = Application.CLIENT_PUBLIC,
            authorization_grant_type = Application.GRANT_PASSWORD,
        )
        self.application.save()

    def test_add_user(self):
        url = reverse('user-list')
        data = {"email": "jsmith@example.com", "password": "hunter23"}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 3)

    def test_add_user_with_profile(self):
        url = reverse('user-list')
        data = {
            "email": "jsmith@example.com",
            "password": "hunter23",
            "first_name": "John",
            "last_name": "Smith",
            "profile": {
                "joinDate": "2010-02-28",
                "position:": "CEO",
                "department": "yes",
                "dateOfBirth": "2000-01-01",
                "bio": "I like people, places and things!"
            }
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_get_users_if_admin(self):
        url = reverse('user-list')
        token = self._create_token(self.admin_user, 'read write admin')
        response = self.client.get(url, HTTP_AUTHORIZATION=self._get_auth_header(token=token.token))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_patch_user_if_admin(self):
        url = reverse('user-detail', kwargs={'pk': self.test_user.pk})
        token = self._create_token(self.admin_user, 'read write admin')
        data = {
            'first_name': 'Bill',
            'profile': {
                'position': 'Engineer'
            }
        }
        response = self.client.patch(url, data=data, format='json', HTTP_AUTHORIZATION=self._get_auth_header(token=token.token))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(json.loads(response.content.decode('utf-8'))['profile']['position'], 'Engineer')

    def test_get_me(self):
        url = reverse('user-me')
        token = self._create_token(self.test_user, 'read')
        serializer = UserSerializer(self.test_user)
        response = self.client.get(url, HTTP_AUTHORIZATION=self._get_auth_header(token=token.token))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(json.loads(response.content.decode('utf-8')), serializer.data)

    def test_patch_me(self):
        url = reverse('user-me')
        token = self._create_token(self.test_user, 'write')
        data = {
            'profile': {
                'bio': 'Some different bio'
            }
        }
        response = self.client.patch(url, data=data, format='json', HTTP_AUTHORIZATION=self._get_auth_header(token=token.token))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        res = json.loads(response.content.decode('utf-8'))
        self.assertEqual(res['profile']['bio'], 'Some different bio')
    ## HELPER FUNCTIONS

    def _get_auth_header(self, token=None):
        return "Bearer {0}".format(token or self.access_token.token)

    def _create_token(self,user,scope):
        return AccessToken.objects.create(
            user=user,
            token='123456789',
            application=self.application,
            expires=timezone.now() + timedelta(days=1),
            scope=scope
        )
