from catalog.models import Product


def get_related_products(product):

    return Product.objects.select_related(
        "category"
    ).prefetch_related(
        "variants__images"
    ).filter(
        category=product.category,
        is_active=True,
        category__is_active=True,
    ).exclude(
        id=product.id
    ).distinct()[:8]