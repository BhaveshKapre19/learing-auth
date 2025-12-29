"""
This module contains the models for user authentication, including custom user model,
password reset tokens, email verification tokens, multi-factor authentication codes,
and user profiles.
"""
from django.db import models
from django.contrib.auth.models import AbstractUser , BaseUserManager
from django.utils import timezone
from django.utils.text import slugify
import uuid
from authentication.services.secrets import SecretGenerator
from datetime import timedelta
from authentication.services.upload_path import user_profile_pic_path

class UserManager(BaseUserManager):
    """
    User manager for the custom User model.
    """
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('has_temp_password', False)
        extra_fields.setdefault('is_email_verified', True)
        extra_fields.setdefault('email_verified_at', timezone.now())

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)
    

class User(AbstractUser):
    username = None
    email = models.EmailField(unique=True,blank=False)
    is_active = models.BooleanField(default=False)
    slug = models.SlugField(unique=True)
    is_email_verified = models.BooleanField(default=False)
    email_verified_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    last_password_change = models.DateTimeField(null=True, blank=True)
    has_temp_password = models.BooleanField(default=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    objects = UserManager()

    def __str__(self):
        return self.email
    
    def verify_email(self):
        self.is_email_verified = True
        self.email_verified_at = timezone.now()
        self.is_active = True
        self.save()

    def change_password(self, new_password):
        self.set_password(new_password)
        self.last_password_change = timezone.now()
        self.has_temp_password = False
        self.save()

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.username or self.email.split('@')[0])
            self.slug = f"{base_slug}-{uuid.uuid4().hex[:8]}"
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'


class BaseToken(models.Model):
    """
    Base token model for password reset and email verification.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField(default=timezone.now)
    is_used = models.BooleanField(default=False)
    used_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(db_index=True)
    request_ip = models.GenericIPAddressField(null=True)
    device = models.CharField(max_length=255, null=True, blank=True)

    def mark_as_used(self):
        self.is_used = True
        self.used_at = timezone.now()
        self.save(update_fields=["is_used", "used_at"])

    def is_valid(self):
        return not self.is_used and timezone.now() < self.expires_at
    
    def is_expired(self):
        return timezone.now() >= self.expires_at

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=["token", "is_used"]),
        ]


class PasswordResetToken(BaseToken):

    user = models.ForeignKey(User,on_delete=models.CASCADE , related_name="password_reset_tokens")

    def __str__(self):
        return f"PasswordResetToken for {self.user.email} - {'Used' if self.is_used else 'Unused'}"
    
    class Meta:
        verbose_name = 'Password Reset Token'
        verbose_name_plural = 'Password Reset Tokens'

    

class EmailVerificationToken(BaseToken):
    user = models.ForeignKey(User,on_delete=models.CASCADE,related_name="email_verification_tokens")
    
    def __str__(self):
        return f"EmailVerificationToken for {self.user.email} - {'Used' if self.is_used else 'Unused'}"
    
    class Meta:
        verbose_name = 'Email Verification Token'
        verbose_name_plural = 'Email Verification Tokens'




class MultiFactorAuthCode(models.Model):
    """
    Model for storing Multi-Factor Authentication (MFA) codes.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="mfa_codes"
    )

    token = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField(db_index=True)

    request_ip = models.GenericIPAddressField(null=True, blank=True)
    device = models.CharField(max_length=255, null=True, blank=True)


    class Meta:
        verbose_name = "Multi-Factor Authentication Code"
        verbose_name_plural = "Multi-Factor Authentication Codes"
        indexes = [
            models.Index(fields=["token"]),
            models.Index(fields=["expires_at"]),
        ]

    @classmethod
    def create_code(cls, user, request, validity_minutes=5):
        cls.objects.filter(user=user).delete()
        raw_code = SecretGenerator.generate_mfa_code()
        token = SecretGenerator.generate_mfa_hash(user.email, raw_code)
        request_ip = request.META.get("REMOTE_ADDR", "Unknown")
        device = request.META.get("HTTP_USER_AGENT", "Unknown Device")

        obj = cls.objects.create(
            user=user,
            token=token,
            expires_at=timezone.now() + timedelta(minutes=validity_minutes),
            request_ip=request_ip,
            device=device
        )

        return obj, raw_code

    def validate_and_consume(self, code: str) -> bool:
        expected = SecretGenerator.generate_mfa_hash(self.user.email, code)

        if self.token != expected:
            return False

        if timezone.now() >= self.expires_at:
            self.delete()
            return False

        return True

    def __str__(self):
        return f"MFA Code for {self.user.email}"
    



class UserProfile(models.Model):
    """
    User profile model to store additional user information.
    """
    user = models.OneToOneField(User,on_delete=models.CASCADE,related_name="profile")
    bio = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to=user_profile_pic_path, default="media/default/default.jpg")
    multi_factor_enabled = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return f"Profile of {self.user.first_name} {self.user.last_name}"
    
    def restore(self):
        self.is_deleted = False
        self.save(update_fields=['is_deleted'])
    
    def delete(self, using=None, keep_parents=True):
        self.is_deleted = True
        self.save(update_fields=['is_deleted'])

    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'



class TempPasswordManager(models.Model):
    """
    Manager for temporary passwords, allowing users to change password after first login.
    """
    user = models.OneToOneField(User,on_delete=models.CASCADE,related_name="temp_password_manager")
    temp_password = models.CharField(max_length=20)
    created_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    used_at = models.DateTimeField(null=True, blank=True)

    def is_valid(self,password):
        if self.is_used or self.user.has_temp_password is False:
            return False
        if password != self.temp_password:
            return False
        return timezone.now() < self.expires_at

    def __str__(self):
        return f"Temp Password for {self.user.email}"

    def mark_as_used(self):
        self.is_used = True
        self.used_at = timezone.now()
        self.save(update_fields=["is_used", "used_at"])
    

    @classmethod
    def create_temp_password(cls, user, validity_hours=24):
        temp_password = SecretGenerator.generate_temp_password()
        obj = cls.objects.create(
            user=user,
            temp_password=temp_password,
            expires_at=timezone.now() + timedelta(hours=validity_hours)
        )
        return obj, temp_password
    
    class Meta:
        verbose_name = 'Temporary Password Manager'
        verbose_name_plural = 'Temporary Password Managers'

