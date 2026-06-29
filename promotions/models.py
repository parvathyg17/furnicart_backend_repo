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
        help_text=(
            "Minimum order total (subtotal + tax + shipping, before coupon) "
            "required for this coupon to apply."
        ),
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

    assigned_user = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="assigned_coupons",
        help_text=(
            "When set, only this user may redeem the coupon "
            "(e.g. referral welcome offers)."
        ),
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


class ReferralProgram(models.Model):

    name = models.CharField(
        max_length=128,
        default="Default Referral Program",
    )

    is_active = models.BooleanField(
        default=True,
        db_index=True,
    )

    referee_discount_type = models.CharField(
        max_length=16,
        choices=Coupon.DiscountType.choices,
        default=Coupon.DiscountType.PERCENT,
    )

    referee_discount_value = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("10.00"),
        help_text="Referee welcome coupon: percent (0–100) or fixed amount.",
    )

    referee_max_discount_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Cap for percentage referee coupons (optional).",
    )

    referee_coupon_valid_days = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Days the referee coupon stays valid (empty = no expiry).",
    )

    referrer_reward_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("500.00"),
        help_text="Wallet credit for referrer after referee's first paid order.",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:

        ordering = ["-created_at"]
        verbose_name = "Referral program"
        verbose_name_plural = "Referral programs"

    def __str__(self):

        return self.name


class ReferralCode(models.Model):

    user = models.OneToOneField(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="referral_code",
    )

    code = models.CharField(
        max_length=32,
        unique=True,
        db_index=True,
        help_text="Shareable referral code (stored uppercase).",
    )

    token = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
        help_text="Token for referral links (?ref=token).",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:

        verbose_name = "Referral code"
        verbose_name_plural = "Referral codes"

    def __str__(self):

        return f"{self.code} ({self.user_id})"

    def save(self, *args, **kwargs):

        if self.code:

            self.code = self.code.strip().upper()

        super().save(*args, **kwargs)


class ReferralAttribution(models.Model):

    referee = models.OneToOneField(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="referral_attribution",
    )

    referrer = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="referrals_made",
    )

    referral_code = models.ForeignKey(
        ReferralCode,
        on_delete=models.PROTECT,
        related_name="attributions",
    )

    referee_coupon = models.OneToOneField(
        Coupon,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="referral_attribution",
    )

    referrer_rewarded = models.BooleanField(
        default=False,
    )

    referrer_reward_order = models.ForeignKey(
        "orders.Order",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="referral_rewards",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:

        verbose_name = "Referral attribution"
        verbose_name_plural = "Referral attributions"

    def __str__(self):

        return f"{self.referee_id} referred by {self.referrer_id}"
