from django.conf import settings
from django.db import models

from catalog.models import ProductVariant


class Cart(models.Model):

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="cart",
    )

    applied_coupon = models.ForeignKey(
        "promotions.Coupon",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="carts",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )


class CartItem(models.Model):

    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name="items",
    )

    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.CASCADE,
    )

    quantity = models.PositiveIntegerField(
        default=1,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:

        constraints = [
            models.UniqueConstraint(
                fields=["cart", "variant"],
                name="cart_unique_variant",
            ),
        ]
