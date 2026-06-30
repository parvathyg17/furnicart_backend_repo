from rest_framework import serializers

from orders.models import Order, OrderLine, ReturnRequest
from orders.services.checkout_pricing import (
    order_subtotal_gross,
    sum_order_line_offer_discount,
)


class OrderOfferPricingMixin(
    object,
):

    def get_offer_discount_total(
        self,
        obj,
    ):

        return sum_order_line_offer_discount(
            obj,
        )

    def get_subtotal_gross(
        self,
        obj,
    ):

        return order_subtotal_gross(
            obj,
        )


class ReturnRequestSerializer(
    serializers.ModelSerializer,
):

    class Meta:

        model = ReturnRequest

        fields = [
            "id",
            "status",
            "reason",
            "admin_note",
            "created_at",
            "resolved_at",
        ]


class OrderLineReturnSummaryMixin(
    object,
):

    def get_open_return(
        self,
        obj,
    ):

        req = (
            ReturnRequest.objects.filter(
                order_line=obj,
                status__in=(
                    ReturnRequest.Status.PENDING,
                    ReturnRequest.Status.APPROVED,
                ),
            )
            .order_by(
                "-created_at",
            )
            .first()
        )

        if req is None:

            return None

        return ReturnRequestSerializer(
            req,
        ).data

    def get_has_return_request(
        self,
        obj,
    ):

        return ReturnRequest.objects.filter(
            order_line=obj,
        ).exists()

    def get_last_return(
        self,
        obj,
    ):

        req = (
            ReturnRequest.objects.filter(
                order_line=obj,
                status=ReturnRequest.Status.REJECTED,
            )
            .order_by(
                "-created_at",
            )
            .first()
        )

        if req is None:

            return None

        return ReturnRequestSerializer(
            req,
        ).data


