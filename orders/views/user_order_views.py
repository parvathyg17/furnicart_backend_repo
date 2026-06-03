from rest_framework import status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from orders.models import Order
from orders.serializers import (
    OrderCreateSerializer,
    OrderDetailSerializer,
)
from orders.services.order_services import (
    create_order_from_cart,
    get_order_for_user,
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


class OrderCreateView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):

        serializer = OrderCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:

            order = create_order_from_cart(
                request.user,
                data["address_id"],
                tax_total=data.get("tax_total"),
                discount_total=data.get("discount_total"),
                shipping_total=data.get("shipping_total"),
            )

        except ValidationError as exc:

            return _validation_error_response(exc)

        return Response(
            OrderDetailSerializer(order).data,
            status=status.HTTP_201_CREATED,
        )


class OrderDetailView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request, order_number):

        try:

            order = get_order_for_user(
                request.user,
                order_number,
            )

        except Order.DoesNotExist:

            raise NotFound(detail="Order not found.")

        return Response(OrderDetailSerializer(order).data)
