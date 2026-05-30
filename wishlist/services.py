from django.db import transaction

from rest_framework import serializers

from catalog.models import ProductVariant

from wishlist.models import (
    Wishlist,
    WishlistItem,
)


def get_or_create_wishlist(user):

    wishlist, _ = Wishlist.objects.get_or_create(
        user=user,
    )

    return wishlist


def _assert_variant_listable(variant):

    if not variant.product.is_active:

        raise serializers.ValidationError(
            "Product unavailable.",
        )

    if not variant.product.category.is_active:

        raise serializers.ValidationError(
            "Product unavailable.",
        )

    if not variant.is_active:

        raise serializers.ValidationError(
            "Variant unavailable.",
        )


@transaction.atomic
def toggle_wishlist_item(
    user,
    variant_id,
):

    try:

        variant = ProductVariant.objects.select_related(
            "product",
            "product__category",
        ).get(
            pk=variant_id,
        )

    except ProductVariant.DoesNotExist:

        raise serializers.ValidationError(
            "Variant not found.",
        )

    _assert_variant_listable(variant)

    wishlist = get_or_create_wishlist(user)

    item = WishlistItem.objects.filter(
        wishlist=wishlist,
        variant=variant,
    ).first()

    if item:

        item.delete()

        return False

    WishlistItem.objects.create(
        wishlist=wishlist,
        variant=variant,
    )

    return True