class OrderLineSerializer(
    OrderLineReturnSummaryMixin,
    serializers.ModelSerializer,
):

    variant_id = serializers.IntegerField(
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

    open_return = serializers.SerializerMethodField()

    has_return_request = serializers.SerializerMethodField()

    last_return = serializers.SerializerMethodField()

    class Meta:

        model = OrderLine

        fields = [
            "id",
            "variant_id",
            "product_id",
            "product_slug",
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
            "fulfillment_status",
            "cancellation_reason",
            "open_return",
            "has_return_request",
            "last_return",
        ]


class OrderLineCardSerializer(
    OrderLineReturnSummaryMixin,
    serializers.ModelSerializer,
):

    variant_id = serializers.IntegerField(
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

    open_return = serializers.SerializerMethodField()

    has_return_request = serializers.SerializerMethodField()

    last_return = serializers.SerializerMethodField()

    class Meta:

        model = OrderLine

        fields = [
            "id",
            "variant_id",
            "product_id",
            "product_slug",
            "product_name",
            "variant_name",
            "image_url",
            "quantity",
            "unit_price",
            "line_total",
            "status",
            "fulfillment_status",
            "cancellation_reason",
            "open_return",
            "has_return_request",
            "last_return",
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
            "wallet",
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


class ReturnCreateSerializer(
    serializers.Serializer,
):

    reason = serializers.CharField(
        required=True,
        allow_blank=False,
        max_length=2000,
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
    OrderOfferPricingMixin,
    serializers.ModelSerializer,
):

    lines = OrderLineSerializer(
        many=True,
        read_only=True,
    )

    offer_discount_total = serializers.SerializerMethodField()

    subtotal_gross = serializers.SerializerMethodField()

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
            "subtotal_gross",
            "offer_discount_total",
            "subtotal",
            "tax_total",
            "discount_total",
            "coupon_code",
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


class PurchaseLineSerializer(
    OrderLineReturnSummaryMixin,
    serializers.ModelSerializer,
):

    order_number = serializers.CharField(
        source="order.order_number",
        read_only=True,
    )

    order_id = serializers.IntegerField(
        read_only=True,
    )

    order_status = serializers.CharField(
        source="order.status",
        read_only=True,
    )

    placed_at = serializers.DateTimeField(
        source="order.placed_at",
        read_only=True,
    )

    variant_id = serializers.IntegerField(
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

    open_return = serializers.SerializerMethodField()

    has_return_request = serializers.SerializerMethodField()

    last_return = serializers.SerializerMethodField()

    class Meta:

        model = OrderLine

        fields = [
            "id",
            "order_id",
            "order_number",
            "order_status",
            "placed_at",
            "variant_id",
            "product_id",
            "product_slug",
            "product_name",
            "variant_name",
            "sku",
            "unit_price",
            "quantity",
            "line_total",
            "image_url",
            "status",
            "fulfillment_status",
            "cancellation_reason",
            "open_return",
            "has_return_request",
            "last_return",
        ]


class AdminOrderLineSerializer(
    serializers.ModelSerializer,
):

    variant_id = serializers.IntegerField(
        read_only=True,
    )

    product_id = serializers.IntegerField(
        source="variant.product_id",
        read_only=True,
    )

    class Meta:

        model = OrderLine

        fields = [
            "id",
            "variant_id",
            "product_id",
            "product_name",
            "variant_name",
            "sku",
            "unit_price",
            "quantity",
            "line_total",
            "image_url",
            "status",
            "fulfillment_status",
            "cancellation_reason",
        ]


class AdminOrderListSerializer(
    serializers.ModelSerializer,
):

    line_count = serializers.IntegerField(
        read_only=True,
    )

    user_email = serializers.EmailField(
        source="user.email",
        read_only=True,
    )

    user_id = serializers.IntegerField(
        read_only=True,
    )

    line_items = serializers.SerializerMethodField()

    class Meta:

        model = Order

        fields = [
            "id",
            "order_number",
            "status",
            "placed_at",
            "grand_total",
            "line_count",
            "user_id",
            "user_email",
            "line_items",
        ]

    def get_line_items(
        self,
        obj,
    ):

        rows = []

        for line in obj.lines.all()[
            :20
        ]:

            rows.append(
                {
                    "product_name": line.product_name,
                    "variant_name": line.variant_name,
                    "sku": line.sku,
                    "quantity": line.quantity,
                    "variant_id": line.variant_id,
                    "image_url": line.image_url,
                },
            )

        return rows


class AdminOrderDetailSerializer(
    OrderOfferPricingMixin,
    serializers.ModelSerializer,
):

    lines = AdminOrderLineSerializer(
        many=True,
        read_only=True,
    )

    user_email = serializers.EmailField(
        source="user.email",
        read_only=True,
    )

    user_id = serializers.IntegerField(
        read_only=True,
    )

    offer_discount_total = serializers.SerializerMethodField()

    subtotal_gross = serializers.SerializerMethodField()

    class Meta:

        model = Order

        fields = [
            "id",
            "user_id",
            "user_email",
            "order_number",
            "status",
            "payment_method",
            "payment_status",
            "subtotal_gross",
            "offer_discount_total",
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


class AdminFulfillmentUpdateSerializer(
    serializers.Serializer,
):

    fulfillment_status = serializers.ChoiceField(
        choices=[
            c
            for c, _ in OrderLine.FulfillmentStatus.choices
            if c != OrderLine.FulfillmentStatus.RETURNED
        ],
    )


class AdminReturnStatusSerializer(
    serializers.Serializer,
):

    status = serializers.ChoiceField(
        choices=[
            ReturnRequest.Status.APPROVED,
            ReturnRequest.Status.REJECTED,
            ReturnRequest.Status.COMPLETED,
        ],
    )

    admin_note = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=2000,
        default="",
    )


class AdminReturnListSerializer(
    serializers.ModelSerializer,
):

    order_number = serializers.CharField(
        source="order_line.order.order_number",
        read_only=True,
    )

    line_id = serializers.IntegerField(
        source="order_line_id",
        read_only=True,
    )

    product_name = serializers.CharField(
        source="order_line.product_name",
        read_only=True,
    )

    variant_name = serializers.CharField(
        source="order_line.variant_name",
        read_only=True,
    )

    sku = serializers.CharField(
        source="order_line.sku",
        read_only=True,
    )

    image_url = serializers.CharField(
        source="order_line.image_url",
        read_only=True,
    )

    user_email = serializers.EmailField(
        source="user.email",
        read_only=True,
    )

    class Meta:

        model = ReturnRequest

        fields = [
            "id",
            "status",
            "reason",
            "admin_note",
            "created_at",
            "resolved_at",
            "order_number",
            "line_id",
            "product_name",
            "variant_name",
            "sku",
            "image_url",
            "user_email",
        ]


class RazorpayInitiateSerializer(
    serializers.Serializer,
):

    address_id = serializers.IntegerField(
        min_value=1,
    )


class RazorpayVerifySerializer(
    serializers.Serializer,
):

    razorpay_order_id = serializers.CharField(
        max_length=255,
    )

    razorpay_payment_id = serializers.CharField(
        max_length=255,
    )

    razorpay_signature = serializers.CharField(
        max_length=512,
    )
