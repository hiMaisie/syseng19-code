from django.test import TestCase
from match.models import Tag
from match.serializers import TagSerializer
import json

class TagSerializerTests(TestCase):

    def test_serialize_valid_tag(self):
        data = {'name': 'Test tag'}
        serializer = TagSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        serializer.save()
        tag = Tag.objects.get(name="Test tag")
        self.assertTrue(tag)

    def test_serialize_fail_tag_empty_name(self):
        data = {'name': ''}
        serializer = TagSerializer(data=data)
        self.assertFalse(serializer.is_valid())

    def test_serialize_fail_tag_no_name(self):
        data = {'tagName': 'this is a broken tag'}
        serializer = TagSerializer(data=data)
        self.assertFalse(serializer.is_valid())
