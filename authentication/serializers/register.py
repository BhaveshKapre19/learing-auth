from rest_framework import serializers
from django.utils import timezone
from datetime import timedelta
from authentication.models import User, EmailVerificationToken, TempPasswordManager
from authentication.services.email_service import EmailService


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)

    def create(self, validated_data):

        user = User.objects.create_user(
            email=validated_data["email"],
            password=None,
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", ""),
            has_temp_password=True,
            is_active=False,
        )

        # temp password
        temp_obj, temp_password = TempPasswordManager.create_temp_password(user)

        # email verification token
        verification_token = EmailVerificationToken.objects.create(
            user=user,
            expires_at=timezone.now() + timedelta(hours=24),
        )

        # emails
        EmailService.send_welcome_email(user, temp_password, verification_token)

        return user
    
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("User with this email already exists.")
        return value
