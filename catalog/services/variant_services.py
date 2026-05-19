from catalog.models import ProductVariant


def get_variant_by_id(variant_id):
    try:
        return ProductVariant.objects.get(id=variant_id)
    except ProductVariant.DoesNotExist:
        return None


def delete_variant(variant):
    product = variant.product

    if product.variants.count() <= 1:
        return False, "Cannot delete last variant"

    variant.delete()
    return True, "Variant deleted"


def toggle_variant_status(variant):
    variant.is_active = not variant.is_active
    variant.save()
    return variant