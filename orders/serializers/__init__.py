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
            "cancellation_reason",
        ]


class OrderLineCardSerializer(
    serializers.ModelSerializer,
):

    class Meta:

        model = OrderLine

        fields = [
            "id",
            "product_name",
            "variant_name",
            "image_url",
            "quantity",
            "unit_price",
            "line_total",
            "status",
            "cancellation_reason",
        ]


class OrderCreateSerializer(
    serializers.Serializer,
):

    address_id = serializers.IntegerField(
        min_value=1,
    )

    payment_method = serializers.ChoiceField(
        choices=[
            "cod",
        ],
        default="cod",
    )


class OrderCancelRequestSerializer(
    serializers.Serializer,
):

    reason = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=500,
        default="",
    )


class OrderListSerializer(
    serializers.ModelSerializer,
):

    line_count = serializers.IntegerField(
        read_only=True,
    )

    lines = OrderLineCardSerializer(
        many=True,
        read_only=True,
    )

    class Meta:

        model = Order

        fields = [
            "id",
            "order_number",
            "status",
            "placed_at",
            "grand_total",
            "line_count",
            "lines",
        ]


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
            "cancelled_at",
            "cancellation_reason",
            "lines",
        ]
