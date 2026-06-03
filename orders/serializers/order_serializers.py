from decimal import Decimal

from rest_framework import serializers

from orders.models import Order, OrderLine


class OrderLineSerializer(
    serializers.ModelSerializer,
):

    class Meta:

        model = OrderLine

        fields = [
            "id",
            "product_name",
            "variant_name",
            "sku",
            "unit_price",
            "quantity",
            "tax_amount",
            "discount_amount",
            "line_total",
            "image_url",
            "status",
        ]


class OrderCreateSerializer(
    serializers.Serializer,
):

    address_id = serializers.IntegerField(
        min_value=1,
    )

    tax_total = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        required=False,
        default=Decimal("0.00"),
    )

    discount_total = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        required=False,
        default=Decimal("0.00"),
    )

    shipping_total = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        required=False,
        default=Decimal("0.00"),
    )


class OrderDetailSerializer(
    serializers.ModelSerializer,
):

    lines = OrderLineSerializer(
        many=True,
        read_only=True,
    )

    class Meta:

        model = Order

        fields = [
            "id",
            "order_number",
            "status",
            "payment_method",
            "payment_status",
            "payment_provider",
            "gateway_order_id",
            "gateway_payment_id",
            "payment_metadata",
            "paid_at",
            "subtotal",
            "tax_total",
            "discount_total",
            "shipping_total",
            "grand_total",
            "shipping_name",
            "shipping_phone",
            "shipping_address_line",
            "shipping_city",
            "shipping_state",
            "shipping_pincode",
            "placed_at",
            "lines",
        ]
