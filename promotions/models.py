from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q


class Coupon(models.Model):

    class DiscountType(models.TextChoices):

        PERCENT = "percent", "Percentage"
        FIXED = "fixed", "Fixed amount"

    code = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
        help_text="Customer-facing code (stored uppercase).",
    )

    description = models.CharField(
        max_length=255,
        blank=True,
        default="",
    )

    discount_type = models.CharField(
        max_length=16,
        choices=DiscountType.choices,
        default=DiscountType.PERCENT,
    )

    discount_value = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text=(
            "If percentage: 0–100. If fixed: amount in shop currency."
        ),
    )

    min_order_subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Minimum cart subtotal before tax/shipping for this coupon to apply.",
    )

    max_discount_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="For percentage coupons: cap the discount (optional).",
    )

    valid_from = models.DateTimeField(
        null=True,
        blank=True,
        help_text="If empty, valid immediately once active.",
    )

    valid_until = models.DateTimeField(
        null=True,
        blank=True,
        help_text="If empty, no end date.",
    )

    max_redemptions_total = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Global usage cap across all users (empty = unlimited).",
    )

    max_redemptions_per_user = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Per-user cap (empty = unlimited). Enforced at checkout.",
    )

    times_used = models.PositiveIntegerField(
        default=0,
        help_text="Incremented when an order completes with this coupon (user flow).",
    )

    is_active = models.BooleanField(
        default=True,
        db_index=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:

        ordering = ["-created_at"]
        verbose_name = "Coupon"
        verbose_name_plural = "Coupons"

    def __str__(self):

        return self.code

    def clean(self):

        super().clean()

        if self.valid_from and self.valid_until:

            if self.valid_until <= self.valid_from:

                raise ValidationError(
                    {
                        "valid_until": "Must be after valid_from.",
                    },
                )

        if self.discount_type == self.DiscountType.PERCENT:

            if self.discount_value <= Decimal("0") or self.discount_value > Decimal("100"):

                raise ValidationError(
                    {
                        "discount_value": (
                            "Percentage must be greater than 0 and at most 100."
                        ),
                    },
                )

        elif self.discount_type == self.DiscountType.FIXED:

            if self.discount_value <= Decimal("0"):

                raise ValidationError(
                    {
                        "discount_value": "Fixed discount must be greater than 0.",
                    },
                )

    def save(self, *args, **kwargs):

        if self.code:

            self.code = self.code.strip().upper()

        super().save(*args, **kwargs)


class Offer(models.Model):

    class OfferType(models.TextChoices):

        PRODUCT = "product", "Product"
        CATEGORY = "category", "Category"

    class DiscountType(models.TextChoices):

        PERCENT = "percent", "Percentage"
        FIXED = "fixed", "Fixed amount"

    title = models.CharField(
        max_length=255,
    )

    description = models.CharField(
        max_length=255,
        blank=True,
        default="",
    )

    offer_type = models.CharField(
        max_length=16,
        choices=OfferType.choices,
        db_index=True,
    )

    product = models.ForeignKey(
        "catalog.Product",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="offers",
    )

    category = models.ForeignKey(
        "catalog.Category",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="offers",
    )

    discount_type = models.CharField(
        max_length=16,
        choices=DiscountType.choices,
        default=DiscountType.PERCENT,
    )

    discount_value = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text=(
            "If percentage: 0–100. If fixed: amount off the line subtotal."
        ),
    )

    max_discount_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="For percentage offers: cap the discount (optional).",
    )

    valid_from = models.DateTimeField(
        null=True,
        blank=True,
        help_text="If empty, valid immediately once active.",
    )

    valid_until = models.DateTimeField(
        null=True,
        blank=True,
        help_text="If empty, no end date.",
    )

    is_active = models.BooleanField(
        default=True,
        db_index=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:

        ordering = ["-created_at"]
        verbose_name = "Offer"
        verbose_name_plural = "Offers"
        constraints = [
            models.CheckConstraint(
                condition=(
                    Q(
                        offer_type="product",
                        product__isnull=False,
                        category__isnull=True,
                    )
                    | Q(
                        offer_type="category",
                        category__isnull=False,
                        product__isnull=True,
                    )
                ),
                name="offer_type_target_consistency",
            ),
        ]

    def __str__(self):

        return self.title

    def clean(self):

        super().clean()

        if self.offer_type == self.OfferType.PRODUCT:

            if self.product_id is None:

                raise ValidationError(
                    {
                        "product": "Product is required for product offers.",
                    },
                )

            if self.category_id is not None:

                raise ValidationError(
                    {
                        "category": "Category must be empty for product offers.",
                    },
                )

        elif self.offer_type == self.OfferType.CATEGORY:

            if self.category_id is None:

                raise ValidationError(
                    {
                        "category": "Category is required for category offers.",
                    },
                )

            if self.product_id is not None:

                raise ValidationError(
                    {
                        "product": "Product must be empty for category offers.",
                    },
                )

        if self.valid_from and self.valid_until:

            if self.valid_until <= self.valid_from:

                raise ValidationError(
                    {
                        "valid_until": "Must be after valid_from.",
                    },
                )

        if self.discount_type == self.DiscountType.PERCENT:

            if (
                self.discount_value <= Decimal("0")
                or self.discount_value > Decimal("100")
            ):

                raise ValidationError(
                    {
                        "discount_value": (
                            "Percentage must be greater than 0 and at most 100."
                        ),
                    },
                )

        elif self.discount_type == self.DiscountType.FIXED:

            if self.discount_value <= Decimal("0"):

                raise ValidationError(
                    {
                        "discount_value": "Fixed discount must be greater than 0.",
                    },
                )

    def save(self, *args, **kwargs):

        super().save(*args, **kwargs)
