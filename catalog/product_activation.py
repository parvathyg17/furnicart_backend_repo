


def sync_product_active_if_no_sellable_variants(product_id):

    from catalog.models.product import Product
    from catalog.models.product_variant import ProductVariant

    sellable_exists = (
        ProductVariant.objects.filter(
            product_id=product_id,
            is_active=True,
            stock__gt=0,
        ).exists()
    )

    if not sellable_exists:

        Product.objects.filter(
            pk=product_id,
            is_active=True,
        ).update(
            is_active=False,
        )
