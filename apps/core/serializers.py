from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from apps.core.models import ShortURL

_UserModel = get_user_model()


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


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])

    class Meta:
        model = _UserModel
        fields = ["id", "username", "email", "password"]
        extra_kwargs = {"email": {"required": True, "allow_blank": False}}

    def create(self, validated_data):
        return _UserModel.objects.create_user(**validated_data)
