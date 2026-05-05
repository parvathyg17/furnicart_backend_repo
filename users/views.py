from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import SignupSerializer, LoginSerializer,ForgotPasswordSerializer, ResetPasswordSerializer,OTPVerifySerializer, ResendOTPSerializer
from .services import user_login_service,create_and_send_otp,verify_otp_service, resend_otp_service,forgot_password_service, reset_password_service
from core.utils.jwt import get_tokens_for_user
from .models import User




class SignupView(APIView):
    def post(self, request):
        serializer = SignupSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.save()

            create_and_send_otp(user)

            return Response({
                "message": "User created. OTP sent to email."
            }, status=201)

        return Response(serializer.errors, status=400)


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

            return Response({
                "tokens": tokens,
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "username": user.username
                }
            })

        return Response(serializer.errors, status=400)
    




class VerifyOTPView(APIView):
    def post(self, request):
        serializer = OTPVerifySerializer(data=request.data)

        if serializer.is_valid():
            email = serializer.validated_data['email']
            otp = serializer.validated_data['otp']

            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return Response({"error": "User not found"}, status=400)

            success, error = verify_otp_service(user, otp)

            if not success:
                return Response({"error": error}, status=400)

            return Response({"message": "Email verified successfully"})

        return Response(serializer.errors, status=400)
    

class ResendOTPView(APIView):
    def post(self, request):
        serializer = ResendOTPSerializer(data=request.data)

        if serializer.is_valid():
            email = serializer.validated_data['email']

            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return Response({"error": "User not found"}, status=400)

            resend_otp_service(user)

            return Response({"message": "OTP resent successfully"})

        return Response(serializer.errors, status=400)
    




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