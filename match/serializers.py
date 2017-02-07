from rest_framework import serializers
from django.contrib.auth.models import User
from . import models

class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Tag
        fields = ('name',)

class UserProfileSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True)
    profileImageUrl = serializers.SerializerMethodField()
    firstName = serializers.CharField(source='user.first_name')
    lastName = serializers.CharField(source='user.last_name')
    email = serializers.EmailField(source='user.email')
    password = serializers.CharField(source='user.password')

    class Meta:
        model = models.UserProfile
        fields = ('email',
            'password',
            'lastName',
            'firstName',
            'password',
            'joinDate',
            'position',
            'department',
            'dateOfBirth',
            'tags',
            'bio',
            'profileImageUrl',
        )

    def getProfileImageUrl(self, userProfile):
        request = self.context.get('request')
        url = userProfile.profileImage.url
        return request.build.absolute_uri(url)
