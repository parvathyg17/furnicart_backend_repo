from django.db.models import Prefetch

from catalog.models import (
    Product,
    ProductVariant,
)


# =====================================================
# ADMIN PRODUCT
# =====================================================

def get_admin_product_by_id(product_id):

    try:

        return Product.objects.select_related(
            "category"
        ).prefetch_related(

            Prefetch(
                "variants",
                queryset=ProductVariant.objects.prefetch_related(
                    "images"
                )
            )

        ).get(
            id=product_id
        )

    except Product.DoesNotExist:

        return None


# =====================================================
# USER PRODUCT
# =====================================================

def get_user_product_by_id(product_id):

    try:

        return Product.objects.select_related(
            "category"
        ).prefetch_related(

            Prefetch(
                "variants",
                queryset=ProductVariant.objects.filter(
                    is_active=True
                ).prefetch_related(
                    "images"
                )
            )

        ).get(
            id=product_id,
            is_active=True,
            category__is_active=True,
            variants__is_active=True,
        )

    except Product.DoesNotExist:

        return None


# =====================================================
# SOFT DELETE
# =====================================================

def soft_delete_product(product):

    product.is_active = False

    product.save()

    return product


# =====================================================
# TOGGLE STATUS
# =====================================================

def toggle_product_status(product):

    product.is_active = not product.is_active

    product.save()

    return product


def validate_product_images(product):

    active_variants = product.variants.filter(
        is_active=True
    )

    for variant in active_variants:

        image_count = variant.images.count()

        if image_count < 3:

            return False, (
                f"{variant.variant_name} "
                f"must contain at least 3 images"
            )

    return True, None