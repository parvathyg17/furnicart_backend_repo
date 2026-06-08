from decimal import Decimal

from rest_framework import serializers

from catalog.serializers.product_serializers import (
    ProductVariantSerializer,
)

from cart.models import CartItem

from .services import (
    MAX_CART_QTY,
    cart_line_subtotal,
    get_cart_line_availability,
)


class CartItemSerializer(
    serializers.ModelSerializer,
):

    variant = ProductVariantSerializer(
        read_only=True,
    )

    product_name = serializers.CharField(
        source="variant.product.name",
        read_only=True,
    )

    product_id = serializers.IntegerField(
        source="variant.product_id",
        read_only=True,
    )

    product_slug = serializers.CharField(
        source="variant.product.slug",
        read_only=True,
    )

    line_subtotal = serializers.SerializerMethodField()

    max_quantity = serializers.SerializerMethodField()

    line_availability = serializers.SerializerMethodField()

    class Meta:

        model = CartItem

        fields = [
            "id",
            "product_id",
            "product_slug",
            "product_name",
            "variant",
            "quantity",
            "line_subtotal",
            "max_quantity",
            "line_availability",
            "created_at",
        ]

        read_only_fields = [
            "id",
            "product_id",
            "product_slug",
            "product_name",
            "variant",
            "line_subtotal",
            "max_quantity",
            "line_availability",
            "created_at",
        ]

    def get_line_subtotal(
        self,
        obj,
    ):

        return str(
            cart_line_subtotal(obj).quantize(
                Decimal("0.01"),
            )
        )

    def get_max_quantity(
        self,
        obj,
    ):

        return min(
            obj.variant.stock,
            MAX_CART_QTY,
        )

    def get_line_availability(
        self,
        obj,
    ):

        return get_cart_line_availability(obj)


class CartItemQuantitySerializer(
    serializers.Serializer,
):

    quantity = serializers.IntegerField(
        min_value=1,
    )
