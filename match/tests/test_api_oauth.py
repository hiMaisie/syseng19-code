from datetime import datetime,timedelta
from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from oauth2_provider.compat import urlencode
from oauth2_provider.models import get_application_model, AccessToken, RefreshToken
from oauth2_provider.settings import oauth2_settings
from oauth2_provider.tests.test_utils import TestCaseUtils
from rest_framework import status
import base64
import json

# Sourced from https://github.com/evonove/django-oauth-toolkit/blob/master/oauth2_provider/tests/test_token_revocation.py

Application = get_application_model()

class OAuthTest(TestCaseUtils, TestCase):
    def setUp(self):
        self.test_user = User.objects.create_user("test@example.com", "test@example.com", "hunter2")
        self.dev_user = User.objects.create_user("dev@example.com", "dev@example.com", "hunter2")
        self.admin_user = User.objects.create_user("admin@example.com", "admin@example.com", "hunter", is_staff=True)

        self.application = Application(
            name = "Django Test",
            user= self.dev_user,
            client_type = Application.CLIENT_PUBLIC,
            authorization_grant_type = Application.GRANT_PASSWORD,
        )
        self.application.save()

        oauth2_settings._SCOPES = ['read', 'write']
        oauth2_settings._DEFAULT_SCOPES = ['read', 'write']

    def tearDown(self):
        self.application.delete()
        self.test_user.delete()
        self.dev_user.delete()

    def test_can_create_token(self):
        token = AccessToken.objects.create(
            user=self.test_user,
            token='123456789',
            application=self.application,
            expires=timezone.now() + timedelta(days=1),
            scope='read write'
        )
        self.assertTrue(token)

    def test_can_get_token_with_form_data(self):
        url = reverse("oauth2_provider:token")
        auth_headers = self.get_basic_auth_header(self.application.client_id, self.application.client_secret)

        req_data = {
                'grant_type': 'password',
                'username': 'test@example.com',
                'password': 'hunter2',
            }
        response = self.client.post(url,
            data=req_data,
            **auth_headers
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_can_get_token_with_json(self):
        url = reverse("oauth2_provider:token")
        auth_headers = self.get_basic_auth_header(self.application.client_id, self.application.client_secret)

        req_data = {
                'grant_type': 'password',
                'username': 'test@example.com',
                'password': 'hunter2',
            }
        response = self.client.post(url,
            data=req_data,
            HTTP_CONTENT_TYPE='application/json',
            **auth_headers
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_can_access_user_list_if_admin(self):
        token = AccessToken.objects.create(
            user=self.admin_user,
            token='123456789',
            application=self.application,
            expires=timezone.now() + timedelta(days=1),
            scope='read write admin',
        )
        auth = self._get_auth_header(token=token.token)
        url = reverse('user-list')
        response = self.client.get(url, HTTP_AUTHORIZATION=auth)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(json.loads(response.content.decode('utf-8'))) == 3)

    def test_cant_access_user_list_if_not_admin(self):
        token = AccessToken.objects.create(
            user=self.test_user,
            token='123456789',
            application=self.application,
            expires=timezone.now() + timedelta(days=1),
            scope='read write admin',
        )
        auth = self._get_auth_header(token=token.token)
        url = reverse('user-list')
        response = self.client.get(url, HTTP_AUTHORIZATION=auth)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cant_access_user_list_if_no_admin_scope(self):
        token = AccessToken.objects.create(
            user=self.admin_user,
            token='123456789',
            application=self.application,
            expires=timezone.now() + timedelta(days=1),
            scope='read write',
        )
        auth = self._get_auth_header(token=token.token)
        url = reverse('user-list')
        response = self.client.get(url, HTTP_AUTHORIZATION=auth)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def _get_auth_header(self, token=None):
        return "Bearer {0}".format(token or self.access_token.token)
