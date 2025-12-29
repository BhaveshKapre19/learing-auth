#authentication/views.py
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.permissions import IsAuthenticated , IsAdminUser , AllowAny
from rest_framework.response import Response
from rest_framework import viewsets 
from rest_framework.views import APIView
from rest_framework import status
from .serializers import (profile,register,password_reset,login,password_reset)
from .models import User , EmailVerificationToken , MultiFactorAuthCode
from django.utils import timezone
from datetime import timedelta
from rest_framework.throttling import UserRateThrottle
import uuid
from rest_framework_simplejwt.tokens import RefreshToken
from authentication.services.email_service import EmailService
from authentication.services.permissions import HasTemporaryPassword,IsActiveUser,IsEmailVerified,RequiresTempPassword

class EmailResendThrottle(UserRateThrottle):
    rate = "3/hour"



class MeView(RetrieveUpdateAPIView):
    permission_classes = [IsActiveUser,IsEmailVerified]
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
        try:
            token = uuid.UUID(token)
        except ValueError:
            return Response({"error": "Invalid token"}, status=400)

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
        serializer = register.RegisterSerializer(data=request.data)

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
    permission_classes = [AllowAny]
    throttle_classes = [EmailResendThrottle]
    
    def post(self,request,*args,**kwargs):
        password_reset_obj  = password_reset.PasswordResetRequestSerializer(data=request.data,context={"request": request})
        if password_reset_obj.is_valid():
            return Response(
                {"message":"Password Reset link send to your email please check the email for the instructions"},
                status=status.HTTP_200_OK
            )
        
        return Response(
            password_reset_obj.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]

    def post(self,request,*args,**kwargs):
        serializer = password_reset.PassowrdResetConfirmSerializer(data=request.data,context={"request": request})
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
    
        
            
class ChangeTempPassword(APIView):
    permission_classes = [RequiresTempPassword]
    
    def post(self,request,*args,**kwargs):
        serializer = password_reset.ChangeTempPasswordSerializer(data=request.data,context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message":"Password changed successfully"},
                status=status.HTTP_200_OK
            )
        
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )



"""
this is the login view now
"""
class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = login.LoginSerializer(
            data=request.data,
            context={"request": request}
        )

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        data = serializer.validated_data

        # MFA REQUIRED → DO NOT ISSUE TOKENS
        if data["mfa_required"]:
            user = data["email"]
            mfa_obj, raw_code = MultiFactorAuthCode.create_code(user,request)
            EmailService.send_mfa_code_email(user, raw_code, request)
            return Response(
                {
                    "message": "MFA verification required",
                    "mfa_required": True,
                    "code_sent": True,
                    "user_email":data['email']
                },
                status=status.HTTP_200_OK
            )

        # NO MFA → ISSUE TOKENS
        user = data["user"]

        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "message": "Login successfully",
                "mfa_required": False,
                "tokens": {
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                }
            },
            status=status.HTTP_200_OK
        )



class GetTheMFACode(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = login.GetTheMFACodeSerializer(
            data=request.data,
            context={"request": request}
        )

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        data = serializer.validated_data

        refresh = RefreshToken.for_user(data["user"])

        return Response(
            {
                "message": "Login successfully",
                "tokens": {
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                }
            },
            status=status.HTTP_200_OK
        )

