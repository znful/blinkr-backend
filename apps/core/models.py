from django.contrib.auth import get_user_model
from django.db import models
from .mixins import TimestampsMixin, SoftDeleteMixin
from apps.core.utils.slugs import generate_slug

_UserModel = get_user_model()


class ShortURL(TimestampsMixin, SoftDeleteMixin, models.Model):
    """
    Short URL Model, contains all the necessary data to handle redirection
    """

    original_url = models.URLField(max_length=200, null=False, blank=False)
    slug = models.CharField(
        max_length=24,
        unique=True,
        db_index=True,
        null=False,
        blank=True,
        default=generate_slug,
    )  # Users can leave it blank and let us generate it, or use a custom slug.
    owner = models.ForeignKey(
        to=_UserModel, related_name="shortened_urls", on_delete=models.DO_NOTHING
    )
    expires_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(null=False, default=True)
    password_hash = models.CharField(max_length=96, null=True, blank=True)
    max_clicks = models.IntegerField(
        null=True, blank=True
    )  # Users can set a limit amount of clicks before the link gets deactivated.


class Click(TimestampsMixin, models.Model):
    """
    Track link clicks for analytics
    """

    DEVICE_CHOICES = [
        ("desktop", "Desktop"),
        ("mobile", "Mobile"),
        ("tablet", "Tablet"),
        ("bot", "Bot"),
        ("unknown", "Unknown"),
    ]

    short_url = models.ForeignKey(
        to=ShortURL, related_name="clicks", on_delete=models.DO_NOTHING
    )

    country_code = models.CharField(max_length=2, blank=True)
    country_name = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)

    device_type = models.CharField(
        max_length=24, choices=DEVICE_CHOICES, default="unknown"
    )
    browser = models.CharField(max_length=64, blank=True)
    os = models.CharField(max_length=64, blank=True)

    referrer_domain = models.CharField(max_length=200, blank=True)

    utm_source = models.CharField(max_length=100, blank=True)
    utm_medium = models.CharField(max_length=100, blank=True)
    utm_campaign = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["short_url", "created_at"]),
            models.Index(fields=["created_at"]),
        ]
