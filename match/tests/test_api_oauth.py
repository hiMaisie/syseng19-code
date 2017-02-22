from datetime import datetime,timedelta
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from oauth2_provider.compat import urlencode
from oauth2_provider.models import get_application_model, AccessToken, RefreshToken
from oauth2_provider.settings import oauth2_settings
from oauth2_provider.tests.test_utils import TestCaseUtils
from rest_framework import status

# Sourced from https://github.com/evonove/django-oauth-toolkit/blob/master/oauth2_provider/tests/test_token_revocation.py

Application = get_application_model()

class OAuthTest(TestCaseUtils, TestCase):
    def setUp(self):
        self.test_user = User.objects.create_user("test", "test@example.com", "hunter2")
        self.dev_user = User.objects.create_user("dev", "dev@example.com", "hunter2")
        self.admin_user = User.objects.create_user("admin", "admin@example.com", "hunter", is_staff=True)

        self.application = Application(
            name = "Django Test",
            redirect_uris = "http://localhost http://example.com",
            user= self.dev_user,
            client_type = Application.CLIENT_CONFIDENTIAL,
            authorization_grant_type = Application.GRANT_AUTHORIZATION_CODE,
        )
        self.application.save()

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

    #def test_can_access_user_list_if_admin(self):
    #    token = AccessToken.objects.create(
    #        user=self.admin_user,
    #        token='123456789',
    #        application=self.application,
    #        expires=timezone.now() + timedelta(days=1),
    #        scope='read write',
    #    )
    #    auth = self._get_auth_header(token=token.token)
    #    url = reverse('user-list')
    #    response = self.client.get(url, HTTP_AUTHORIZATION=auth)
    #    print(response.content.decode('utf-8'))
    #    self.assertEqual(response.status_code, status.HTTP_200_OK)
    #    self.assertTrue(len(json.loads(response.content.decode('utf-8'))) == 3)

    def _get_auth_header(self, token=None):
        return "Bearer: {0}".format(token or self.access_token.token)
