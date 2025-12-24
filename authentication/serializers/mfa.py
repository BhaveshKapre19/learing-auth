from rest_framework import serializers
from authentication.models import MultiFactorAuthCode


class MFAVerifySerializer(serializers.Serializer):
    code = serializers.CharField()

    def validate(self, attrs):
        user = self.context["user"]

        mfa_obj = MultiFactorAuthCode.objects.filter(user=user).first()
        if not mfa_obj:
            raise serializers.ValidationError("MFA session expired")

        if not mfa_obj.validate_and_consume(attrs["code"]):
            raise serializers.ValidationError("Invalid MFA code")

        return user
