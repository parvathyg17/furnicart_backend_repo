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
    build_checkout_preview,
    get_available_coupons_payload,
    get_cart_payload,
    remove_cart_item,
    update_cart_item_quantity,
    validate_cart_for_checkout,
)

from promotions.services.coupon_cart_services import (
    apply_coupon_to_cart,
    remove_coupon_from_cart,
)


class CartView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        payload = get_cart_payload(
            request.user,
        )

        items = payload["items"]

        subtotal = payload["subtotal"]

        item_count = payload["item_count"]

        can_checkout = payload["can_checkout"]

        gross_subtotal = payload["gross_subtotal"]

        offer_discount_total = payload["offer_discount_total"]

        resolver = payload["offer_resolver"]

        serializer = CartItemSerializer(
            items,
            many=True,
            context={
                "request": request,
                "offer_resolver": resolver,
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

                "subtotal_gross": str(
                    gross_subtotal.quantize(
                        Decimal("0.01"),
                    )
                ),

                "offer_discount_total": str(
                    offer_discount_total.quantize(
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

        payload = get_cart_payload(
            request.user,
        )

        items = payload["items"]

        subtotal = payload["subtotal"]

        item_count = payload["item_count"]

        can_checkout = payload["can_checkout"]

        gross_subtotal = payload["gross_subtotal"]

        offer_discount_total = payload["offer_discount_total"]

        resolver = payload["offer_resolver"]

        return Response(
            {
                "item": serializer.data,

                "items": CartItemSerializer(
                    items,
                    many=True,
                    context={
                        "request": request,
                        "offer_resolver": resolver,
                    },
                ).data,

                "item_count": item_count,

                "subtotal": str(
                    subtotal.quantize(
                        Decimal("0.01"),
                    )
                ),

                "subtotal_gross": str(
                    gross_subtotal.quantize(
                        Decimal("0.01"),
                    )
                ),

                "offer_discount_total": str(
                    offer_discount_total.quantize(
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

        payload = get_cart_payload(
            request.user,
        )

        items = payload["items"]

        subtotal = payload["subtotal"]

        item_count = payload["item_count"]

        can_checkout = payload["can_checkout"]

        gross_subtotal = payload["gross_subtotal"]

        offer_discount_total = payload["offer_discount_total"]

        resolver = payload["offer_resolver"]

        return Response(
            {
                "items": CartItemSerializer(
                    items,
                    many=True,
                    context={
                        "request": request,
                        "offer_resolver": resolver,
                    },
                ).data,

                "item_count": item_count,

                "subtotal": str(
                    subtotal.quantize(
                        Decimal("0.01"),
                    )
                ),

                "subtotal_gross": str(
                    gross_subtotal.quantize(
                        Decimal("0.01"),
                    )
                ),

                "offer_discount_total": str(
                    offer_discount_total.quantize(
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


class CartCheckoutPreviewView(APIView):

    permission_classes = [IsAuthenticated]

    def get(
        self,
        request,
    ):

        body = build_checkout_preview(
            request.user,
        )

        return Response(
            body,
        )


class CartAvailableCouponsView(APIView):

    permission_classes = [IsAuthenticated]

    def get(
        self,
        request,
    ):

        payload = get_available_coupons_payload(
            request.user,
        )

        return Response(
            payload,
        )


class CartCouponView(APIView):

    permission_classes = [IsAuthenticated]

    def post(
        self,
        request,
    ):

        code = request.data.get(
            "code",
        )

        try:

            apply_coupon_to_cart(
                request.user,
                code,
            )

        except DRFValidationError as exc:

            return Response(
                exc.detail,
                status=status.HTTP_400_BAD_REQUEST,
            )

        preview = build_checkout_preview(
            request.user,
        )

        return Response(
            {
                "message": "Coupon applied.",
                "preview": preview,
            },
            status=status.HTTP_200_OK,
        )

    def delete(
        self,
        request,
    ):

        try:

            remove_coupon_from_cart(
                request.user,
            )

        except DRFValidationError as exc:

            return Response(
                exc.detail,
                status=status.HTTP_400_BAD_REQUEST,
            )

        preview = build_checkout_preview(
            request.user,
        )

        return Response(
            {
                "message": "Coupon removed.",
                "preview": preview,
            },
            status=status.HTTP_200_OK,
        )
