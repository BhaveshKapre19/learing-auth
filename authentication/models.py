"""
Docstring for authentication.models


This module contains the models for user authentication, including custom user model,
password reset tokens, email verification tokens, multi-factor authentication codes,
and user profiles.

the point is user slug is editable because if there is a mistake in users name or something 
then we can change it later 




"""
from django.db import models
from django.contrib.auth.models import AbstractUser , BaseUserManager
from django.utils import timezone
from django.utils.text import slugify
import uuid
from authentication.services.secrets import SecretGenerator
from datetime import timedelta


"""this is the user manager for the custom user model"""
class UserManager(BaseUserManager):
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

    def set_slug(self):
        self.slug = slugify(f"{self.first_name}-{self.last_name}-{uuid.uuid4()}")

    def save(self, *args, **kwargs):
        if not self.slug:
            self.set_slug()
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'


"""
this is the base token model for the password reset and the email verification 

the token will be send to the user in the email 

but the catch is the token will be stored in the database for validation

and now the token will be in the url its just the one time url which will has that token

"""
class BaseToken(models.Model):
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




"""
this is the login multi factor code model

the user will login first with email and password

then if they have multi factor enabled, a code will be generated and sent to their email
then they will have to enter the code to complete the login process

now there is a catch we need a good urls for the models views  and we can change the process or add some 
more things later

the code will be genreted and will expire in 5 minutes  

the code will be the combination of the integers and the letters and some special characters

this will be the good security measure for the multi factor authentication

now the code will be send into the email for the user to enter it in the login process

and the token is not shown to the user but the token will be strored in the database for validation

"""

class MultiFactorAuthCode(models.Model):
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
    def create_code(cls, user, validity_minutes=5):
        cls.objects.filter(user=user).delete()
        raw_code = SecretGenerator.generate_mfa_code()
        token = SecretGenerator.generate_mfa_hash(user.email, raw_code)

        obj = cls.objects.create(
            user=user,
            token=token,
            expires_at=timezone.now() + timedelta(minutes=validity_minutes)
        )

        return obj, raw_code

    def validate_and_consume(self, code: str) -> bool:
        expected = SecretGenerator.generate_mfa_hash(self.user.email, code)

        if self.token != expected:
            return False

        if timezone.now() >= self.expires_at:
            self.delete()
            return False

        self.delete()
        return True

    def __str__(self):
        return f"MFA Code for {self.user.email}"
    



"""
this is the user profile model

"""
class UserProfile(models.Model):
    user = models.OneToOneField(User,on_delete=models.CASCADE,related_name="profile")
    bio = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)
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



"""
this is the custom password manager where there are the temp passwords are stored
and user can chanage it after first login

"""

class TempPasswordManager(models.Model):
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

