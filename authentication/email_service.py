# authentication/email_service.py


from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils import timezone
from django.conf import settings


class EmailService:

    @staticmethod
    def _send(subject, template, context, to_email):
        html_message = render_to_string(template, context)
        plain_message = strip_tags(html_message)

        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[to_email],
            html_message=html_message,
            fail_silently=False,
        )

    @staticmethod
    def send_verification_email(user, token):
        context = {
            'user': user,
            'verification_url': f"{settings.FRONTEND_BASE_URL}/verify/{token.token}",
            'expiration_hours': 24,
            'site_name': settings.SITE_NAME,
            'current_year': timezone.now().year,
        }

        EmailService._send(
            subject="Verify Your Email Address",
            template="emails/email_verification/verification_email.html",
            context=context,
            to_email=user.email,
        )

    @staticmethod
    def send_password_reset_email(user, token, request):
        context = {
            'user': user,
            'reset_url': f"{settings.FRONTEND_BASE_URL}/reset-password/{token.token}",
            'expiration_hours': 1,
            'request_time': timezone.now().strftime('%Y-%m-%d %H:%M:%S UTC'),
            'request_ip': request.META.get('REMOTE_ADDR', 'Unknown'),
            'site_name': settings.SITE_NAME,
            'current_year': timezone.now().year,
        }

        EmailService._send(
            subject="Reset Your Password",
            template="emails/password_reset/reset_password_email.html",
            context=context,
            to_email=user.email,
        )

    @staticmethod
    def send_mfa_code_email(user, code, request):
        context = {
            'user': user,
            'mfa_code': code,
            'validity_minutes': 5,
            'request_time': timezone.now().strftime('%Y-%m-%d %H:%M:%S UTC'),
            'request_ip': request.META.get('REMOTE_ADDR', 'Unknown'),
            'device_info': request.META.get('HTTP_USER_AGENT', 'Unknown Device'),
            'site_name': settings.SITE_NAME,
            'current_year': timezone.now().year,
        }

        EmailService._send(
            subject="Your Login Code",
            template="emails/mfa_code/mfa_code_email.html",
            context=context,
            to_email=user.email,
        )

    @staticmethod
    def send_welcome_email(user, temp_password, activation_token):
        context = {
            'user': user,
            'temp_password': temp_password,
            'expiration_hours': 24,
            'activation_url': f"{settings.FRONTEND_BASE_URL}/activate/{activation_token.token}",
            'support_url': settings.SUPPORT_URL,
            'site_name': settings.SITE_NAME,
            'current_year': timezone.now().year,
        }

        EmailService._send(
            subject=f"Welcome to {settings.SITE_NAME}!",
            template="emails/onboarding/welcome_email.html",
            context=context,
            to_email=user.email,
        )
