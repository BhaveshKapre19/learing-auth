from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    MeView,
    AdminUsersView,
    EmailVerificationView,
    ResendEmailVerificationView,
    RegisterUserView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
    ChangeTempPassword,
    LoginView,
    GetTheMFACode,
)

router = DefaultRouter()
router.register(
    r"admin/users",
    AdminUsersView,
    basename="admin-users"
)

urlpatterns = [

    path("login/", LoginView.as_view(), name="login"),
    path("login/verify-mfa/", GetTheMFACode.as_view(), name="login-verify-mfa"),
    # ─────────────────────────────
    # User self
    # ─────────────────────────────
    path("me/", MeView.as_view(), name="me"),

    # ─────────────────────────────
    # Registration (admin only)
    # ─────────────────────────────
    path("register/", RegisterUserView.as_view(), name="register"),

    # ─────────────────────────────
    # Email verification
    # ─────────────────────────────
    path(
        "email/verify/<uuid:token>/",
        EmailVerificationView.as_view(),
        name="email-verify"
    ),
    path(
        "email/resend/",
        ResendEmailVerificationView.as_view(),
        name="email-resend"
    ),

    # ─────────────────────────────
    # Password reset
    # ─────────────────────────────
    path(
        "password/reset/",
        PasswordResetRequestView.as_view(),
        name="password-reset-request"
    ),
    path(
        "password/reset/confirm/",
        PasswordResetConfirmView.as_view(),
        name="password-reset-confirm"
    ),

    # ─────────────────────────────
    # Temporary password change
    # ─────────────────────────────
    path(
        "password/change-temp/",
        ChangeTempPassword.as_view(),
        name="change-temp-password"
    ),

    # ─────────────────────────────
    # Admin routes (ViewSet)
    # ─────────────────────────────
    path("", include(router.urls)),
]
