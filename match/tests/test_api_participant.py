from datetime import timedelta
import json
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from match.models import Cohort,Participant,Programme
from match.serializers import ParticipantSerializer
from oauth2_provider.compat import urlencode
from oauth2_provider.models import AccessToken, Application
from oauth2_provider.settings import oauth2_settings
from oauth2_provider.tests.test_utils import TestCaseUtils
from rest_framework import status
from rest_framework.test import APITestCase
from datetime import timedelta

class ParticipantAPITests(TestCaseUtils, APITestCase):

    def setUp(self):
        self.test_user = User.objects.create_user("test@example.com", "test@example.com", "hunter23")
        self.other_user = User.objects.create_user("test2@example.com", "test2@example.com", "hunter23")
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
        self.cohort = self.programme.cohorts.create(
            cohortSize=2,
            createdBy=self.staff_user
        )

    def test_can_register_for_cohort(self):
        url = reverse('cohort-register', kwargs={'cohortId': self.cohort.cohortId})
        data = {
            'isMentor': True
        }
        token = self._create_token(self.test_user, 'read write')
        response = self.client.post(url, data=data, format='json', HTTP_AUTHORIZATION=self._get_auth_header(token=token.token))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_cant_register_for_cohort_without_scope(self):
        url = reverse('cohort-register', kwargs={'cohortId': self.cohort.cohortId})
        data = {
            'isMentor': True
        }
        token = self._create_token(self.test_user, '')
        response = self.client.post(url, data=data, format='json', HTTP_AUTHORIZATION=self._get_auth_header(token=token.token))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cant_register_for_cohort_twice(self):
        self.cohort.participants.create(
            user=self.test_user,
            isMentor=True
        )
        url = reverse('cohort-register', kwargs={'cohortId': self.cohort.cohortId})
        data = {
            'isMentor': True
        }
        token = self._create_token(self.test_user, 'read write')
        response = self.client.post(url, data=data, format='json', HTTP_AUTHORIZATION=self._get_auth_header(token=token.token))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cant_register_for_full_cohort(self):
        Participant.objects.create(
            user=self.test_user,
            cohort=self.cohort,
            isMentor=True
        )
        Participant.objects.create(
            user=self.staff_user,
            cohort=self.cohort,
            isMentor=True
        )
        url = reverse('cohort-register', kwargs={'cohortId': self.cohort.cohortId})
        data = {
            'isMentor': True
        }
        token = self._create_token(self.other_user, 'read write')
        response = self.client.post(url, data=data, format='json', HTTP_AUTHORIZATION=self._get_auth_header(token=token.token))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cant_register_for_cohort_before_opendate(self):
        earlycohort = self.programme.cohorts.create(
            cohortSize=2,
            createdBy=self.staff_user,
            openDate=timezone.now() + timedelta(days=2)
        )
        url = reverse('cohort-register', kwargs={'cohortId': earlycohort.cohortId})
        data = {
            'isMentor': True
        }
        token = self._create_token(self.other_user, 'read write')
        response = self.client.post(url, data=data, format='json', HTTP_AUTHORIZATION=self._get_auth_header(token=token.token))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cant_register_for_cohort_after_closedate(self):
        latecohort = self.programme.cohorts.create(
            cohortSize=2,
            createdBy=self.staff_user,
            openDate=timezone.now() - timedelta(days=7),
            closeDate=timezone.now() - timedelta(days=2)
        )
        url = reverse('cohort-register', kwargs={'cohortId': latecohort.cohortId})
        data = {
            'isMentor': True
        }
        token = self._create_token(self.other_user, 'read write')
        response = self.client.post(url, data=data, format='json', HTTP_AUTHORIZATION=self._get_auth_header(token=token.token))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

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
