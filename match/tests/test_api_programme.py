from datetime import timedelta
import json
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from match.models import Programme
from match.serializers import ProgrammeSerializer
from oauth2_provider.compat import urlencode
from oauth2_provider.models import AccessToken, Application
from oauth2_provider.settings import oauth2_settings
from oauth2_provider.tests.test_utils import TestCaseUtils
from rest_framework import status
from rest_framework.test import APITestCase

class ProgrammeAPITests(TestCaseUtils, APITestCase):

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

    def test_create_programme_if_staff(self):
        url = reverse('programme-list')
        data = {
            'name': 'Test Programme',
            'description': 'This is a test programme.',
            'defaultCohortSize': 100,
            'createdBy': self.staff_user.pk
        }
        token = self._create_token(self.staff_user, 'write staff')
        response = self.client.post(url, data, format='json', HTTP_AUTHORIZATION=self._get_auth_header(token=token.token))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_can_create_programme_with_implicit_author(self):
        url = reverse('programme-list')
        data = {
            'name': 'Test Programme',
            'description': 'This is a test programme',
            'defaultCohortSize': 100
        }
        token = self._create_token(self.staff_user, 'write staff')
        response = self.client.post(url, data, format='json', HTTP_AUTHORIZATION=self._get_auth_header(token=token.token))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response_data = ProgrammeSerializer(data=json.loads(response.content.decode('utf-8')))
        if not response_data.is_valid():
            self.fail()
        p = Programme.objects.get(programmeId=json.loads(response.content.decode('utf-8'))['programmeId'])
        self.assertEqual(p.createdBy, self.staff_user)

    def test_cant_create_programme_if_not_staff(self):
        url = reverse('programme-list')
        data = {
            'name': 'Test Programme',
            'description': 'This is a test programme.',
            'defaultCohortSize': 100,
            'createdBy': self.test_user.pk
        }
        token = self._create_token(self.test_user, 'write staff')
        response = self.client.post(url, data, format='json', HTTP_AUTHORIZATION=self._get_auth_header(token=token.token))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cant_create_programme_if_not_staff_with_implicit_author(self):
        url = reverse('programme-list')
        data = {
            'name': 'Test Programme',
            'description': 'This is a test programme.',
            'defaultCohortSize': 100
        }
        token = self._create_token(self.test_user, 'write staff')
        response = self.client.post(url, data, format='json', HTTP_AUTHORIZATION=self._get_auth_header(token=token.token))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cant_create_programme_if_no_staff_scope(self):
        url = reverse('programme-list')
        data = {
            'name': 'Test Programme',
            'description': 'This is a test programme.',
            'defaultCohortSize': 100,
            'createdBy': self.staff_user.pk
        }
        token = self._create_token(self.staff_user, 'write')
        response = self.client.post(url, data, format='json', HTTP_AUTHORIZATION=self._get_auth_header(token=token.token))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_can_read_programme_list(self):
        url = reverse('programme-list')
        token = self._create_token(self.test_user, 'read')
        response = self.client.get(url, HTTP_AUTHORIZATION=self._get_auth_header(token=token.token))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_cant_read_programme_list_if_no_auth(self):
        url = reverse('programme-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cant_read_programme_list_if_no_read_scope(self):
        url = reverse('programme-list')
        token = self._create_token(self.test_user, 'write')
        response = self.client.get(url, HTTP_AUTHORIZATION=self._get_auth_header(token=token.token))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_can_read_specific_programme(self):
        programme = Programme.objects.create(
            name = 'Test Programme',
            description = 'This is a test programme.',
            defaultCohortSize = 100,
            createdBy = self.staff_user
        )
        serializer = ProgrammeSerializer(programme)
        url = reverse('programme-detail', kwargs={'programmeId': programme.programmeId})
        token = self._create_token(self.test_user, 'read')
        response = self.client.get(url, HTTP_AUTHORIZATION=self._get_auth_header(token=token.token))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(json.loads(response.content.decode('utf-8')), serializer.data)

    def test_can_patch_specific_programme_if_owner(self):
        programme = Programme.objects.create(
            name = 'Test Programme',
            description = 'This is a test programme.',
            defaultCohortSize = 100,
            createdBy = self.staff_user
        )
        url = reverse('programme-detail', kwargs={'programmeId': programme.programmeId})
        patch_data = { 'name': 'Renamed Test Programme' }
        token = self._create_token(self.staff_user, 'write staff')
        response = self.client.patch(url, data=patch_data, format='json', HTTP_AUTHORIZATION=self._get_auth_header(token=token.token))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        programme = Programme.objects.get(programmeId=programme.programmeId)
        self.assertEqual(programme.name, 'Renamed Test Programme')

    def test_cant_patch_programme_id(self):
        programme = Programme.objects.create(
            name = 'Test Programme',
            description = 'This is a test programme.',
            defaultCohortSize = 100,
            createdBy = self.staff_user
        )
        old_id = programme.programmeId
        url = reverse('programme-detail', kwargs={'programmeId': programme.programmeId})
        patch_data = { 'programmeId': '12345678-90ab-cdef-1234-567890abcdef' }
        token = self._create_token(self.staff_user, 'write staff')
        response = self.client.patch(url, data=patch_data, format='json', HTTP_AUTHORIZATION=self._get_auth_header(token=token.token))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # ensure doesn't change
        self.assertEqual(json.loads(response.content.decode('utf-8'))['programmeId'], str(old_id))

    def test_cant_patch_specific_programme_if_no_staff_scope(self):
        programme = Programme.objects.create(
            name = 'Test Programme',
            description = 'This is a test programme.',
            defaultCohortSize = 100,
            createdBy = self.staff_user
        )
        url = reverse('programme-detail', kwargs={'programmeId': programme.programmeId})
        patch_data = { 'name': 'Renamed Test Programme' }
        token = self._create_token(self.staff_user, 'write')
        response = self.client.patch(url, data=patch_data, format='json', HTTP_AUTHORIZATION=self._get_auth_header(token=token.token))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cant_patch_specific_programme_if_not_owner(self):
        programme = Programme.objects.create(
            name = 'Test Programme',
            description = 'This is a test programme.',
            defaultCohortSize = 100,
            createdBy = self.test_user
        )
        url = reverse('programme-detail', kwargs={'programmeId': programme.programmeId})
        patch_data = { 'name': 'Renamed Test Programme' }
        token = self._create_token(self.staff_user, 'write')
        response = self.client.patch(url, data=patch_data, format='json', HTTP_AUTHORIZATION=self._get_auth_header(token=token.token))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_can_delete_specific_programme_if_owner(self):
        programme = Programme.objects.create(
            name = 'Test Programme',
            description = 'This is a test programme.',
            defaultCohortSize = 100,
            createdBy = self.staff_user
        )
        url = reverse('programme-detail', kwargs={'programmeId': programme.programmeId})
        token = self._create_token(self.staff_user, 'write admin')
        response = self.client.delete(url, HTTP_AUTHORIZATION=self._get_auth_header(token=token.token))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        with self.assertRaises(Programme.DoesNotExist):
            programme = Programme.objects.get(programmeId=programme.programmeId)

    def test_cant_delete_specific_programme_if_no_staff_scope(self):
        programme = Programme.objects.create(
            name = 'Test Programme',
            description = 'This is a test programme.',
            defaultCohortSize = 100,
            createdBy = self.staff_user
        )
        url = reverse('programme-detail', kwargs={'programmeId': programme.programmeId})
        token = self._create_token(self.staff_user, 'read')
        response = self.client.delete(url, HTTP_AUTHORIZATION=self._get_auth_header(token=token.token))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cant_delete_specific_programme_if_no_read_scope(self):
        programme = Programme.objects.create(
            name = 'Test Programme',
            description = 'This is a test programme.',
            defaultCohortSize = 100,
            createdBy = self.staff_user
        )
        url = reverse('programme-detail', kwargs={'programmeId': programme.programmeId})
        token = self._create_token(self.staff_user, 'staff')
        response = self.client.delete(url, HTTP_AUTHORIZATION=self._get_auth_header(token=token.token))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cant_delete_specific_programme_if_not_owner(self):
        programme = Programme.objects.create(
            name = 'Test Programme',
            description = 'This is a test programme.',
            defaultCohortSize = 100,
            createdBy = self.test_user
        )
        url = reverse('programme-detail', kwargs={'programmeId': programme.programmeId})
        token = self._create_token(self.staff_user, 'write staff')
        response = self.client.delete(url, HTTP_AUTHORIZATION=self._get_auth_header(token=token.token))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_can_patch_programme_if_admin(self):
        programme = Programme.objects.create(
            name = 'Test Programme',
            description = 'This is a test programme.',
            defaultCohortSize = 100,
            createdBy = self.staff_user
        )
        patch_data = {
            'name':'Renamed Programme',
            'description': 'This is some random description'
        }
        url = reverse('programme-detail', kwargs={'programmeId': programme.programmeId})
        token = self._create_token(self.staff_user, 'write staff')
        response = self.client.patch(url, patch_data, HTTP_AUTHORIZATION=self._get_auth_header(token=token.token))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # refresh programme var
        programme = Programme.objects.get(programmeId=programme.programmeId)
        self.assertEqual(programme.name, patch_data['name'])
        self.assertEqual(programme.description, patch_data['description'])

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
