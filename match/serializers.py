from rest_framework import serializers
from django.contrib.auth.models import User
from . import models

class TagSerializer(serializers.Serializer):
    name = serializers.CharField(read_only=True)

    class Meta:
        model = models.Tag

class UserProfileSerializer(serializers.Serializer):
    first_name = serializers.CharField(source='user.first_name')
    last_name = serializers.CharField(source='user.last_name')
    email = serializers.CharField(source='user.email')
    password = serializers.CharField(source='user.password')

    joinDate = serializers.DateTimeField(read_only=True)
    position = serializers.CharField()
    department = serializers.CharField()
    dateOfBirth = serializers.DateTimeField(read_only=True)
    tags = TagSerializer(many=True)
    bio = serializers.CharField()
    profileImageUrl = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'password', 'last_name', 'first_name', 'password')

    def getProfileImageUrl(self, userProfile):
        request = self.context.get('request')
        url = userProfile.profileImage.url
        return request.build.absolute_uri(url)
