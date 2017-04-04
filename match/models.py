from datetime import date,timedelta
from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.utils import timezone
from match.validators import user_validators
import os
from slugify import slugify
import uuid


# Returns path of directory where images are stored.
def _get_image_path(instance, filename):
    return os.path.join('img', str(instance.id), filename)

# Function that returns datetime two weeks after right now.
# Default value for a cohort's sign up closing date.
def _get_default_close_date():
    # return timezone.now() + timedelta.days(14)
    return timezone.now() + timedelta(days=14)

# Function that returns datetime three weeks after right now.
# Default value for a cohort's matching closing date.
def _get_default_match_date():
    return timezone.now() + timedelta(days=21)

class Tag(models.Model):
    name = models.CharField(max_length=30, primary_key=True)
    slug = models.CharField(max_length=30, default="")

    def __str__(self):
        return self.name

    def _get_slug(self):
        return slugify(self.name)
    
    def save(self, *args, **kwargs):
        self.slug = self._get_slug()
        super(Tag, self).save(*args, **kwargs)
    
    def update(self, *args, **kwargs):
        self.slug = self._get_slug()
        super(Tag, self).update(*args, **kwargs)

class UserProfile(models.Model):
    user = models.OneToOneField(User, related_name="profile")
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

    @property
    def profileImageUrl(self):
        if self.profileImage and hasattr(self.profileImage, 'url'):
            return self.image.url

class Programme(models.Model):
    programmeId = models.UUIDField(primary_key=True,default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=40)
    description = models.TextField()
    logo = models.ImageField(upload_to=_get_image_path, blank=True, null=True)
    bannerImage = models.ImageField(upload_to=_get_image_path, blank=True, null=True)
    defaultCohortSize = models.IntegerField(default=100)
    createdBy = models.ForeignKey(User, on_delete=models.CASCADE, related_name="programmes")

    def __str__(self):
        return self.name

    class Meta:
        ordering = ('name',)

    @property
    def activeCohort(self):
        qs = self.cohorts.filter(
            openDate__lte=timezone.now(),
            closeDate__gt=timezone.now()
        ).order_by('openDate')

        # select if not empty
        cohorts = [c for c in qs if c.participantCount < c.cohortSize]

        if len(cohorts):
            return cohorts[0]
        
        # If all full, pick earliest.
        cohorts = qs.all()
        if len(cohorts):
            return cohorts[0]
        return None

class Cohort(models.Model):
    cohortId = models.UUIDField(primary_key=True,default=uuid.uuid4, editable=False, unique=True)
    programme = models.ForeignKey(Programme, on_delete=models.CASCADE, related_name="cohorts")
    cohortSize = models.IntegerField(default=0)
    openDate = models.DateTimeField(default=timezone.now)
    closeDate = models.DateTimeField(default=_get_default_close_date)
    matchDate = models.DateTimeField(default=_get_default_match_date)
    createdBy = models.ForeignKey(User, on_delete=models.CASCADE, related_name="cohorts")

    def __str__(self):
        return "%s - %s" % (self.programme.name, self.openDate)

    @property
    def participantCount(self):
        return self.participants.count()

    def match(self):
        mentors = self.participants.filter(isMentor=True)
        for mentee in self.participants.filter(isMentor=False):
            for mentor in mentors:
                p = MentorshipScore.objects.create(
                        mentor=mentor,
                        mentee=mentee
                )
                p.calculateScore()

class Participant(models.Model):
    participantId = models.UUIDField(primary_key=True,default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(User, related_name="mentorships")
    cohort = models.ForeignKey(Cohort, related_name="participants")
    signUpDate = models.DateTimeField(default=timezone.now)
    isMentor = models.BooleanField(null=False)
    isMatched = models.BooleanField(default=False)
    isTopThreeSelected = models.BooleanField(default=False)
    tags = models.ManyToManyField(Tag, related_name="ParticipantTag")

    class Meta:
        unique_together  = (("user", "cohort",),)

    def getTopThree(self):
        if not (self.isMentor or self.isTopThreeSelected):
            topThree = MentorshipScore.objects.filter(mentee=self).order_by("-score")[:3]
            return list(map(lambda p: p.mentor, topThree))
        else:
            return []

class MentorshipScore(models.Model):
    mentorshipScoreId = models.UUIDField(primary_key=True,default=uuid.uuid4, editable=False, unique=True)
    mentor = models.ForeignKey(Participant, related_name="+")
    mentee = models.ForeignKey(Participant, related_name="scores")
    score = models.IntegerField(default=0)

    def calculateScore(self):
        mentee_tags = list(self.mentee.tags.all())
        mentor_tags = list(self.mentor.tags.all())
        self.score = len(set(mentee_tags).intersection(mentor_tags))
        self.save()

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
