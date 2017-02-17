from datetime import date,timedelta
from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.utils import timezone
from match.validators import user_validators
import os
import uuid


# Returns path of directory where images are stored.
def _get_image_path(instance, filename):
    return os.path.join('img', str(instance.id), filename)

# Function that returns datetime two weeks after right now.
# Default value for a cohort's sign up closing date.
def _get_default_close_date():
    return timezone.now() + timedelta.days(14)

# Function that returns datetime three weeks after right now.
# Default value for a cohort's matching closing date.
def _get_default_match_date():
    return timezone.now() + timedelta.days(21)

class Tag(models.Model):
    name = models.CharField(max_length=30, primary_key=True)

    def __str__(self):
        return self.name

class UserProfile(models.Model):
    user = models.OneToOneField(User)
    joinDate = models.DateField(default=date.today, null=True, validators=[user_validators.validate_joinDate])
    position = models.CharField(max_length=30, blank=True, default="")
    department = models.CharField(max_length=30, blank=True, default="")
    dateOfBirth = models.DateField(blank=True, null=True, validators=[user_validators.validate_joinDate])
    tags = models.ManyToManyField(Tag, related_name="UserTag")
    bio = models.TextField(default="", blank=True)
    profileImage = models.ImageField(upload_to=_get_image_path, blank=True, null=True)
    profileSetupComplete = models.BooleanField(default=False)

    def __str__(self):
        return self.user.get_full_name()

    def getAge(self):
        if not self.dateOfBirth:
            return None
        return (date.today() - self.dateOfBirth).days // 365.25

    def getYearsWorked(self):
        if not self.joinDate:
            return None
        return (date.today() - self.joinDate).days // 365.25

class Programme(models.Model):
    programmeId = models.UUIDField(primary_key=True,default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=40)
    description = models.TextField()
    logo = models.ImageField(upload_to=_get_image_path, blank=True, null=True)
    bannerImage = models.ImageField(upload_to=_get_image_path, blank=True, null=True)
    defaultCohortSize = models.IntegerField(default=100)
    createdBy = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name="programmes")

    def __str__(self):
        return self.name

    class Meta:
        ordering = ('name',)

class Cohort(models.Model):
    cohortId = models.UUIDField(primary_key=True,default=uuid.uuid4, editable=False, unique=True)
    programme = models.ForeignKey(Programme, on_delete=models.CASCADE, related_name="cohorts")
    cohortSize = models.IntegerField(default=0)
    openDate = models.DateTimeField(default=timezone.now)
    closeDate = models.DateTimeField(default=_get_default_close_date)
    matchDate = models.DateTimeField(default=_get_default_match_date)
    createdBy = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name="cohorts")

    def __str__(self):
        return "%s - %s" % (self.programme.name, self.openDate)

class Participant(models.Model):
    participantId = models.UUIDField(primary_key=True,default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(User, related_name="mentorships")
    cohort = models.ForeignKey(Cohort, related_name="participants")
    signUpDate = models.DateTimeField(default=timezone.now)
    isMentor = models.BooleanField(default=False)
    isMatched = models.BooleanField(default=False)

class MentorshipScore(models.Model):
    mentorshipScoreId = models.UUIDField(primary_key=True,default=uuid.uuid4, editable=False, unique=True)
    mentor = models.ForeignKey(Participant, related_name="+")
    mentee = models.ForeignKey(Participant, related_name="scores")
    score = models.IntegerField(default=0)

class Mentorship(models.Model):
    mentor = models.ForeignKey(Participant, related_name="mentor_mentorships")
    mentee = models.ForeignKey(Participant, related_name="mentee_mentorships")

class Update(models.Model):
    updateId = models.UUIDField(primary_key=True,default=uuid.uuid4, editable=False, unique=True)
    mentorship = models.ForeignKey(Mentorship, related_name="updates")
    updateType = models.CharField(max_length=10)
    title = models.TextField()
    message = models.TextField(null=False)

class Message(models.Model):
    messageId = models.UUIDField(primary_key=True,default=uuid.uuid4, editable=False, unique=True)
    mentorship = models.ForeignKey(Mentorship, related_name="messages")
    sender = models.ForeignKey(Participant, related_name="messages_sent")
    recipient = models.ForeignKey(Participant, related_name="messages_received")
    dateSent = models.DateTimeField(default=timezone.now)
    received = models.BooleanField(default=False)

def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

post_save.connect(create_user_profile, sender=User)
