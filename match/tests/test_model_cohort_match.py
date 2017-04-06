from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from match.models import Cohort,MentorshipScore,Programme,Tag
from datetime import timedelta

class CohortModelMatchTets(TestCase):

    def setUp(self):
        self.user1 = User.objects.create_user(
            username="test@example.com",
            email="test@example.com",
            password="hunter2",
            last_name="Smith",
            first_name="John"
        )

        self.user2 = User.objects.create_user(
            username="test2@example.com",
            email="test2@example.com",
            password="hunter2",
            last_name="Smith",
            first_name="Jane"
        )
        
        self.user3 = User.objects.create_user(
            username="test3@example.com",
            email="test3@example.com",
            password="hunter2",
            last_name="Moss",
            first_name="Maurice"
        )

        self.programme = Programme.objects.create(
            name="Test programme",
            description="A test programme",
            createdBy=self.user1
        )

        self.cohort = self.programme.cohorts.create(
            openDate=timezone.now() - timedelta(days=7),
            createdBy=self.user1
        )

        self.tags = {
            'nodejs': Tag.objects.create(name="Node.JS"),
            'sports': Tag.objects.create(name="Sports"),
            'django': Tag.objects.create(name="Django"),
        }

    def test_match_no_scores_for_empty_cohort(self):
        self.cohort.match()
        self.assertEqual(MentorshipScore.objects.all().count(), 0)
        

    def test_match_no_scores_for_one_mentor(self):
        self.cohort.participants.create(
            user=self.user1,
            isMentor=True
        )
        self.cohort.match()
        self.assertEqual(MentorshipScore.objects.all().count(), 0)
    
    def test_match_no_scores_for_one_mentee(self):
        self.cohort.participants.create(
            user=self.user1,
            isMentor=False
        )
        self.cohort.match()
        self.assertEqual(MentorshipScore.objects.all().count(), 0)
    
    def test_match_one_score_for_one_mentee_one_mentor(self):
        self.cohort.participants.create(
            user=self.user1,
            isMentor=False,
            tags = [
                self.tags['nodejs']
            ]           
        )
        self.cohort.participants.create(
            user=self.user2,
            isMentor=True,
            tags=[
                self.tags['nodejs']
            ]
        )
        self.cohort.match()
        self.assertEqual(MentorshipScore.objects.all().count(), 1)
        ms = MentorshipScore.objects.first()

    def test_match_two_scores_for_two_mentees_one_mentor(self):
        p1 = self.cohort.participants.create(
            user=self.user1,
            isMentor=False,
            tags = [
                self.tags['nodejs'],
                self.tags['sports'],
            ]           
        )
        p2 = self.cohort.participants.create(
            user=self.user2,
            isMentor=False,
        )
        p3 = self.cohort.participants.create(
            user=self.user3,
            isMentor=True,
            tags = [
                self.tags['nodejs'],
                self.tags['sports'],
            ]           
        )
        self.cohort.match()
        self.assertEqual(MentorshipScore.objects.all().count(), 2)
        # check scores are correctly set
        ms1 = MentorshipScore.objects.filter(mentee=p1).first()
        ms2 = MentorshipScore.objects.filter(mentee=p2).first()
        self.assertTrue(ms1.score, 2)
        self.assertTrue(ms1.score, 0)

