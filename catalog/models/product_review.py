from django.conf import settings
from django.db import models

from catalog.models.product import Product


class ProductReview(models.Model):

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="product_reviews",
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="reviews",
    )

    order_line = models.ForeignKey(
        "orders.OrderLine",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviews",
    )

    rating = models.PositiveSmallIntegerField()

    title = models.CharField(
        max_length=120,
        blank=True,
        default="",
    )

    body = models.TextField(
        max_length=2000,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.APPROVED,
        db_index=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:

        ordering = ["-created_at"]

        constraints = [
            models.UniqueConstraint(
                fields=["user", "product"],
                name="unique_user_product_review",
            ),
            models.CheckConstraint(
                condition=models.Q(
                    rating__gte=1,
                    rating__lte=5,
                ),
                name="product_review_rating_1_to_5",
            ),
        ]

        indexes = [
            models.Index(
                fields=["product", "status", "-created_at"],
            ),
        ]

    def __str__(self):

        return (
            f"Review {self.id} — "
            f"{self.product.name} ({self.rating}/5)"
        )
