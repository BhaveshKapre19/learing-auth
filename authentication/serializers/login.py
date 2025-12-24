from rest_framework import serializers
from django.contrib.auth import authenticate

from authentication.models import User, MultiFactorAuthCode
from authentication.email_service import EmailService


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, attrs):
        user = authenticate(
            email=attrs["email"],
            password=attrs["password"]
        )

        if not user:
            raise serializers.ValidationError("Invalid credentials")

        if not user.is_email_verified:
            raise serializers.ValidationError("Email not verified")

        # MFA flow
        if user.profile.multi_factor_enabled:
            mfa_obj, raw_code = MultiFactorAuthCode.create_code(user)
            EmailService.send_mfa_code_email(user, raw_code, self.context["request"])

            return {
                "mfa_required": True,
                "user_id": user.id
            }

        return {
            "mfa_required": False,
            "user": user
        }
