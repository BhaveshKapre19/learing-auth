from rest_framework import serializers
from authentication.models import EmailVerificationToken


class EmailVerifySerializer(serializers.Serializer):
    token = serializers.UUIDField()

    def validate(self, attrs):
        token_obj = EmailVerificationToken.objects.filter(
            token=attrs["token"],
            is_used=False
        ).first()

        if not token_obj or not token_obj.is_valid():
            raise serializers.ValidationError("Invalid or expired token")

        user = token_obj.user
        user.verify_email()
        token_obj.mark_as_used()

        return user
