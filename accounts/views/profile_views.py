from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models.otp import OTP
from accounts.models.profile import UserProfile
from accounts.serializers.profile_serializers import (
    EmailChangeRequestSerializer,
    EmailChangeVerifySerializer,
    UserProfileSerializer,
)
from accounts.services.profile_services import (
    send_email_change_otp,
    verify_email_change,
)



class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request):
        profile = UserProfile.objects.get(user=request.user)
        serializer = UserProfileSerializer(
            profile,
            context={"request": request},
        )
        return Response(serializer.data)

    def put(self, request):
        profile = UserProfile.objects.get(user=request.user)
        serializer = UserProfileSerializer(
            profile,
            data=request.data,
            partial=True,
            context={"request": request},
        )
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer.save()
        return Response(serializer.data)


class EmailChangeRequestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = EmailChangeRequestSerializer(
            data=request.data,
            context={"request": request},
        )
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        new_email = serializer.validated_data["new_email"]
        otp_code = send_email_change_otp(request.user, new_email)
        OTP.objects.filter(
            user=request.user,
            purpose="email_change",
            otp=otp_code,
        ).update(extra_data={"new_email": new_email})

        return Response(
            {
                "message": "OTP sent to new email",
                "email": new_email,
            }
        )


class EmailChangeVerifyView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = EmailChangeVerifySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        new_email = serializer.validated_data["new_email"]
        otp = serializer.validated_data["otp"]
        success, error = verify_email_change(request.user, new_email, otp)
        if not success:
            return Response(
                {"error": error},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response({"message": "Email updated successfully. Please login again."})
