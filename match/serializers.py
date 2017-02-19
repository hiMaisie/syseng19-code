from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, User
import json
from . import models

class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Tag
        fields = ('name',)

class UserProfileSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, required=False)
    profileImageUrl = serializers.SerializerMethodField()
    # firstName = serializers.CharField(source='user.first_name')
    # lastName = serializers.CharField(source='user.last_name')
    # email = serializers.EmailField(source='user.email')

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

    def get_profileImageUrl(self, userProfile):
        request = self.context.get('request')
        url = userProfile.profileImage.url
        if url:
            return request.build.absolute_uri(url)

class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer()

    class Meta:
        model = get_user_model()
        fields = ('email', 'first_name', 'last_name', 'profile', 'password')
        write_only_fields = ('password',)

    def create(self, validated_data):
        userprofile_data = validated_data.pop('profile', {})
        password = validated_data.pop('password', None)
        validated_data['username'] = validated_data['email']
        user = User.objects.create(**validated_data)
        if password:
            user.set_password(password)

        user.save()
        # if not (userprofile_data == {}):
        #     userprofile_data.user = user
        #     userproflie = models.UserProfile.objects.create(**userprofile_data)

        return user

class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
