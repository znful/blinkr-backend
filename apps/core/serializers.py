from rest_framework import serializers
from apps.core.models import ShortURL


class ShortURLSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShortURL
        fields = [
            "id",
            "original_url",
            "slug",
            "owner",
            "expires_at",
            "is_active",
            "max_clicks",
        ]
