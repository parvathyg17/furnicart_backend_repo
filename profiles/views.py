from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import UserProfile
from users.models import OTP
from .serializers import UserProfileSerializer,EmailChangeRequestSerializer,EmailChangeVerifySerializer
from core.utils.permissions import IsOwner
from .services import send_email_change_otp, verify_email_change
from google.oauth2 import id_token
from google.auth.transport import requests

from django.conf import settings
from django.contrib.auth import get_user_model

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework_simplejwt.tokens import RefreshToken


class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]  

    # 🔹 GET profile (own only)
    def get(self, request):
        profile = UserProfile.objects.get(user=request.user)
        serializer = UserProfileSerializer(profile)

        return Response(serializer.data)

    # 🔹 UPDATE profile (own only)
    def put(self, request):
        profile = UserProfile.objects.get(user=request.user)

        serializer = UserProfileSerializer(
            profile,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors, status=400)
    


class EmailChangeRequestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):

        serializer = EmailChangeRequestSerializer(
            data=request.data,
            context={"request": request}
        )

        if serializer.is_valid():
            new_email = serializer.validated_data['new_email']

            # store OTP with context
            otp_code = send_email_change_otp(request.user, new_email)

            OTP.objects.filter(
                user=request.user,
                purpose="email_change",
                otp=otp_code
            ).update(extra_data={"new_email": new_email})

            return Response({
                "message": "OTP sent to new email",
                "email": new_email
            })

        return Response(serializer.errors, status=400)
    

class EmailChangeVerifyView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):

        serializer = EmailChangeVerifySerializer(data=request.data)

        if serializer.is_valid():

            new_email = serializer.validated_data['new_email']
            otp = serializer.validated_data['otp']

            success, error = verify_email_change(
                request.user,
                new_email,
                otp
            )

            if not success:
                return Response({"error": error}, status=400)

            return Response({
                "message": "Email updated successfully. Please login again."
            })

        return Response(serializer.errors, status=400)
    

    
    

