from datetime import timedelta
import json
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from match.models import Cohort,Programme
from match.serializers import CohortSerializer
from oauth2_provider.compat import urlencode
from oauth2_provider.models import AccessToken, Application
from oauth2_provider.settings import oauth2_settings
from oauth2_provider.tests.test_utils import TestCaseUtils
from rest_framework import status
from rest_framework.test import APITestCase

class CohortAPITests(TestCaseUtils, APITestCase):

    def setUp(self):
        self.test_user = User.objects.create_user("test@example.com", "test@example.com", "hunter23")
        self.staff_user = User.objects.create_user("staff@example.com", "staff@example.com", "hunter23", is_staff=True)

        self.application = Application(
            name = "Django Test",
            user= self.test_user,
            client_type = Application.CLIENT_PUBLIC,
            authorization_grant_type = Application.GRANT_PASSWORD,
        )
        self.application.save()

        self.programme = Programme.objects.create(
            name="Test Programme",
            description="Test programme for the API tests",
            defaultCohortSize=150,
            createdBy=self.test_user
        )

    def test_can_get_list_of_cohorts(self):
        url = reverse('programme-cohort-list', kwargs={'programmeId': self.programme.programmeId})
        cohort = Cohort.objects.create(
            programme=self.programme,
            cohortSize=200,
            createdBy=self.test_user
        )
        token = self._create_token(self.test_user, 'read')
        response = self.client.get(url, HTTP_AUTHORIZATION=self._get_auth_header(token=token.token))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_can_create_cohort_if_staff(self):
        url = reverse('programme-cohort-list', kwargs={'programmeId': self.programme.programmeId})
        data = {
            'programme': self.programme.programmeId,
            'cohortSize': 200,
            'openDate': '2017-07-13 12:00:00',
            'closeDate': '2017-07-27 12:00:00',
            'matchDate':'2017-08-03 12:00:00',
            'createdBy': self.staff_user.pk
        }
        token = self._create_token(self.staff_user, 'read write staff')
        response = self.client.post(url, data, format='json', HTTP_AUTHORIZATION=self._get_auth_header(token=token.token))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_can_create_cohort_if_staff_implicit_author(self):
        url = reverse('programme-cohort-list', kwargs={'programmeId': self.programme.programmeId})
        data = {
            'programme': self.programme.programmeId,
            'cohortSize': 200,
            'closeDate': '2017-07-27 12:00:00',
            'matchDate':'2017-08-03 12:00:00'
        }
        token = self._create_token(self.staff_user, 'read write staff')
        response = self.client.post(url, data, format='json', HTTP_AUTHORIZATION=self._get_auth_header(token=token.token))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response_data = CohortSerializer(data=json.loads(response.content.decode('utf-8')))
        c = Cohort.objects.get(cohortId=json.loads(response.content.decode('utf-8'))['cohortId'])
        self.assertEqual(c.createdBy, self.staff_user)

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
