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

        if value.size > 5 * 1024 * 1024:

            raise serializers.ValidationError(
                "Image size must be below 5MB"
            )

        return value