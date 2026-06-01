from django.db import models
from django.db.models import Q
from PIL import Image

from catalog.models.product_variant import (
    ProductVariant
)

class VariantImage(models.Model):

    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.CASCADE,
        related_name="images"
    )

    image = models.ImageField(
        upload_to="products/"
    )

    is_primary = models.BooleanField(
        default=False
    )

    display_order = models.PositiveIntegerField(
        default=0
    )

  

    width = models.PositiveIntegerField(
        null=True,
        blank=True
    )

    height = models.PositiveIntegerField(
        null=True,
        blank=True
    )

    file_size = models.PositiveIntegerField(
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:

        ordering = [
            "display_order",
            "-created_at"
        ]

        constraints = [

            models.UniqueConstraint(
                fields=["variant"],
                condition=Q(is_primary=True),
                name="unique_primary_image_per_variant"
            )

        ]

    def save(self, *args, **kwargs):

       

        if self.is_primary:

            VariantImage.objects.filter(
                variant=self.variant,
                is_primary=True
            ).exclude(
                id=self.id
            ).update(
                is_primary=False
            )

        super().save(*args, **kwargs)

        

        if self.image:

            img = Image.open(
                self.image.path
            )

            self.width = img.width

            self.height = img.height

            self.file_size = (
                self.image.size
            )

            super().save(
                update_fields=[
                    "width",
                    "height",
                    "file_size",
                ]
            )

    def __str__(self):

        return self.variant.sku