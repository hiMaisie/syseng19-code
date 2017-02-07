from django.test import TestCase
from match.models import Tag
# Create your tests here.

class TagTestCase(TestCase):
    def setUp(self):
        Tag.objects.create(name="My Tag")

    def test_tag_creation(self):
        myTag = Tag.objects.get(name="My Tag")
        self.assertEqual(myTag.name, "My Tag")
