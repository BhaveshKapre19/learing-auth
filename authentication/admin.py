from django.contrib import admin
from .models import User, PasswordResetToken, EmailVerificationToken, MultiFactorAuthCode, UserProfile

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'is_active', 'is_staff', 'is_superuser', 'created_at')
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'is_email_verified')
    search_fields = ('email', 'slug')
    ordering = ('-created_at',)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'multi_factor_enabled', 'is_deleted')
    list_filter = ('multi_factor_enabled', 'is_deleted')
    search_fields = ('user__email', 'bio')

@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_used', 'expires_at', 'created_at')
    list_filter = ('is_used',)
    search_fields = ('user__email',)

@admin.register(EmailVerificationToken)
class EmailVerificationTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_used', 'expires_at', 'created_at')
    list_filter = ('is_used',)
    search_fields = ('user__email',)

@admin.register(MultiFactorAuthCode)
class MultiFactorAuthCodeAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at', 'expires_at')
    search_fields = ('user__email',)
