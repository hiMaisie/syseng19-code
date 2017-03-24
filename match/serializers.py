from rest_framework import serializers,validators
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, User
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from django.utils.encoding import smart_text
import json
from . import models

# A modification of SlugRelatedField that allows the object
# to be created if it does not exist.
# http://stackoverflow.com/questions/28009829/creating-and-saving-foreign-key-objects-using-a-slugrelatedfield
class CreatableSlugRelatedField(serializers.SlugRelatedField):

    def to_internal_value(self, data):
        try:
            # .lower() so that we only *FIND* with case insensitive
            return self.get_queryset().get(**{self.slug_field: data.lower()})
        except self.get_queryset().model.DoesNotExist:
            return self.get_queryset().create(**{self.slug_field: data})
        except ObjectDoesNotExist:
            self.fail('does_not_exist', slug_name=self.slug_field, value=smart_text(data))
        except (TypeError, ValueError):
            self.fail('invalid')

class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Tag
        fields = ('name',)
        extra_kwargs = {
            'name': { 'validators': [] }
        }

class UserProfileSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, required=False)

    class Meta:
        model = models.UserProfile
        fields = ('joinDate',
            'position',
            'department',
            'dateOfBirth',
            'bio',
            'profileImageUrl',
            'tags',
        )
        read_only_fields = ('tags',)

class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(required=False)
    isStaff = serializers.ReadOnlyField(source='is_staff')

    class Meta:
        model = get_user_model()
        fields = ('email', 'first_name', 'last_name', 'isStaff', 'profile', 'password', 'id')
        extra_kwargs = {
            'password': { 'write_only': True },
            'isStaff': { 'read_only': True }
        }

    def create(self, validated_data):
        userprofile_data = validated_data.pop('profile', {})

        tags_data = []
        if 'tags' in validated_data:
            tags_data = validated_data.pop('tags')

        password = validated_data.pop('password', None)
        validated_data['username'] = validated_data['email']
        user = User.objects.create(**validated_data)
        if password:
            user.set_password(password)

        for tag in tags_data:
            try:
                obj = models.Tag.objects.get(name=tag['name'])
                user.tags.add(obj)
            except models.Tag.DoesNotExist:
                user.tags.create(**tag)

        user.save()
        return user

    def update(self, instance, validated_data):
        userprofile_data = validated_data.pop('profile', {})
        validated_data.pop('email', "")
        # instance.update(validated_data)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if userprofile_data:
            for attr, value in userprofile_data.items():
                setattr(instance.profile, attr, value)
            instance.profile.save()
        return instance

class ProgrammeSerializer(serializers.ModelSerializer):
    createdBy = UserSerializer(required=False, read_only=True)

    class Meta:
        model = models.Programme
        fields = (
            'programmeId',
            'name',
            'description',
            'logo',
            'bannerImage',
            'defaultCohortSize',
            'createdBy'
        )

class CohortSerializer(serializers.ModelSerializer):
    createdBy = UserSerializer(required=False, read_only=True)
    programme = ProgrammeSerializer(required=False, read_only=True)
    participantCount = serializers.IntegerField(source='participants.count', read_only=True)

    class Meta:
        model = models.Cohort
        fields = (
            'cohortId',
            'programme',
            'cohortSize',
            'participantCount',
            'openDate',
            'closeDate',
            'matchDate',
            'createdBy'
        )

class ParticipantSerializer(serializers.ModelSerializer):
    # tags = TagSerializer(many=True, required=False)
    tags = CreatableSlugRelatedField(many=True,
            slug_field="name", 
            queryset=models.Tag.objects.all(),
            required=False
    )
    user = UserSerializer(required=False, read_only=True)
    cohort = CohortSerializer(required=False, read_only=True)

    class Meta:
        model = models.Participant
        fields = (
            'participantId',
            'user',
            'cohort',
            'signUpDate',
            'isMentor',
            'isMatched',
            'tags'
        )
        extra_kwargs = {
            'signUpDate': { 'read_only': True },
            'isMatched': { 'read_only': True },
            'isMentor': { 'required': True }
        }

    def create(self, validated_data):
        # prevent too many signups
        if validated_data['cohort'].participants.count() >= validated_data['cohort'].cohortSize:
            raise serializers.ValidationError("This cohort is full.")

        # prevent signups before opening date and after closing date
        if timezone.now() > validated_data['cohort'].closeDate:
            raise serializers.ValidationError("This cohort has closed for registration.")
        if timezone.now() < validated_data['cohort'].openDate:
            raise serializers.ValidationError("This cohort is not yet open for registration.")

        return models.Participant.objects.create(**validated_data)

class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = '__all__'
