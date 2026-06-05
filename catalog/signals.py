from django.db.models.signals import post_delete
from django.dispatch import receiver

from catalog.models import VariantImage
from catalog.models.product_variant import ProductVariant
from catalog.product_activation import (
    sync_product_active_if_no_variants_remain,
)


@receiver(post_delete, sender=VariantImage)
def delete_variant_image_file(
    sender,
    instance,
    **kwargs,
):

    if instance.image:

        instance.image.delete(
            save=False,
        )


@receiver(post_delete, sender=ProductVariant)
def deactivate_product_when_last_variant_removed(
    sender,
    instance,
    **kwargs,
):

    sync_product_active_if_no_variants_remain(
        instance.product_id,
    )