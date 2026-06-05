


def sync_product_active_if_no_variants_remain(product_id):

    """
    Deactivate the product only when it has no variant rows left.

    Out-of-stock products stay visible in the shop; ``stock_status`` on
    serializers drives sold-out UI. Delisting is reserved for empty products
    or manual admin toggles.
    """

    from catalog.models.product import Product
    from catalog.models.product_variant import ProductVariant

    if ProductVariant.objects.filter(
        product_id=product_id,
    ).exists():

        return

    Product.objects.filter(
        pk=product_id,
        is_active=True,
    ).update(
        is_active=False,
    )
