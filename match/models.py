from django.db import models
from django.contrib.auth.models import User
from datetime import datetime,timedelta
import os
import uuid

# Returns path of directory where images are stored.
def get_image_path(instance, filename):
    return os.path.join('img', str(instance.id), filename)

# Function that returns datetime two weeks after right now.
# Default value for a cohort's sign up closing date.
def get_default_close_date():
    return datetime.now() + timedelta.days(14)

# Function that returns datetime three weeks after right now.
# Default value for a cohort's matching closing date.
def get_default_match_date():
    return datetime.now() + timedelta.days(21)

class Tag(models.Model):
    name = models.CharField(max_length=30, primary_key=True)

    def __str__(self):
        return self.name

class UserProfile(models.Model):
    user = models.OneToOneField(User)
    joinDate = models.DateTimeField(default=datetime.now)
    position = models.CharField(max_length=30)
    department = models.CharField(max_length=30)
    dateOfBirth = models.DateTimeField()
    tags = models.ManyToManyField(Tag, related_name="UserTag")
    bio = models.TextField()
    profileImage = models.ImageField(upload_to=get_image_path, blank=True, null=True)

    def __str__(self):
        return self.user.get_full_name()

class Programme(models.Model):
    programmeId = models.UUIDField(primary_key=True,default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=40)
    description = models.TextField()
    logo = models.ImageField(upload_to=get_image_path, blank=True, null=True)
    bannerImage = models.ImageField(upload_to=get_image_path, blank=True, null=True)
    defaultCohortSize = models.IntegerField(default=100)
    createdBy = models.ForeignKey(UserProfile, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ('name',)

class Cohort(models.Model):
    cohortId = models.UUIDField(primary_key=True,default=uuid.uuid4, editable=False, unique=True)
    programme = models.ForeignKey(Programme, on_delete=models.CASCADE)
    cohortSize = models.IntegerField(default=0)
    openDate = models.DateTimeField(default=datetime.now)
    closeDate = models.DateTimeField(default=get_default_close_date)
    matchDate = models.DateTimeField(default=get_default_match_date)
    createdBy = models.ForeignKey(UserProfile, on_delete=models.CASCADE)

    def __str__(self):
        return "%s - %s" % (self.programme.name, self.openDate)

class Participant(models.Model):
    participantId = models.UUIDField(primary_key=True,default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(User)
    cohort = models.ForeignKey(Cohort)
    signUpDate = models.DateTimeField(default=datetime.now)
    isMentor = models.BooleanField(default=false)
    isMatched = models.BooleanField(default=false)

class MentorshipScore(models.Model):
    mentorshipScoreId = models.UUIDField(primary_key=True,default=uuid.uuid4, editable=False, unique=True)
    mentor = models.ForeignKey(Participant)
    mentee = models.ForeignKey(Participant)
    score = models.IntegerField(default=0)

class Mentorship(models.Model):
    mentor = models.ForeignKey(Participant)
    mentee = models.ForeignKey(Participant)

class Update(models.Model):
    updateId = models.UUIDField(primary_key=True,default=uuid.uuid4, editable=False, unique=True)

class Message(models.Model):
    messageId = models.UUIDField(primary_key=True,default=uuid.uuid4, editable=False, unique=True)
