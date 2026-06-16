from rest_framework import serializers

from catalog.models import ProductReview


class ProductReviewSerializer(
    serializers.ModelSerializer,
):

    user_display = serializers.SerializerMethodField()

    product_name = serializers.CharField(
        source="product.name",
        read_only=True,
    )

    product_slug = serializers.CharField(
        source="product.slug",
        read_only=True,
    )

    variant_name = serializers.SerializerMethodField()

    class Meta:

        model = ProductReview

        fields = [
            "id",
            "product",
            "product_name",
            "product_slug",
            "rating",
            "title",
            "body",
            "status",
            "user_display",
            "variant_name",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "product",
            "status",
            "created_at",
            "updated_at",
        ]

    def get_user_display(
        self,
        obj,
    ):

        full_name = (
            obj.user.get_full_name() or ""
        ).strip()

        if full_name:

            parts = full_name.split()

            if len(parts) == 1:

                return parts[0]

            return f"{parts[0]} {parts[-1][0]}."

        email = (obj.user.email or "").strip()

        if email:

            local = email.split("@")[0]

            return local[:1].upper() + local[1:]

        return "Verified buyer"

    def get_variant_name(
        self,
        obj,
    ):

        if obj.order_line:

            return obj.order_line.variant_name

        return None


class ProductReviewCreateSerializer(
    serializers.Serializer,
):

    rating = serializers.IntegerField(
        min_value=1,
        max_value=5,
    )

    title = serializers.CharField(
        max_length=120,
        required=False,
        allow_blank=True,
        default="",
    )

    body = serializers.CharField(
        max_length=2000,
    )


class ProductReviewUpdateSerializer(
    serializers.Serializer,
):

    rating = serializers.IntegerField(
        min_value=1,
        max_value=5,
        required=False,
    )

    title = serializers.CharField(
        max_length=120,
        required=False,
        allow_blank=True,
    )

    body = serializers.CharField(
        max_length=2000,
        required=False,
    )


class AdminReviewModerationSerializer(
    serializers.Serializer,
):

    status = serializers.ChoiceField(
        choices=ProductReview.Status.choices,
    )


class EligibleProductSerializer(
    serializers.Serializer,
):

    id = serializers.IntegerField()

    name = serializers.CharField()

    slug = serializers.CharField()

    thumbnail = serializers.CharField(
        allow_null=True,
    )

    order_line_id = serializers.IntegerField(
        allow_null=True,
    )
