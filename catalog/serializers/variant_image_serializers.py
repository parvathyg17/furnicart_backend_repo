from rest_framework import serializers

from catalog.models import VariantImage


class VariantImageUploadSerializer(
    serializers.ModelSerializer
):

    class Meta:

        model = VariantImage

        fields = [
            "id",
            "variant",
            "image",
            "created_at"
        ]

        read_only_fields = [
            "id",
            "created_at"
        ]

    def validate_image(self, value):

        # =========================
        # FILE SIZE VALIDATION
        # =========================

        if value.size > 5 * 1024 * 1024:

            raise serializers.ValidationError(
                "Image size must be below 5MB"
            )

        # =========================
        # FILE TYPE VALIDATION
        # =========================

        valid_extensions = [
            ".jpg",
            ".jpeg",
            ".png",
            ".webp",
        ]

        file_name = value.name.lower()

        if not file_name.endswith(
            tuple(valid_extensions)
        ):

            raise serializers.ValidationError(
                "Only JPG, JPEG, PNG, WEBP allowed"
            )

        return value