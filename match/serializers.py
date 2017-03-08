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
        fields = ('email', 'first_name', 'last_name', 'profile', 'password', 'id')
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

class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = '__all__'
