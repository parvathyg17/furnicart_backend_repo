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

# class UserOfferSavingsView(APIView):
#     permission_classes = [IsAuthenticated]
#     def get(self, request):
#         from orders.models import Order, OrderLine
#         from django.db.models import Sum
        
#         offer_savings = OrderLine.objects.filter(
#             order__user=request.user
#         ).exclude(
#             order__status__in=[Order.Status.CANCELLED, Order.Status.PARTIALLY_CANCELLED]
#         ).exclude(
#             status=OrderLine.LineStatus.CANCELLED
#         ).aggregate(total=Sum('discount_amount'))['total'] or 0.00
        
#         coupon_savings = Order.objects.filter(f
#             user=request.user
#         ).exclude(
#             status__in=[Order.Status.CANCELLED, Order.Status.PARTIALLY_CANCELLED]
#         ).aggregate(total=Sum('discount_total'))['total'] or 0.00
        
#         return Response({
#             "offer_savings": offer_savings,
#             "coupon_savings": coupon_savings,
#             "total_savings": offer_savings + coupon_savings
#         })



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
