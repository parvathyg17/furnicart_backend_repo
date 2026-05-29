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

    """
    Legacy helper: minimum 3 images per active variant.
    Prefer validate_product_can_activate for full checks.
    """

    active_variants = product.variants.filter(
        is_active=True
    )

    for variant in active_variants:

        if variant.images.count() < 3:

            return (
                False,
                (
                    f'Variant "{variant.variant_name}" '
                    "must have at least 3 images"
                ),
            )

    return True, None


def validate_product_can_activate(
    product,
    description=None,
    room_type_ids=None,
):

    """
    Full catalog readiness for an active product.

    description / room_type_ids: when validating a ProductSerializer
    update before save, pass merged values so room types and
    description are evaluated against the incoming payload.
    """

    name = (product.name or "").strip()

    if not name:

        return False, "Product name is required."

    desc = product.description if description is None else description

    if not (desc or "").strip():

        return False, "Description is required."

    if room_type_ids is not None:

        if len(room_type_ids) < 1:

            return (
                False,
                "Select at least one room type.",
            )

    elif product.room_types.count() < 1:

        return False, "Select at least one room type."

    if product.variants.count() < 3:

        return (
            False,
            "Add at least 3 variants before activating the product.",
        )

    active_variants = product.variants.filter(
        is_active=True
    )

    if active_variants.count() < 1:

        return (
            False,
            "At least one variant must be active.",
        )

    for variant in active_variants:

        ok, err = validate_variant_fields_and_images(
            variant
        )

        if not ok:

            return False, err

    return True, None


def validate_variant_fields_and_images(variant):

    """
    Each active variant must have all fields set and at least 3 images.
    """

    if variant.images.count() < 3:

        return (
            False,
            (
                f'Variant "{variant.variant_name}" '
                "must have at least 3 images."
            ),
        )

    checks = [
        (
            (variant.variant_name or "").strip(),
            "variant name",
        ),
        (
            (variant.sku or "").strip(),
            "SKU",
        ),
        (
            (variant.color or "").strip(),
            "color / finish",
        ),
        (
            (variant.material or "").strip(),
            "material",
        ),
        (
            (variant.size or "").strip(),
            "size",
        ),
    ]

    for value, label in checks:

        if not value:

            return (
                False,
                (
                    f'Variant "{variant.variant_name}" '
                    f"is missing {label}."
                ),
            )

    if variant.price is None or variant.price <= 0:

        return (
            False,
            (
                f'Variant "{variant.variant_name}" '
                "must have a price greater than 0."
            ),
        )

    if variant.stock is None or variant.stock < 0:

        return (
            False,
            (
                f'Variant "{variant.variant_name}" '
                "cannot have negative stock."
            ),
        )

    return True, None