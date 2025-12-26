# authentication/secrets.py

import string
import hmac
import hashlib
import secrets
from django.conf import settings


class SecretGenerator:

    @staticmethod
    def generate_mfa_hash(email: str, code: str) -> str:
        message = f"{email}:{code}".encode()
        return hmac.new(
            settings.SECRET_KEY.encode(),
            message,
            hashlib.sha256
        ).hexdigest()

    @staticmethod
    def generate_mfa_code(length=8) -> str:
        alphabet = string.ascii_letters + string.digits
        return "".join(secrets.choice(alphabet) for _ in range(length))
    

    @staticmethod
    def generate_temp_password(length=12) -> str:
        alphabet = string.ascii_letters + string.digits + string.punctuation
        return "".join(secrets.choice(alphabet) for _ in range(length))
