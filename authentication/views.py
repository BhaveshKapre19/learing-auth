#authentication/views.py
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.permissions import IsAuthenticated , IsAdminUser , AllowAny
from rest_framework.response import Response
from rest_framework import viewsets 
from rest_framework.views import APIView
from rest_framework import status
from .serializers import (profile,register,password_reset)

from .permissions import HasTemporaryPassword,IsActiveUser,IsEmailVerified

from .models import User , EmailVerificationToken
from django.utils import timezone
from datetime import timedelta

from email_service import EmailService


from rest_framework.throttling import UserRateThrottle

class EmailResendThrottle(UserRateThrottle):
    rate = "3/hour"



class MeView(RetrieveUpdateAPIView):
    permission_classes = [HasTemporaryPassword,IsActiveUser,IsEmailVerified]
    serializer_class = profile.MeSerializer

    def get_object(self):
        return self.request.user.profile
    

"""
this model is admin only model need the admin to access this route
"""
class AdminUsersView(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    serializer_class = profile.AdminUserSerializer
    lookup_field = 'slug'
    
    def get_queryset(self):
        return User.objects.all()
    


"""
this will handel the email verification
"""
class EmailVerificationView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, token, *args, **kwargs):
        email_token = EmailVerificationToken.objects.filter(token=token).first()

        if not email_token:
            return Response(
                {"error": "Invalid token"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not email_token.is_valid():
            return Response(
                {"error": "Token expired or already used"},
                status=status.HTTP_400_BAD_REQUEST
            )

        email_token.mark_as_used()
        email_token.user.verify_email()

        return Response(
            {"message": "Email verified successfully"},
            status=status.HTTP_200_OK
        )



class ResendEmailVerificationView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [EmailResendThrottle]

    def post(self, request, *args, **kwargs):
        user = request.user

        if user.is_email_verified:
            return Response(
                {"message": "Email is already verified"},
                status=status.HTTP_400_BAD_REQUEST
            )

        EmailVerificationToken.objects.filter(
            user=user,
            is_used=False,
            expires_at__gt=timezone.now()
        ).update(
            is_used=True,
            used_at=timezone.now()
        )

        token = EmailVerificationToken.objects.create(
            user=user,
            expires_at=timezone.now() + timedelta(hours=24),
            request_ip=self.get_client_ip(request),
            device=request.META.get("HTTP_USER_AGENT", "")
        )

        EmailService.send_verification_email(user, token)

        return Response(
            {"message": "Verification email resent successfully"},
            status=status.HTTP_200_OK
        )


"""
user registration view
"""

class RegisterUserView(APIView):
    permission_classes = [IsAdminUser]

    def post(self,request,*args,**kwargs):
        serializer = register.RegisterSerializer(request.data)

        if not serializer.is_valid():
            return Response(
                serializer.errors,status=status.HTTP_400_BAD_REQUEST
            )
        
        user = serializer.save()

        return Response(
            {
                "message": "User registered successfully Check your email for verification code",
                "user_id": user.id,
                "email": user.email,
            },
            status=status.HTTP_201_CREATED
        )




"""
password reset view
"""


class PasswordResetRequestView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self,request,*args,**kwargs):
        user = request.user
        password_reset = password_reset.PasswordResetRequestSerializer(request.data)
        if password_reset.is_valid():
            return Response(
                {"message":"Password Reset link send to your email please check the email for the instructions"},
                status=status.HTTP_200_OK
            )
        
        return Response(
            password_reset.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]

    def post(self,request,*args,**kwargs):
        serializer = password_reset.PassowrdResetConfirmSerializer(request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message":"Password Reset successfully"},
                status=status.HTTP_200_OK
            )
        
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )
    
        
            














