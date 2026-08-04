from rest_framework import serializers

from orders.models import Order, OrderLine, ReturnRequest
from orders.services.checkout_pricing import (order_subtotal_gross,
                                              sum_order_line_offer_discount)


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

    def get_refunded_total(
        self,
        obj,
    ):

        from orders.services.order_wallet_services import \
            total_refunded_for_order

        return total_refunded_for_order(
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
            "quantity",
            "admin_note",
            "created_at",
            "resolved_at",
        ]


class OrderLineQuantityMixin(
    serializers.Serializer,
):

    active_quantity = serializers.SerializerMethodField()

    cancellable_quantity = serializers.SerializerMethodField()

    returnable_quantity = serializers.SerializerMethodField()

    def get_active_quantity(
        self,
        obj,
    ):

        from orders.services.order_services import active_quantity

        return active_quantity(
            obj,
        )

    def get_cancellable_quantity(
        self,
        obj,
    ):

        from orders.services.order_services import cancellable_quantity

        return cancellable_quantity(
            obj,
        )

    def get_returnable_quantity(
        self,
        obj,
    ):

        from orders.services.order_services import returnable_quantity

        return returnable_quantity(
            obj,
        )


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
    OrderLineQuantityMixin,
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
            "cancelled_quantity",
            "returned_quantity",
            "active_quantity",
            "cancellable_quantity",
            "returnable_quantity",
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
    OrderLineQuantityMixin,
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
            "cancelled_quantity",
            "returned_quantity",
            "active_quantity",
            "cancellable_quantity",
            "returnable_quantity",
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

    quantity = serializers.IntegerField(
        required=False,
        min_value=1,
    )


class ReturnCreateSerializer(
    serializers.Serializer,
):

    reason = serializers.CharField(
        required=True,
        allow_blank=False,
        max_length=2000,
    )

    quantity = serializers.IntegerField(
        required=False,
        min_value=1,
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

    refunded_total = serializers.SerializerMethodField()

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
            "refunded_total",
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

    def to_representation(
        self,
        instance,
    ):

        data = super().to_representation(
            instance,
        )

        from orders.services.refund_reporting import order_refund_report

        report = order_refund_report(
            instance,
        )

        line_financials = report["lines"]

        for line in data.get(
            "lines",
            [],
        ):

            fin = line_financials.get(
                line["id"],
                {},
            )

            line["coupon_share"] = fin.get(
                "coupon_share",
                "0.00",
            )

            line["tax_share"] = fin.get(
                "tax_share",
                "0.00",
            )

            line["refund_amount"] = fin.get(
                "refund_amount",
            )

        data["original_paid"] = report["original_paid"]

        data["remaining_value"] = report["remaining_value"]

        data["refunded_total"] = report["total_refunded"]

        data["cancel_refund_total"] = report["cancel_refund_total"]

        data["return_refund_total"] = report["return_refund_total"]

        data["refund_transactions"] = report["refund_transactions"]

        from orders.services.refund_reporting import _gst_rate

        data["gst_rate"] = str(_gst_rate())

        return data


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
    OrderLineQuantityMixin,
    serializers.ModelSerializer,
):

    variant_id = serializers.IntegerField(
        read_only=True,
    )

    product_id = serializers.IntegerField(
        source="variant.product_id",
        read_only=True,
    )

    active_quantity = serializers.SerializerMethodField()

    cancellable_quantity = serializers.SerializerMethodField()

    returnable_quantity = serializers.SerializerMethodField()

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
            "cancelled_quantity",
            "returned_quantity",
            "active_quantity",
            "cancellable_quantity",
            "returnable_quantity",
            "discount_amount",
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
            "original_paid",
            "remaining_value",
            "refunded_total",
            "line_count",
            "user_id",
            "user_email",
            "line_items",
        ]

    original_paid = serializers.SerializerMethodField()

    remaining_value = serializers.SerializerMethodField()

    refunded_total = serializers.SerializerMethodField()

    def get_original_paid(
        self,
        obj,
    ):

        return self._refund_report(
            obj,
        )["original_paid"]

    def get_remaining_value(
        self,
        obj,
    ):

        return self._refund_report(
            obj,
        )["remaining_value"]

    def get_refunded_total(
        self,
        obj,
    ):

        return self._refund_report(
            obj,
        )["total_refunded"]

    def _refund_report(
        self,
        obj,
    ):

        cache = self.context.setdefault(
            "_admin_list_refund_reports",
            {},
        )

        if obj.pk not in cache:

            from orders.services.refund_reporting import order_refund_report

            cache[obj.pk] = order_refund_report(
                obj,
            )

        return cache[obj.pk]

    def get_line_items(
        self,
        obj,
    ):

        rows = []

        for line in obj.lines.all()[:20]:

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

    refunded_total = serializers.SerializerMethodField()

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
            "coupon_code",
            "shipping_total",
            "grand_total",
            "refunded_total",
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

    def to_representation(
        self,
        instance,
    ):

        data = super().to_representation(
            instance,
        )

        from orders.services.refund_reporting import order_refund_report

        report = order_refund_report(
            instance,
        )

        line_financials = report["lines"]

        for line in data.get(
            "lines",
            [],
        ):

            fin = line_financials.get(
                line["id"],
                {},
            )

            line["coupon_share"] = fin.get(
                "coupon_share",
                "0.00",
            )

            line["tax_share"] = fin.get(
                "tax_share",
                "0.00",
            )

            line["refund_amount"] = fin.get(
                "refund_amount",
            )

        data["original_paid"] = report["original_paid"]

        data["remaining_value"] = report["remaining_value"]

        data["refunded_total"] = report["total_refunded"]

        data["cancel_refund_total"] = report["cancel_refund_total"]

        data["return_refund_total"] = report["return_refund_total"]

        data["refund_transactions"] = report["refund_transactions"]

        from orders.services.refund_reporting import _gst_rate

        data["gst_rate"] = str(_gst_rate())

        return data


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
            "quantity",
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
