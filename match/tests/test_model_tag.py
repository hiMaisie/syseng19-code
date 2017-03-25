from django.test import TestCase
from match.models import Tag
from slugify import slugify
# Create your tests here.

class TagModelTests(TestCase):
    def setUp(self):
        Tag.objects.create(name="My Tag")

    def test_tag_creation(self):
        myTag = Tag.objects.get(name="My Tag")
        self.assertEqual(myTag.name, "My Tag")

    def test_tag_slug_created(self):
        tag = Tag.objects.create(name="This is some. weird ass tag")
        self.assertEqual(tag.slug, slugify("This is some. weird ass tag"))
