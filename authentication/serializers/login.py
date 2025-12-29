from rest_framework import serializers
from django.contrib.auth import authenticate

from authentication.models import User, MultiFactorAuthCode
from authentication.services.email_service import EmailService


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
            return {
                "mfa_required": True,
                "user_id": user.id,
                "email": user.email,
            }

        return {
            "mfa_required": False,
            "user": user
        }


class GetTheMFACodeSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField()

    def validate(self, attrs):
        mfa_obj = MultiFactorAuthCode.objects.filter(user__email=attrs["email"]).first()
        if not mfa_obj:
            raise serializers.ValidationError("Invalid credentials")

        if not mfa_obj.validate_and_consume(attrs["code"]):
            raise serializers.ValidationError("Invalid code")

        return {
            "user": mfa_obj.user,
            "mfa_verified": True
        }

    

