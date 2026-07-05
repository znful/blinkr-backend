from django.db import IntegrityError
from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.core.models import ShortURL


_UserModel = get_user_model()

# Create your tests here.
class TestSlugGeneration(TestCase):

    def setUp(self):
        self.user = _UserModel.objects.create(email="test@example.com", password="testpass123")

    def test_slug_auto_generated_when_blank(self):
        url: ShortURL = ShortURL.objects.create(original_url="https://example.com", owner=self.user)
        self.assertTrue(url.original_url)
        self.assertGreater(len(url.slug), 0)

    def test_slug_respected_when_provided(self):
        url: ShortURL = ShortURL.objects.create(original_url="https://example.com", owner=self.user, slug="custom-slug")
        self.assertEqual(url.slug, "custom-slug")

    def test_slugs_are_unique(self):
       url1 = ShortURL.objects.create(original_url="https://example1.com", owner=self.user)
       url2 = ShortURL.objects.create(original_url="https://example2.com", owner=self.user)
       self.assertNotEqual(url1, url2)

    def test_slug_max_length(self):
        url: ShortURL = ShortURL.objects.create(original_url="https://example.com", owner=self.user, slug="custom-slug")
        self.assertLessEqual(len(url.slug), 24)

    def test_duplicate_custom_slug_raises(self):
        ShortURL.objects.create(original_url="https://example.com", owner=self.user, slug="custom-slug")
        with self.assertRaises(IntegrityError):
                ShortURL.objects.create(original_url="https://example.com", owner=self.user, slug="custom-slug")
