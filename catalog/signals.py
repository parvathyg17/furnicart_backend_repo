from django.db.models.signals import post_delete
from django.dispatch import receiver

from catalog.models import VariantImage


@receiver(post_delete, sender=VariantImage)
def delete_variant_image_file(
    sender,
    instance,
    **kwargs
):

    if instance.image:

        instance.image.delete(
            save=False
        )