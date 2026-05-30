from decimal import Decimal

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from rest_framework.exceptions import (
    ValidationError as DRFValidationError,
)

from cart.serializers import (
    CartItemSerializer,
    CartItemQuantitySerializer,
)

from .services import (
    add_to_cart,
    get_cart_payload,
    remove_cart_item,
    update_cart_item_quantity,
    validate_cart_for_checkout,
)


class CartView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        _, items, subtotal, item_count, can_checkout = get_cart_payload(
            request.user,
        )

        serializer = CartItemSerializer(
            items,
            many=True,
            context={
                "request": request,
            },
        )

        return Response(
            {
                "items": serializer.data,

                "item_count": item_count,

                "subtotal": str(
                    subtotal.quantize(
                        Decimal("0.01"),
                    )
                ),

                "can_checkout": can_checkout,
            }
        )

    def post(self, request):

        variant_id = request.data.get(
            "variant_id",
        )

        quantity = request.data.get(
            "quantity",
            1,
        )

        if variant_id is None:

            return Response(
                {
                    "error": "variant_id is required.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:

            variant_id = int(variant_id)

            quantity = int(quantity)

        except (TypeError, ValueError):

            return Response(
                {
                    "error": "variant_id and quantity must be integers.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:

            item = add_to_cart(
                request.user,
                variant_id,
                quantity,
            )

        except DRFValidationError as exc:

            return Response(
                exc.detail,
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = CartItemSerializer(
            item,
            context={
                "request": request,
            },
        )

        _, items, subtotal, item_count, can_checkout = get_cart_payload(
            request.user,
        )

        return Response(
            {
                "item": serializer.data,

                "items": CartItemSerializer(
                    items,
                    many=True,
                    context={
                        "request": request,
                    },
                ).data,

                "item_count": item_count,

                "subtotal": str(
                    subtotal.quantize(
                        Decimal("0.01"),
                    )
                ),

                "can_checkout": can_checkout,
            },
            status=status.HTTP_201_CREATED,
        )


class CartItemDetailView(APIView):

    permission_classes = [IsAuthenticated]

    def patch(
        self,
        request,
        item_id,
    ):

        ser = CartItemQuantitySerializer(
            data=request.data,
        )

        ser.is_valid(
            raise_exception=True,
        )

        try:

            item = update_cart_item_quantity(
                request.user,
                item_id,
                ser.validated_data["quantity"],
            )

        except DRFValidationError as exc:

            return Response(
                exc.detail,
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            CartItemSerializer(
                item,
                context={
                    "request": request,
                },
            ).data,
        )

    def delete(
        self,
        request,
        item_id,
    ):

        try:

            remove_cart_item(
                request.user,
                item_id,
            )

        except DRFValidationError as exc:

            return Response(
                exc.detail,
                status=status.HTTP_400_BAD_REQUEST,
            )

        _, items, subtotal, item_count, can_checkout = get_cart_payload(
            request.user,
        )

        return Response(
            {
                "items": CartItemSerializer(
                    items,
                    many=True,
                    context={
                        "request": request,
                    },
                ).data,

                "item_count": item_count,

                "subtotal": str(
                    subtotal.quantize(
                        Decimal("0.01"),
                    )
                ),

                "can_checkout": can_checkout,
            }
        )


class CartCheckoutValidateView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):

        result = validate_cart_for_checkout(
            request.user,
        )

        if result["valid"]:

            return Response(
                result,
                status=status.HTTP_200_OK,
            )

        return Response(
            result,
            status=status.HTTP_400_BAD_REQUEST,
        )
