from django.db import models
from django.db.models import Q

from catalog.models.product import Product
from catalog.product_activation import (
    sync_product_active_if_no_sellable_variants,
)

class ProductVariant(models.Model):

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="variants"
    )

    variant_name = models.CharField(
        max_length=255
    )

    color = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    size = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    material = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    stock = models.PositiveIntegerField(
        default=0
    )

    sku = models.CharField(
        max_length=100,
        unique=True
    )

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:

        ordering = ["-created_at"]

        indexes = [
            models.Index(fields=["sku"]),
            models.Index(fields=["is_active"]),
        ]

        constraints = [

            models.CheckConstraint(
                condition=Q(price__gt=0),
                name="variant_price_gt_0"
            ),

            models.CheckConstraint(
                condition=Q(stock__gte=0),
                name="variant_stock_gte_0"
            ),
        ]

    def __str__(self):

        return f"{self.product.name} - {self.variant_name}"

    def save(
        self,
        *args,
        **kwargs,
    ):

        super().save(
            *args,
            **kwargs,
        )

        sync_product_active_if_no_sellable_variants(
            self.product_id,
        )