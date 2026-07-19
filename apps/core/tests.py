import json
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

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


DESKTOP_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
MOBILE_UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
BOT_UA = "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"


class TestRedirectView(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = _UserModel.objects.create(
            email="test@example.com", password="testpass123"
        )
        self.short_url = ShortURL.objects.create(
            original_url="https://example.com", owner=self.user
        )

    def test_valid_slug_redirects(self):
        response = self.client.get(reverse("redirect", args=[self.short_url.slug]))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "https://example.com")

    def test_unknown_slug_returns_404(self):
        response = self.client.get(reverse("redirect", args=["doesnotexist"]))
        self.assertEqual(response.status_code, 404)

    def test_inactive_url_returns_410(self):
        self.short_url.is_active = False
        self.short_url.save()
        response = self.client.get(reverse("redirect", args=[self.short_url.slug]))
        self.assertEqual(response.status_code, 410)

    def test_expired_url_returns_410(self):
        self.short_url.expires_at = timezone.now() - timedelta(hours=1)
        self.short_url.save()
        response = self.client.get(reverse("redirect", args=[self.short_url.slug]))
        self.assertEqual(response.status_code, 410)

    def test_not_yet_expired_url_still_redirects(self):
        self.short_url.expires_at = timezone.now() + timedelta(hours=1)
        self.short_url.save()
        response = self.client.get(reverse("redirect", args=[self.short_url.slug]))
        self.assertEqual(response.status_code, 302)

    def test_max_clicks_reached_returns_410(self):
        self.short_url.max_clicks = 1
        self.short_url.save()
        Click.objects.create(short_url=self.short_url)
        response = self.client.get(reverse("redirect", args=[self.short_url.slug]))
        self.assertEqual(response.status_code, 410)

    def test_max_clicks_reached_deactivates_url(self):
        self.short_url.max_clicks = 1
        self.short_url.save()
        Click.objects.create(short_url=self.short_url)
        self.client.get(reverse("redirect", args=[self.short_url.slug]))
        self.short_url.refresh_from_db()
        self.assertFalse(self.short_url.is_active)

    def test_below_max_clicks_still_redirects(self):
        self.short_url.max_clicks = 5
        self.short_url.save()
        Click.objects.create(short_url=self.short_url)
        response = self.client.get(reverse("redirect", args=[self.short_url.slug]))
        self.assertEqual(response.status_code, 302)

    def test_redirect_records_click(self):
        self.client.get(reverse("redirect", args=[self.short_url.slug]))
        self.assertEqual(Click.objects.filter(short_url=self.short_url).count(), 1)

    def test_redirect_records_utm_params(self):
        self.client.get(
            reverse("redirect", args=[self.short_url.slug]),
            {
                "utm_source": "newsletter",
                "utm_medium": "email",
                "utm_campaign": "launch",
            },
        )
        click = Click.objects.get(short_url=self.short_url)
        self.assertEqual(click.utm_source, "newsletter")
        self.assertEqual(click.utm_medium, "email")
        self.assertEqual(click.utm_campaign, "launch")

    def test_redirect_records_referrer_domain(self):
        self.client.get(
            reverse("redirect", args=[self.short_url.slug]),
            HTTP_REFERER="https://twitter.com/some/path",
        )
        click = Click.objects.get(short_url=self.short_url)
        self.assertEqual(click.referrer_domain, "twitter.com")

    def test_redirect_records_desktop_device_type(self):
        self.client.get(
            reverse("redirect", args=[self.short_url.slug]),
            HTTP_USER_AGENT=DESKTOP_UA,
        )
        click = Click.objects.get(short_url=self.short_url)
        self.assertEqual(click.device_type, "desktop")

    def test_redirect_records_mobile_device_type(self):
        self.client.get(
            reverse("redirect", args=[self.short_url.slug]),
            HTTP_USER_AGENT=MOBILE_UA,
        )
        click = Click.objects.get(short_url=self.short_url)
        self.assertEqual(click.device_type, "mobile")

    def test_redirect_records_bot_device_type(self):
        self.client.get(
            reverse("redirect", args=[self.short_url.slug]),
            HTTP_USER_AGENT=BOT_UA,
        )
        click = Click.objects.get(short_url=self.short_url)
        self.assertEqual(click.device_type, "bot")


class TestAuthEndpoints(TestCase):
    def setUp(self):
        self.client = Client()
        self.password = "a-Very-Str0ng-Pass!"
        self.user = _UserModel.objects.create_user(
            username="alice", password=self.password
        )

    def _post(self, url_name, payload):
        return self.client.post(
            reverse(url_name),
            data=json.dumps(payload),
            content_type="application/json",
        )

    def test_register_creates_user(self):
        response = self._post(
            "register",
            {
                "username": "bob",
                "email": "bob@example.com",
                "password": "an0ther-Str0ng-Pass!",
            },
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(_UserModel.objects.filter(username="bob").exists())

    def test_register_hashes_password(self):
        self._post(
            "register",
            {
                "username": "carol",
                "email": "carol@example.com",
                "password": "an0ther-Str0ng-Pass!",
            },
        )
        user = _UserModel.objects.get(username="carol")
        self.assertNotEqual(user.password, "an0ther-Str0ng-Pass!")
        self.assertTrue(user.check_password("an0ther-Str0ng-Pass!"))

    def test_register_rejects_weak_password(self):
        response = self._post(
            "register",
            {"username": "dave", "email": "dave@example.com", "password": "password"},
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(_UserModel.objects.filter(username="dave").exists())

    def test_register_rejects_duplicate_username(self):
        response = self._post(
            "register",
            {
                "username": "alice",
                "email": "alice2@example.com",
                "password": "an0ther-Str0ng-Pass!",
            },
        )
        self.assertEqual(response.status_code, 400)

    def test_register_rejects_missing_email(self):
        response = self._post(
            "register", {"username": "erin", "password": "an0ther-Str0ng-Pass!"}
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(_UserModel.objects.filter(username="erin").exists())

    def test_login_returns_tokens(self):
        response = self._post(
            "login", {"username": "alice", "password": self.password}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.json())
        self.assertIn("refresh", response.json())

    def test_login_rejects_wrong_password(self):
        response = self._post("login", {"username": "alice", "password": "wrong"})
        self.assertEqual(response.status_code, 401)

    def test_access_token_authenticates_api_requests(self):
        tokens = self._post(
            "login", {"username": "alice", "password": self.password}
        ).json()
        response = self.client.get(
            reverse("shorturl-list"), HTTP_AUTHORIZATION=f"Bearer {tokens['access']}"
        )
        self.assertEqual(response.status_code, 200)

    def test_api_requests_require_authentication(self):
        response = self.client.get(reverse("shorturl-list"))
        self.assertEqual(response.status_code, 401)

    def test_refresh_returns_new_access_token(self):
        tokens = self._post(
            "login", {"username": "alice", "password": self.password}
        ).json()
        response = self._post("refresh", {"refresh": tokens["refresh"]})
        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.json())

    def test_logout_blacklists_refresh_token(self):
        tokens = self._post(
            "login", {"username": "alice", "password": self.password}
        ).json()
        response = self.client.post(
            reverse("logout"),
            data=json.dumps({"refresh": tokens["refresh"]}),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {tokens['access']}",
        )
        self.assertEqual(response.status_code, 204)

        retry = self._post("refresh", {"refresh": tokens["refresh"]})
        self.assertEqual(retry.status_code, 401)

    def test_logout_requires_authentication(self):
        response = self.client.post(
            reverse("logout"),
            data=json.dumps({"refresh": "irrelevant"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 401)
