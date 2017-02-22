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
    # profileImageUrl = serializers.SerializerMethodField()
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

class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(required=False)

    class Meta:
        model = get_user_model()
        fields = ('email', 'first_name', 'last_name', 'profile', 'password')
        extra_kwargs = {
            'password': { 'write_only': True }
        }

    def create(self, validated_data):
        userprofile_data = validated_data.pop('profile', {})
        password = validated_data.pop('password', None)
        validated_data['username'] = validated_data['email']
        user = User.objects.create(**validated_data)
        if password:
            user.set_password(password)
        user.save()
        return user

class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = '__all__'
