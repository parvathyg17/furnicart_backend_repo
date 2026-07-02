from django.conf import settings
from google.auth.transport import requests
from google.oauth2 import id_token
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models.profile import UserProfile
from accounts.models.users import User
from accounts.serializers.auth_serializers import (
    ChangePasswordSerializer,
    ForgotPasswordSerializer,
    LoginSerializer,
    OTPVerifySerializer,
    ResendOTPSerializer,
    ResetPasswordSerializer,
    SignupSerializer,
)
from accounts.services.auth_services import (
    create_and_send_otp,
    forgot_password_service,
    resend_otp_service,
    reset_password_service,
    user_login_service,
    verify_otp_service,
)
from core.utils.jwt import get_tokens_for_user


class SignupView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email", "").lower().strip()
        existing_user = User.objects.filter(email__iexact=email).first()

        if existing_user and not existing_user.is_verified:
            create_and_send_otp(existing_user, "signup")
            return Response(
                {
                    "status": "otp_resent",
                    "message": "Account exists but not verified. OTP sent again.",
                    "email": existing_user.email,
                    "is_new_user": False,
                },
                status=status.HTTP_200_OK,
            )

        if existing_user and existing_user.is_verified:
            return Response(
                {
                    "status": "already_verified",
                    "message": "Email already registered. Please login.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = SignupSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = serializer.save()
        create_and_send_otp(user, "signup")
        return Response(
            {
                "status": "otp_sent",
                "message": "User created. OTP sent to email.",
                "email": user.email,
                "is_new_user": True,
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        user, error = user_login_service(
            serializer.validated_data["email"],
            serializer.validated_data["password"],
        )
        if error:
            return Response(
                {"error": error},
                status=status.HTTP_400_BAD_REQUEST,
            )

        tokens = get_tokens_for_user(user)
        response = Response(
            {
                "message": "Login successful",
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "username": user.username,
                    "is_admin": user.is_superuser,
                },
            }
        )
        response.set_cookie(
            key="access_token",
            value=tokens["access"],
            httponly=True,
            secure=settings.COOKIE_SECURE,
            samesite=settings.COOKIE_SAMESITE,
            path="/",
        )
        response.set_cookie(
            key="refresh_token",
            value=tokens["refresh"],
            httponly=True,
            secure=settings.COOKIE_SECURE,
            samesite=settings.COOKIE_SAMESITE,
            path="/",
        )
        return response


class VerifyOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = OTPVerifySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        email = serializer.validated_data["email"]
        otp = serializer.validated_data["otp"]
        purpose = serializer.validated_data["purpose"].strip().lower()

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {"error": "User not found"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        success, error = verify_otp_service(user, otp, purpose=purpose)
        if not success:
            return Response(
                {"error": error},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if purpose == "signup":
            from promotions.services.referral_services import (
                try_attach_referral_on_signup,
            )

            try_attach_referral_on_signup(
                user,
                referral_token=serializer.validated_data.get("referral_token"),
                referral_code=serializer.validated_data.get("referral_code"),
            )
            return Response({"message": "Email verified successfully"})

        return Response({"message": "OTP verified successfully"})


class ResendOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ResendOTPSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        email = serializer.validated_data["email"]
        purpose = serializer.validated_data.get("purpose", "signup")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {"error": "User not found"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        success, error = resend_otp_service(user, purpose=purpose)
        if not success:
            return Response(
                {"error": error},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response({"message": "OTP resent successfully"})


class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        _user, error = forgot_password_service(serializer.validated_data["email"])
        if error:
            return Response(
                {"error": error},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response({"message": "OTP sent to email"})


class ResetPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        success, error = reset_password_service(
            serializer.validated_data["email"],
            serializer.validated_data["otp"],
            serializer.validated_data["new_password"],
        )
        if not success:
            return Response(
                {"error": error},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response({"message": "Password reset successful"})


class GoogleLoginView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        token = request.data.get("token")
        if not token:
            return Response(
                {"error": "Token required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            idinfo = id_token.verify_oauth2_token(
                token,
                requests.Request(),
                settings.GOOGLE_CLIENT_ID,
            )
            email = idinfo["email"]
            name = idinfo.get("name", email.split("@")[0])
        except Exception:
            return Response(
                {"error": "Invalid Google token"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "username": name,
                "is_verified": True,
                "is_active": True,
                "is_superuser": False,
                "is_staff": False,
            },
        )

        if created:
            from promotions.services.referral_services import (
                try_attach_referral_on_signup,
            )

            try_attach_referral_on_signup(
                user,
                referral_token=request.data.get("referral_token"),
                referral_code=request.data.get("referral_code"),
            )

        if user.is_superuser or user.is_staff:
            return Response(
                {"error": "Admin accounts cannot use Google login"},
                status=status.HTTP_403_FORBIDDEN,
            )

        if not user.is_active:
            return Response(
                {"error": "User is blocked"},
                status=status.HTTP_403_FORBIDDEN,
            )

        refresh = RefreshToken.for_user(user)
        response = Response(
            {
                "message": "Google login successful",
                "user": {"email": user.email, "username": user.username},
                "is_new": created,
            }
        )
        response.set_cookie(
            key="access_token",
            value=str(refresh.access_token),
            httponly=True,
            secure=settings.COOKIE_SECURE,
            samesite=settings.COOKIE_SAMESITE,
            path="/",
        )
        response.set_cookie(
            key="refresh_token",
            value=str(refresh),
            httponly=True,
            secure=settings.COOKIE_SECURE,
            samesite=settings.COOKIE_SAMESITE,
            path="/",
        )
        return response


class LogoutView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        refresh_token = request.COOKIES.get("refresh_token")
        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
            except Exception:
                pass

        response = Response({"message": "Logged out successfully"})
        response.delete_cookie(
            "access_token",
            path="/",
            samesite=settings.COOKIE_SAMESITE,
        )
        response.delete_cookie(
            "refresh_token",
            path="/",
            samesite=settings.COOKIE_SAMESITE,
        )
        return response


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        payload = {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "is_verified": user.is_verified,
            "is_admin": user.is_superuser,
            "profile_image": None,
            "phone": None,
            "date_of_birth": None,
        }

        try:
            prof = UserProfile.objects.get(user=user)
        except UserProfile.DoesNotExist:
            pass
        else:
            if prof.profile_image:
                payload["profile_image"] = prof.profile_image.url
            if prof.phone:
                payload["phone"] = prof.phone
            if prof.date_of_birth:
                payload["date_of_birth"] = prof.date_of_birth.isoformat()

        return Response(payload)


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = request.user
        old_password = serializer.validated_data["old_password"]
        new_password = serializer.validated_data["new_password"]

        if not user.check_password(old_password):
            return Response(
                {"error": "Old password is incorrect"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if old_password == new_password:
            return Response(
                {"error": "New password cannot be same as old password"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(new_password)
        user.save()
        return Response({"message": "Password changed successfully"})
