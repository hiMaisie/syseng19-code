from datetime import timedelta
import json
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from match.models import Cohort,MentorshipScore,Participant,Programme,Tag
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
        self.fourth_user = User.objects.create_user("test3@example.com", "test3@example.com", "hunter23")

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

        self.tags = {
            'nodejs': Tag.objects.create(name="One True Dev Language"),
            'sports': Tag.objects.create(name="Sport Stuff"),
            'django': Tag.objects.create(name="Django Rest Framework"),
        }

    def test_cant_get_participant_endpoint_without_registering(self):
        url = reverse('cohort-register', kwargs={'cohortId': self.cohort.cohortId})
        token = self._create_token(self.test_user, 'read write')
        response = self.client.get(url, HTTP_AUTHORIZATION=self._get_auth_header(token.token))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_can_get_participant_endpoint_after_registration(self):
        self.cohort.participants.create(
            isMentor=True,
            user=self.test_user
        )
        url = reverse('cohort-register', kwargs={'cohortId': self.cohort.cohortId})
        token = self._create_token(self.test_user, 'read write')
        response = self.client.get(url, HTTP_AUTHORIZATION=self._get_auth_header(token.token))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_can_get_list_of_users_participants(self):
        p = self.cohort.participants.create(
            isMentor=True,
            user=self.test_user
        )
        self.cohort.participants.create(
            isMentor=False,
            user=self.other_user
        )
        url = reverse('participant-list')
        token = self._create_token(self.test_user, 'read')
        response = self.client.get(url, HTTP_AUTHORIZATION=self._get_auth_header(token.token))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        res_data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(len(res_data), 1)
        self.assertEqual(res_data[0]['participantId'], str(p.participantId))

    def test_get_empty_list_of_participants_if_no_participants(self):
        self.cohort.participants.create(
            isMentor=False,
            user=self.other_user
        )
        url = reverse('participant-list')
        token = self._create_token(self.test_user, 'read')
        response = self.client.get(url, HTTP_AUTHORIZATION=self._get_auth_header(token.token))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        res_data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(len(res_data), 0)

    def test_can_get_participant_detail(self):
        p = self.cohort.participants.create(
            isMentor=True,
            user=self.test_user
        )
        url = reverse('participant-detail', kwargs={'participantId': p.participantId})
        token = self._create_token(self.test_user, 'read')
        response = self.client.get(url, HTTP_AUTHORIZATION=self._get_auth_header(token.token))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        res_data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(res_data['participantId'], str(p.participantId))

    def test_can_get_top_three_if_cohort_closed(self):
        cohort = self.programme.cohorts.create(
            openDate=timezone.now() - timedelta(days=8),
            closeDate=timezone.now() - timedelta(days=1),
            matchDate=timezone.now() + timedelta(days=3),
            createdBy=self.test_user
        )
        p = cohort.participants.create(
            isMentor=False,
            user=self.test_user,
            tags=[
                self.tags['django'],
                self.tags['nodejs'],
                self.tags['sports'],
            ]
        )
        mentor1 = cohort.participants.create(
            isMentor=True,
            user=self.other_user,
            tags=[
                self.tags['django'],
            ]
        )
        mentor2 = cohort.participants.create(
            isMentor=True,
            user=self.staff_user,
            tags=[
                self.tags['nodejs'],
                self.tags['sports'],
            ]
        )
        mentor3 = cohort.participants.create(
            isMentor=True,
            user=self.fourth_user,
            tags=[
                self.tags['django'],
                self.tags['nodejs'],
                self.tags['sports'],
            ]
        )
        cohort.match()
        url = reverse('participant-top-three', kwargs={'participantId': p.participantId})
        token = self._create_token(self.test_user, 'read')
        response = self.client.get(url, HTTP_AUTHORIZATION=self._get_auth_header(token.token))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        res_data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(len(res_data), 3)
        self.assertEqual(res_data[0]['participantId'], str(mentor3.participantId))
        self.assertEqual(res_data[1]['participantId'], str(mentor2.participantId))
        self.assertEqual(res_data[2]['participantId'], str(mentor1.participantId))

    def test_cant_get_top_three_if_cohort_not_closed(self):
        cohort = self.programme.cohorts.create(
            openDate=timezone.now() - timedelta(days=3),
            closeDate=timezone.now() + timedelta(days=3),
            matchDate=timezone.now() + timedelta(days=10),
            createdBy=self.test_user
        )
        p = cohort.participants.create(
            isMentor=False,
            user=self.test_user,
            tags=[
                self.tags['django'],
                self.tags['nodejs'],
                self.tags['sports'],
            ]
        )
        mentor1 = cohort.participants.create(
            isMentor=True,
            user=self.other_user,
            tags=[
                self.tags['django'],
            ]
        )
        url = reverse('participant-top-three', kwargs={'participantId': p.participantId})
        token = self._create_token(self.test_user, 'read')
        response = self.client.get(url, HTTP_AUTHORIZATION=self._get_auth_header(token.token))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_cant_get_top_three_if_matching_finished(self):
        objs = self._create_nominal_cohort_and_participants()
        objs['cohort'].matchDate= timezone.now() - timedelta(minutes=10)
        objs['cohort'].save()
        objs['cohort'].match()
        url = reverse('participant-top-three', kwargs={'participantId': objs['mentee'].participantId})
        token = self._create_token(self.test_user, 'read')
        response = self.client.get(url, HTTP_AUTHORIZATION=self._get_auth_header(token.token))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_can_get_top_three_even_if_not_top_three(self):
        cohort = self.programme.cohorts.create(
            openDate=timezone.now() - timedelta(days=8),
            closeDate=timezone.now() - timedelta(days=1),
            matchDate=timezone.now() + timedelta(days=6),
            createdBy=self.test_user
        )
        p = cohort.participants.create(
            isMentor=False,
            user=self.test_user,
            tags=[
                self.tags['django'],
                self.tags['nodejs'],
                self.tags['sports'],
            ]
        )
        mentor1 = cohort.participants.create(
            isMentor=True,
            user=self.other_user,
            tags=[
                self.tags['django'],
            ]
        )
        mentor2 = cohort.participants.create(
            isMentor=True,
            user=self.staff_user,
            tags=[
                self.tags['nodejs'],
                self.tags['sports'],
            ]
        )
        cohort.match()
        url = reverse('participant-top-three', kwargs={'participantId': p.participantId})
        token = self._create_token(self.test_user, 'read')
        response = self.client.get(url, HTTP_AUTHORIZATION=self._get_auth_header(token.token))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        res_data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(len(res_data), 2)

    def test_cant_get_top_three_if_mentor(self):
        objs = self._create_nominal_cohort_and_participants()
        url = reverse('participant-top-three', kwargs={'participantId': objs['mentors'][0].participantId})
        token = self._create_token(self.other_user, 'read')
        response = self.client.get(url, HTTP_AUTHORIZATION=self._get_auth_header(token.token))
        self._destroy_nominal_cohort_and_participants(objs)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_can_choose_top_three_if_mentee(self):
        objs = self._create_nominal_cohort_and_participants()
        url = reverse('participant-top-three', kwargs={'participantId': objs['mentee'].participantId})
        token = self._create_token(self.test_user, 'write')
        scores = [
            MentorshipScore.objects.get(mentee=objs['mentee'], mentor=objs['mentors'][2]),
            MentorshipScore.objects.get(mentee=objs['mentee'], mentor=objs['mentors'][1]),
            MentorshipScore.objects.get(mentee=objs['mentee'], mentor=objs['mentors'][0])
        ]
        data = {
            'choices': [
                objs['mentors'][2].participantId,
                objs['mentors'][1].participantId,
                objs['mentors'][0].participantId,
            ]
        }
        response = self.client.post(url, data, HTTP_AUTHORIZATION=self._get_auth_header(token.token))
        self._destroy_nominal_cohort_and_participants(objs)
        if not response.status_code == status.HTTP_200_OK:
            self.fail(response.content)
        new_scores = [
            MentorshipScore.objects.get(mentee=objs['mentee'], mentor=objs['mentors'][2]),
            MentorshipScore.objects.get(mentee=objs['mentee'], mentor=objs['mentors'][1]),
            MentorshipScore.objects.get(mentee=objs['mentee'], mentor=objs['mentors'][0])
        ]
        self.assertEqual(new_scores[0].score, scores[0].score + 10)
        self.assertEqual(new_scores[1].score, scores[1].score + 5)
        self.assertEqual(new_scores[2].score, scores[2].score)
    
    def test_cant_choose_top_three_if_mentor(self):
        objs = self._create_nominal_cohort_and_participants()
        url = reverse('participant-top-three', kwargs={'participantId': objs['mentors'][0].participantId})
        token = self._create_token(self.other_user, 'write')
        data = {
            'choices': [
                objs['mentee'].participantId
            ]
        }
        response = self.client.post(url, data, HTTP_AUTHORIZATION=self._get_auth_header(token.token))
        self._destroy_nominal_cohort_and_participants(objs)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_cant_choose_top_three_twice(self):
        objs = self._create_nominal_cohort_and_participants()
        url = reverse('participant-top-three', kwargs={'participantId': objs['mentee'].participantId})
        token = self._create_token(self.test_user, 'write')
        data = {
            'choices': [
                objs['mentors'][2].participantId,
                objs['mentors'][1].participantId,
                objs['mentors'][0].participantId,
            ]
        }
        response = self.client.post(url, data, HTTP_AUTHORIZATION=self._get_auth_header(token.token))
        if not response.status_code == status.HTTP_200_OK:
            self.fail(response.content)
        response = self.client.post(url, data, HTTP_AUTHORIZATION=self._get_auth_header(token.token))
        self._destroy_nominal_cohort_and_participants(objs)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cant_choose_same_mentor_in_top_three_twice(self):
        objs = self._create_nominal_cohort_and_participants()
        url = reverse('participant-top-three', kwargs={'participantId': objs['mentee'].participantId})
        token = self._create_token(self.test_user, 'write')
        data = {
            'choices': [
                objs['mentors'][2].participantId,
                objs['mentors'][2].participantId,
                objs['mentors'][0].participantId,
            ]
        }
        response = self.client.post(url, data, HTTP_AUTHORIZATION=self._get_auth_header(token.token))
        self._destroy_nominal_cohort_and_participants(objs)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cant_choose_top_three_before_closeDate(self):
        objs = self._create_nominal_cohort_and_participants()
        objs['cohort'].openDate = timezone.now() - timedelta(days=1)
        objs['cohort'].closeDate = timezone.now() + timedelta(days=1)
        objs['cohort'].matchDate = timezone.now() + timedelta(days=3)
        objs['cohort'].save()
        url = reverse('participant-top-three', kwargs={'participantId': objs['mentee'].participantId})
        token = self._create_token(self.test_user, 'write')
        data = {
            'choices': [
                objs['mentors'][2].participantId,
                objs['mentors'][1].participantId,
                objs['mentors'][0].participantId,
            ]
        }
        response = self.client.post(url, data, HTTP_AUTHORIZATION=self._get_auth_header(token.token))
        self._destroy_nominal_cohort_and_participants(objs)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    #TODO: Add test for can't choose top three after matchDate
    #TODO: Add test for can't choose top three if auth user isn't participant
    #TODO: Add test for pass when <3 choices given.

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

    def _create_nominal_cohort_and_participants(self):
        cohort = self.programme.cohorts.create(
            openDate=timezone.now() - timedelta(days=8),
            closeDate=timezone.now() - timedelta(days=1),
            matchDate=timezone.now() + timedelta(days=3),
            createdBy=self.test_user
        )
                
        p = cohort.participants.create(
            isMentor=False,
            user=self.test_user,
            tags=[
                self.tags['django'],
                self.tags['nodejs'],
                self.tags['sports'],
            ]
        )
        mentor1 = cohort.participants.create(
            isMentor=True,
            user=self.other_user,
            tags=[
                self.tags['django'],
            ]
        )
        mentor2 = cohort.participants.create(
            isMentor=True,
            user=self.staff_user,
            tags=[
                self.tags['nodejs'],
                self.tags['sports'],
            ]
        )
        mentor3 = cohort.participants.create(
            isMentor=True,
            user=self.fourth_user,
            tags=[
                self.tags['django'],
                self.tags['nodejs'],
                self.tags['sports'],
            ]
        )
        cohort.match()
        return {
            'cohort': cohort,
            'mentee': p,
            'mentors': [
                mentor1,
                mentor2,
                mentor3,
            ]
        }
    
    def _destroy_nominal_cohort_and_participants(self, objs):
        pass
        #for mentor in objs['mentors']:
        #    mentor.destroy()
        #objs['mentee'].destroy()
        #objs['cohort'].destroy()
