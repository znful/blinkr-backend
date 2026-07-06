from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase

from apps.core.models import Click, ShortURL

_UserModel = get_user_model()


class TestSlugGeneration(TestCase):
    def setUp(self):
        self.user = _UserModel.objects.create(
            email="test@example.com", password="testpass123"
        )

    def test_slug_auto_generated_when_blank(self):
        url: ShortURL = ShortURL.objects.create(
            original_url="https://example.com", owner=self.user
        )
        self.assertTrue(url.original_url)
        self.assertGreater(len(url.slug), 0)

    def test_slug_respected_when_provided(self):
        url: ShortURL = ShortURL.objects.create(
            original_url="https://example.com", owner=self.user, slug="custom-slug"
        )
        self.assertEqual(url.slug, "custom-slug")

    def test_slugs_are_unique(self):
        url1 = ShortURL.objects.create(
            original_url="https://example1.com", owner=self.user
        )
        url2 = ShortURL.objects.create(
            original_url="https://example2.com", owner=self.user
        )
        self.assertNotEqual(url1, url2)

    def test_slug_max_length(self):
        url: ShortURL = ShortURL.objects.create(
            original_url="https://example.com", owner=self.user, slug="custom-slug"
        )
        self.assertLessEqual(len(url.slug), 24)

    def test_duplicate_custom_slug_raises(self):
        ShortURL.objects.create(
            original_url="https://example.com", owner=self.user, slug="custom-slug"
        )
        with self.assertRaises(IntegrityError):
            ShortURL.objects.create(
                original_url="https://example.com", owner=self.user, slug="custom-slug"
            )


class TestDefaults(TestCase):
    def setUp(self):
        self.user = _UserModel.objects.create(
            email="test@example.com", password="testpass123"
        )
        self.short_url = ShortURL.objects.create(
            original_url="https://example.com", owner=self.user
        )

    def test_short_url_is_active_defaults_to_true(self):
        self.assertTrue(self.short_url.is_active)

    def test_expires_at_defaults_to_none(self):
        self.assertIsNone(self.short_url.expires_at)

    def test_max_clicks_defaults_to_none(self):
        self.assertIsNone(self.short_url.max_clicks)

    def test_password_hash_defaults_to_none(self):
        self.assertIsNone(self.short_url.password_hash)


class TestSoftDelete(TestCase):
    def setUp(self):
        self.user = _UserModel.objects.create(
            email="test@example.com", password="testpass123"
        )
        self.url = ShortURL.objects.create(
            original_url="https://example.com", owner=self.user
        )

    def test_soft_delete_sets_deleted_at(self):
        self.url.delete()
        refreshed = ShortURL.all_objects.get(pk=self.url.pk)
        self.assertIsNotNone(refreshed.deleted_at)

    def test_soft_deleted_excluded_from_default_manager(self):
        self.url.delete()
        self.assertFalse(ShortURL.objects.filter(pk=self.url.pk).exists())

    def test_soft_deleted_visible_in_all_objects(self):
        self.url.delete()
        self.assertTrue(ShortURL.all_objects.filter(pk=self.url.pk).exists())

    def test_hard_delete_removes_record(self):
        pk = self.url.pk
        self.url.hard_delete()
        self.assertFalse(ShortURL.all_objects.filter(pk=pk).exists())

    def test_all_objects_alive_excludes_deleted(self):
        self.url.delete()
        self.assertFalse(ShortURL.all_objects.alive().filter(pk=self.url.pk).exists())

    def test_all_objects_dead_returns_deleted(self):
        self.url.delete()
        self.assertTrue(ShortURL.all_objects.dead().filter(pk=self.url.pk).exists())

    def test_bulk_soft_delete_does_not_hard_delete(self):
        ShortURL.objects.filter(pk=self.url.pk).delete()
        self.assertFalse(ShortURL.objects.filter(pk=self.url.pk).exists())
        self.assertTrue(ShortURL.all_objects.dead().filter(pk=self.url.pk).exists())

    def test_soft_delete_returns_count_and_label(self):
        count, detail = self.url.delete()
        self.assertEqual(count, 1)
        self.assertIn("core.ShortURL", detail)


class TestTimestamps(TestCase):
    def setUp(self):
        self.user = _UserModel.objects.create(
            email="test@example.com", password="testpass123"
        )

    def test_created_at_set_on_creation(self):
        url = ShortURL.objects.create(
            original_url="https://example.com", owner=self.user
        )
        self.assertIsNotNone(url.created_at)

    def test_updated_at_set_on_creation(self):
        url = ShortURL.objects.create(
            original_url="https://example.com", owner=self.user
        )
        self.assertIsNotNone(url.updated_at)


class TestClickModel(TestCase):
    def setUp(self):
        self.user = _UserModel.objects.create(
            email="test@example.com", password="testpass123"
        )
        self.short_url = ShortURL.objects.create(
            original_url="https://example.com", owner=self.user
        )

    def test_click_can_be_created(self):
        click = Click.objects.create(short_url=self.short_url)
        self.assertIsNotNone(click.pk)

    def test_click_optional_fields_default_to_empty_string(self):
        click = Click.objects.create(short_url=self.short_url)
        self.assertEqual(click.country_code, "")
        self.assertEqual(click.country_name, "")
        self.assertEqual(click.city, "")
        self.assertEqual(click.browser, "")
        self.assertEqual(click.os, "")
        self.assertEqual(click.referrer_domain, "")
        self.assertEqual(click.utm_source, "")
        self.assertEqual(click.utm_medium, "")
        self.assertEqual(click.utm_campaign, "")

    def test_click_device_type_defaults_to_unknown(self):
        click = Click.objects.create(short_url=self.short_url)
        self.assertEqual(click.device_type, "unknown")

    def test_click_ordered_newest_first(self):
        click1 = Click.objects.create(short_url=self.short_url)
        click2 = Click.objects.create(short_url=self.short_url)
        clicks = list(Click.objects.all())
        self.assertEqual(clicks[0].pk, click2.pk)
        self.assertEqual(clicks[1].pk, click1.pk)
