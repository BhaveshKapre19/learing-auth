# ============================================================
# File: authentication/serializers/profile.py
# ============================================================

from rest_framework import serializers
from django.utils import timezone

from authentication.models import (
    User,
    UserProfile,
    EmailVerificationToken,
)
from authentication.services.email_service import EmailService


def build_absolute_media_url(request, file_field):
    """
    Build absolute media URL safely.
    Works even if request is missing (background jobs, tests).
    """
    if not file_field:
        return None

    url = file_field.url
    if request:
        return request.build_absolute_uri(url)

    return url




# ------------------------------------------------------------
# Serializer for logged-in user (ONE FORM, ONE UPDATE)
# ------------------------------------------------------------
class MeSerializer(serializers.Serializer):
    # ---- User fields ----
    email = serializers.EmailField(required=False)
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)
    slug = serializers.SlugField(required=False)

    # ---- Profile fields ----
    bio = serializers.CharField(required=False, allow_blank=True)
    profile_picture = serializers.ImageField(required=False)
    multi_factor_enabled = serializers.BooleanField(required=False)

    # ---------- Validation ----------
    def validate_email(self, value):
        user = self.context["request"].user
        if User.objects.filter(email=value).exclude(id=user.id).exists():
            raise serializers.ValidationError("Email already in use")
        return value

    def validate_slug(self, value):
        user = self.context["request"].user
        if User.objects.filter(slug=value).exclude(id=user.id).exists():
            raise serializers.ValidationError("Slug already in use")
        return value

    # ---------- Update ----------
    def update(self, instance, validated_data):
        """
        instance = request.user
        Updates User + UserProfile in one request
        """
        profile = instance.profile
        email_changed = False

        # ---- User updates ----
        for field in ("first_name", "last_name", "slug"):
            if field in validated_data:
                setattr(instance, field, validated_data[field])

        if "email" in validated_data and validated_data["email"] != instance.email:
            instance.email = validated_data["email"]
            instance.is_email_verified = False
            instance.is_active = False
            email_changed = True

        instance.save()

        # ---- Profile updates ----
        for field in ("bio", "profile_picture", "multi_factor_enabled"):
            if field in validated_data:
                setattr(profile, field, validated_data[field])

        profile.save()

        # ---- Re-verification if email changed ----
        if email_changed:
            token = EmailVerificationToken.objects.create(
                user=instance,
                expires_at=timezone.now() + timezone.timedelta(hours=24),
            )
            EmailService.send_verification_email(instance, token)

        return instance

    # ---------- Output ----------
    def to_representation(self, instance):
        profile = instance.profile
        request = self.context.get("request")

        return {
            "email": instance.email,
            "first_name": instance.first_name,
            "last_name": instance.last_name,
            "slug": instance.slug,
            "is_email_verified": instance.is_email_verified,

            "bio": profile.bio,
            "profile_picture": build_absolute_media_url(
                request, profile.profile_picture
            ),
            "multi_factor_enabled": profile.multi_factor_enabled,
        }


# ------------------------------------------------------------
# Public user serializer (SAFE FIELDS ONLY)
# ------------------------------------------------------------
class PublicUserSerializer(serializers.ModelSerializer):
    profile_picture = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "slug",
            "first_name",
            "last_name",
            "profile_picture",
        ]

    def get_profile_picture(self, obj):
        request = self.context.get("request")
        return build_absolute_media_url(
            request, obj.profile.profile_picture
        )


# ------------------------------------------------------------
# Admin / internal serializer (FULL ACCESS)
# ------------------------------------------------------------
class AdminUserSerializer(serializers.ModelSerializer):
    profile = serializers.StringRelatedField()
    profile_picture = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = "__all__"

    def get_profile_picture(self, obj):
        request = self.context.get("request")
        return build_absolute_media_url(
            request, obj.profile.profile_picture
        )
