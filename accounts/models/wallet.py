from decimal import Decimal

from django.conf import settings
from django.db import models


class Wallet(models.Model):

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="wallet",
    )

    balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:

        ordering = ["-updated_at"]

    def __str__(self):

        return f"Wallet({self.user_id}) ₹{self.balance}"


class WalletTransaction(models.Model):

    class Type(models.TextChoices):

        CREDIT = "credit", "Credit"
        DEBIT = "debit", "Debit"

    class Reason(models.TextChoices):

        ORDER_CANCEL = "order_cancel", "Order cancellation"
        RETURN_REFUND = "return_refund", "Return refund"
        ORDER_PAYMENT = "order_payment", "Order payment"
        REFERRAL_REWARD = "referral_reward", "Referral reward"
        ADMIN_ADJUSTMENT = "admin_adjustment", "Admin adjustment"
        OTHER = "other", "Other"

    wallet = models.ForeignKey(
        Wallet,
        on_delete=models.CASCADE,
        related_name="transactions",
    )

    type = models.CharField(
        max_length=16,
        choices=Type.choices,
        db_index=True,
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    reason = models.CharField(
        max_length=32,
        choices=Reason.choices,
        default=Reason.OTHER,
        db_index=True,
    )

    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="wallet_transactions",
    )

    return_request = models.ForeignKey(
        "orders.ReturnRequest",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="wallet_transactions",
    )

    reference_note = models.CharField(
        max_length=255,
        blank=True,
        default="",
    )

    balance_after = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Wallet balance immediately after this transaction.",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
    )

    class Meta:

        ordering = ["-created_at"]

    def __str__(self):

        sign = "+" if self.type == self.Type.CREDIT else "−"

        return f"{sign}₹{self.amount} ({self.reason})"
