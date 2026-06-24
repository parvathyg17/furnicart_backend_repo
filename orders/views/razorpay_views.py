from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from orders.serializers import (
    RazorpayInitiateSerializer,
    RazorpayVerifySerializer,
)
from orders.services.razorpay_services import (
    handle_razorpay_webhook,
    initiate_razorpay_checkout,
    serialize_order_response,
    verify_razorpay_payment,
)


def _validation_error_response(exc):

    if isinstance(exc.detail, dict):

        return Response(
            exc.detail,
            status=status.HTTP_400_BAD_REQUEST,
        )

    if isinstance(exc.detail, list):

        return Response(
            {"detail": exc.detail},
            status=status.HTTP_400_BAD_REQUEST,
        )

    return Response(
        {"detail": str(exc.detail)},
        status=status.HTTP_400_BAD_REQUEST,
    )


class RazorpayInitiateView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):

        serializer = RazorpayInitiateSerializer(
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        try:

            payload = initiate_razorpay_checkout(
                request.user,
                serializer.validated_data[
                    "address_id"
                ],
            )

        except ValidationError as exc:

            return _validation_error_response(
                exc,
            )

        return Response(
            payload,
            status=status.HTTP_201_CREATED,
        )


class RazorpayVerifyView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):

        serializer = RazorpayVerifySerializer(
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        data = serializer.validated_data

        try:

            order = verify_razorpay_payment(
                request.user,
                razorpay_order_id=data[
                    "razorpay_order_id"
                ],
                razorpay_payment_id=data[
                    "razorpay_payment_id"
                ],
                razorpay_signature=data[
                    "razorpay_signature"
                ],
            )

        except ValidationError as exc:

            return _validation_error_response(
                exc,
            )

        return Response(
            serialize_order_response(
                order,
            ),
            status=status.HTTP_200_OK,
        )


@method_decorator(
    csrf_exempt,
    name="dispatch",
)
class RazorpayWebhookView(APIView):

    authentication_classes = []

    permission_classes = [AllowAny]

    def post(self, request):

        signature = request.headers.get(
            "X-Razorpay-Signature",
            "",
        )

        handle_razorpay_webhook(
            request.body,
            signature,
        )

        return Response(
            {"status": "ok"},
            status=status.HTTP_200_OK,
        )
