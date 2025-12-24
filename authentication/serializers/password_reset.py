#serializers/password_reset.py

from rest_framework import serializers
from django.utils import timezone
from authentication.models import User, PasswordResetToken
from authentication.email_service import EmailService


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate(self, attrs):
        user = User.objects.filter(email=attrs["email"]).first()
        if user:
            token = PasswordResetToken.objects.create(
                user=user,
                expires_at=timezone.now() + timezone.timedelta(hours=1),
            )
            EmailService.send_password_reset_email(
                user, token, self.context["request"]
            )
        return attrs


class PassowrdResetConfirmSerializer(serializers.Serializer):
    token = serializers.CharField()
    password = serializers.CharField(write_only=True, min_length=8)

    def validate(self, attrs):
        token = attrs["token"]
        password = attrs["password"]
        
        try:
            password_reset_token = PasswordResetToken.objects.get(token=token,is_used=False)
        except PasswordResetToken.DoesNotExist:
            raise serializers.ValidationError("Invalid Token")
        
        if not password_reset_token.is_valid():
            raise serializers.ValidationError("Token is already used")

        # check expiry
        if not password_reset_token.is_valid():
            raise serializers.ValidationError("Token has expired")

        # attach token object for later use
        attrs["password_reset_token"] = password_reset_token
        return attrs

    def save(self):
        password = self.validated_data["password"]
        password_reset_token = self.validated_data["password_reset_token"]

        user = password_reset_token.user
        user.change_password(password)
        user.save()

        password_reset_token.mark_as_used()
        return user

