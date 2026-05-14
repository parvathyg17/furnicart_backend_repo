from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import SignupSerializer, LoginSerializer,ForgotPasswordSerializer, ResetPasswordSerializer,OTPVerifySerializer, ResendOTPSerializer
from .services import user_login_service,create_and_send_otp,verify_otp_service, resend_otp_service,forgot_password_service, reset_password_service
from core.utils.jwt import get_tokens_for_user
from .models import User
from google.oauth2 import id_token
from google.auth.transport import requests

from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework.permissions import IsAuthenticated

from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken

from rest_framework.permissions import IsAuthenticated
from .serializers import ChangePasswordSerializer

from rest_framework_simplejwt.tokens import RefreshToken

class SignupView(APIView):

    permission_classes = [AllowAny]

    def post(self, request):

        email = request.data.get("email", "").lower().strip()

        existing_user = User.objects.filter(
            email__iexact=email
        ).first()

        

        if existing_user and not existing_user.is_verified:
            create_and_send_otp(existing_user, "signup")
            return Response({
                "status": "otp_resent",
                "message": "Account exists but not verified. OTP sent again.",
                "email": existing_user.email,
                "is_new_user": False
                },status=200)

        if existing_user and existing_user.is_verified:
            return Response({
                "status": "already_verified",
                "message": "Email already registered. Please login."
                }, status=400)

        serializer = SignupSerializer(
            data=request.data
        )

        if serializer.is_valid():

            user = serializer.save()
            create_and_send_otp(user, "signup")
            return Response({
                "status": "otp_sent",
                "message": "User created. OTP sent to email.",
                "email": user.email,
                "is_new_user": True},status=201)
        return Response(serializer.errors,status=400)


class LoginView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)

        if serializer.is_valid():
            user, error = user_login_service(
                serializer.validated_data['email'],
                serializer.validated_data['password']
            )

            if error:
                return Response({"error": error}, status=400)

            
            tokens = get_tokens_for_user(user)
            response = Response({
                "message": "Login successful",
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "username": user.username,
                    "is_admin": user.is_superuser,}
                    })
            response.set_cookie(
                key="access_token",
                value=tokens["access"],
                httponly=True,
                secure=settings.COOKIE_SECURE,
                samesite=settings.COOKIE_SAMESITE,
                path="/")
            response.set_cookie(
                key="refresh_token",
                value=tokens["refresh"],
                httponly=True,
                secure=settings.COOKIE_SECURE,
                samesite=settings.COOKIE_SAMESITE,
                path="/")
            return response
        return Response(serializer.errors, status=400)
    




class VerifyOTPView(APIView):

    permission_classes = [AllowAny]

    def post(self, request):

        serializer = OTPVerifySerializer(
            data=request.data
        )

        if serializer.is_valid():

            email = serializer.validated_data['email']
            otp = serializer.validated_data['otp']
            purpose = serializer.validated_data['purpose'].strip().lower()

            try:
                user = User.objects.get(
                    email=email
                )

            except User.DoesNotExist:

                return Response(
                    {"error": "User not found"},
                    status=400
                )

            success, error = verify_otp_service(
                user,
                otp,
                purpose=purpose
            )

            if not success:

                return Response(
                    {"error": error},
                    status=400
                )

            if purpose == "signup":

                return Response({
                    "message": "Email verified successfully"
                })

            return Response({
                "message": "OTP verified successfully"
            })

        return Response(
            serializer.errors,
            status=400
        )
    

class ResendOTPView(APIView):

    permission_classes = [AllowAny]

    def post(self, request):

        serializer = ResendOTPSerializer(data=request.data)

        if serializer.is_valid():

            email = serializer.validated_data['email']
            purpose = serializer.validated_data.get("purpose", "signup")

            print("RESEND OTP:", email, purpose)

            try:
                user = User.objects.get(email=email)

            except User.DoesNotExist:

                return Response(
                    {"error": "User not found"},
                    status=400
                )

            resend_otp_service(
                user,
                purpose=purpose
            )

            return Response({
                "message": "OTP resent successfully"
            })

        return Response(
            serializer.errors,
            status=400
        )
    




class ForgotPasswordView(APIView):
    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)

        if serializer.is_valid():
            user, error = forgot_password_service(
                serializer.validated_data['email']
            )

            if error:
                return Response({"error": error}, status=400)

            return Response({
                "message": "OTP sent to email"
            })

        return Response(serializer.errors, status=400)
    

class ResetPasswordView(APIView):
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)

        if serializer.is_valid():
            success, error = reset_password_service(
                serializer.validated_data['email'],
                serializer.validated_data['otp'],
                serializer.validated_data['new_password']
            )

            if not success:
                return Response({"error": error}, status=400)

            return Response({
                "message": "Password reset successful"
            })

        return Response(serializer.errors, status=400)
    


User = get_user_model()


class GoogleLoginView(APIView):

    def post(self, request):

        token = request.data.get("token")

        if not token:
            return Response({"error": "Token required"}, status=400)

        try:
            idinfo = id_token.verify_oauth2_token(
                token,
                requests.Request(),
                settings.GOOGLE_CLIENT_ID
            )

            email = idinfo["email"]
            name = idinfo.get("name", email.split("@")[0])

        except Exception:
            return Response({"error": "Invalid Google token"}, status=400)

        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "username": name,
                "is_verified": True,
                "is_active": True,
                "is_superuser": False,   
                "is_staff": False        
    }
)

        if user.is_superuser or user.is_staff:
            return Response(
                {"error": "Admin accounts cannot use Google login"},
                status=403
    )
       
        if not user.is_active:
            return Response(
                {"error": "User is blocked"},
                status=403
            )
        refresh = RefreshToken.for_user(user)
        response = Response({
            "message": "Google login successful",
            "user": {
                "email": user.email,
                "username": user.username
                },
                "is_new": created})
        response.set_cookie(
            key="access_token",
            value=str(refresh.access_token),
            httponly=True,
            secure=settings.COOKIE_SECURE,
            samesite=settings.COOKIE_SAMESITE,
            path="/")
        response.set_cookie(
            key="refresh_token",
            value=str(refresh),
            httponly=True,
            secure=settings.COOKIE_SECURE,
            samesite=settings.COOKIE_SAMESITE,
            path="/")
        return response
    



class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):

        refresh_token = request.COOKIES.get("refresh_token")

        if refresh_token:

            try:
                token = RefreshToken(refresh_token)
                token.blacklist()

            except Exception:
                pass

        response = Response({
            "message": "Logged out successfully"
        })

        response.delete_cookie("access_token",path="/",samesite=settings.COOKIE_SAMESITE,)
        response.delete_cookie(
            "refresh_token",
            path="/",
            samesite=settings.COOKIE_SAMESITE,)
        return response

class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        return Response({
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "is_verified": user.is_verified,
            "is_admin": user.is_superuser,
        })
    

class ChangePasswordView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):

        serializer = ChangePasswordSerializer(data=request.data)

        if serializer.is_valid():

            user = request.user

            old_password = serializer.validated_data["old_password"]
            new_password = serializer.validated_data["new_password"]

            
            if not user.check_password(old_password):
                return Response(
                    {"error": "Old password is incorrect"},
                    status=400
                )

            
            if old_password == new_password:
                return Response(
                    {"error": "New password cannot be same as old password"},
                    status=400
                )

            user.set_password(new_password)
            user.save()

            return Response({
                "message": "Password changed successfully"
            })

        return Response(serializer.errors, status=400)



