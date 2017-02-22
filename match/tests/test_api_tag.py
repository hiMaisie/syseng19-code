from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from match.models import Tag
import json

class TagAPITests(APITestCase):

    def test_add_tag(self):
        url = reverse('tag_list')
        data = {'name': 'Test tag'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Tag.objects.count(), 1)
        self.assertEqual(Tag.objects.get().name, 'Test tag')

    def test_get_tags(self):
        url = reverse('tag_list')
        Tag(name="My Tag").save()
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(json.loads(response.content.decode('utf-8')), [{'name': 'My Tag'}])
