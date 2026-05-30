from rest_framework import serializers

from catalog.models import Product

from catalog.serializers.product_serializers import (
    ProductVariantSerializer,
)

from wishlist.models import WishlistItem


class ProductMicroSerializer(
    serializers.ModelSerializer,
):

    class Meta:

        model = Product

        fields = [
            "id",
            "name",
            "slug",
        ]


class WishlistVariantSerializer(
    ProductVariantSerializer,
):

    product = ProductMicroSerializer(
        read_only=True,
    )

    class Meta(
        ProductVariantSerializer.Meta,
    ):

        fields = (
            list(
                ProductVariantSerializer.Meta.fields
            )
            + ["product"]
        )


class WishlistItemSerializer(
    serializers.ModelSerializer,
):

    variant = WishlistVariantSerializer(
        read_only=True,
    )

    class Meta:

        model = WishlistItem

        fields = [
            "id",
            "variant",
            "created_at",
        ]

        read_only_fields = fields
