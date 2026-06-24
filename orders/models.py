from decimal import Decimal

from django.conf import settings
from django.db import models

from accounts.models.address import Address
from catalog.models import ProductVariant


class DailyOrderCounter(models.Model):

    

    date = models.DateField(
        primary_key=True,
    )

    last_number = models.PositiveIntegerField(
        default=0,
    )


class Order(models.Model):

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        SHIPPED = "shipped", "Shipped"
        OUT_FOR_DELIVERY = "out_for_delivery", "Out for delivery"
        DELIVERED = "delivered", "Delivered"
        CANCELLED = "cancelled", "Cancelled"
        PARTIALLY_CANCELLED = "partially_cancelled", "Partially cancelled"
        PARTIALLY_SHIPPED = "partially_shipped", "Partially shipped"
        PARTIALLY_DELIVERED = "partially_delivered", "Partially delivered"

    class PaymentMethod(models.TextChoices):
       

        COD = "cod", "Cash on delivery"
        RAZORPAY = "razorpay", "Razorpay"
        WALLET = "wallet", "Wallet"
        OTHER = "other", "Other / custom"

    class PaymentStatus(models.TextChoices):
       

        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        PAID = "paid", "Paid"
        FAILED = "failed", "Failed"
        REFUNDED = "refunded", "Refunded"
        PARTIALLY_REFUNDED = "partially_refunded", "Partially refunded"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="orders",
    )

    order_number = models.CharField(
        max_length=32,
        unique=True,
        db_index=True,
    )

    status = models.CharField(
        max_length=32,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )

    payment_method = models.CharField(
        max_length=32,
        choices=PaymentMethod.choices,
        default=PaymentMethod.COD,
        db_index=True,
    )

    payment_status = models.CharField(
        max_length=32,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
        db_index=True,
    )

    payment_provider = models.CharField(
        max_length=64,
        blank=True,
        default="",
        help_text=(
            "Gateway or processor id, e.g. ``razorpay``. "
            "Optional when ``payment_method`` is self-explanatory."
        ),
    )

    gateway_order_id = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Provider order/session id (e.g. Razorpay order_id).",
    )

    gateway_payment_id = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Provider payment/charge id after authorization or capture.",
    )

    payment_metadata = models.JSONField(
        null=True,
        blank=True,
        help_text="Raw or extra gateway/wallet payload, split-payment breakdown, etc.",
    )

    paid_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the payment was confirmed (online) or recorded as settled.",
    )

    subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    tax_total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    discount_total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    applied_coupon = models.ForeignKey(
        "promotions.Coupon",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
    )

    coupon_code = models.CharField(
        max_length=64,
        blank=True,
        default="",
        help_text="Snapshot of coupon code at checkout time.",
    )

    shipping_total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    grand_total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    shipping_address = models.ForeignKey(
        Address,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders_shipped_to",
    )

    shipping_name = models.CharField(
        max_length=100,
    )

    shipping_phone = models.CharField(
        max_length=15,
    )

    shipping_address_line = models.TextField()

    shipping_city = models.CharField(
        max_length=100,
    )

    shipping_state = models.CharField(
        max_length=100,
    )

    shipping_pincode = models.CharField(
        max_length=10,
    )

    placed_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
    )

    cancelled_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    cancellation_reason = models.TextField(
        blank=True,
        default="",
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:

        ordering = ["-placed_at"]

    def __str__(self):

        return self.order_number


class OrderLine(models.Model):

    class LineStatus(models.TextChoices):
        ACTIVE = "active", "Active"
        CANCELLED = "cancelled", "Cancelled"

    class FulfillmentStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        SHIPPED = "shipped", "Shipped"
        OUT_FOR_DELIVERY = "out_for_delivery", "Out for delivery"
        DELIVERED = "delivered", "Delivered"
        RETURNED = "returned", "Returned"

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="lines",
    )

    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.PROTECT,
        related_name="order_lines",
    )

    product_name = models.CharField(
        max_length=255,
    )

    variant_name = models.CharField(
        max_length=255,
    )

    sku = models.CharField(
        max_length=100,
    )

    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )

    quantity = models.PositiveIntegerField()

    tax_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    line_total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    image_url = models.CharField(
        max_length=512,
        blank=True,
        default="",
    )

    status = models.CharField(
        max_length=16,
        choices=LineStatus.choices,
        default=LineStatus.ACTIVE,
    )

    fulfillment_status = models.CharField(
        max_length=32,
        choices=FulfillmentStatus.choices,
        default=FulfillmentStatus.PENDING,
        db_index=True,
    )

    cancellation_reason = models.TextField(
        blank=True,
        default="",
    )

    class Meta:

        ordering = ["id"]

    def __str__(self):

        return f"{self.order.order_number} — {self.sku} x{self.quantity}"


class ReturnRequest(models.Model):

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        COMPLETED = "completed", "Completed"

    order_line = models.ForeignKey(
        OrderLine,
        on_delete=models.CASCADE,
        related_name="return_requests",
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="return_requests",
    )

    reason = models.TextField()

    admin_note = models.TextField(
        blank=True,
        default="",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
    )

    resolved_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    class Meta:

        ordering = ["-created_at"]

    def __str__(self):

        return f"Return {self.pk} — {self.order_line_id} ({self.status})"


class PaymentIntent(models.Model):

    class Status(models.TextChoices):

        PENDING = "pending", "Pending"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"
        EXPIRED = "expired", "Expired"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="payment_intents",
    )

    shipping_address = models.ForeignKey(
        Address,
        on_delete=models.PROTECT,
        related_name="payment_intents",
    )

    razorpay_order_id = models.CharField(
        max_length=255,
        unique=True,
        db_index=True,
    )

    amount_paise = models.PositiveIntegerField()

    grand_total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    applied_coupon_id = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )

    order = models.ForeignKey(
        Order,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="payment_intents",
    )

    gateway_payment_id = models.CharField(
        max_length=255,
        blank=True,
        default="",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
    )

    expires_at = models.DateTimeField(
        db_index=True,
    )

    class Meta:

        ordering = ["-created_at"]

    def __str__(self):

        return f"PaymentIntent {self.pk} ({self.status})"
