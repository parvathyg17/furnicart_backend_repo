from rest_framework import serializers

from catalog.models import VariantImage


class VariantImageUploadSerializer(
    serializers.ModelSerializer
):

    image_url = serializers.SerializerMethodField()

    class Meta:

        model = VariantImage

        fields = [
            "id",
            "variant",
            "image",
            "image_url",
            "is_primary",
            "display_order",
            "created_at",
        ]

        read_only_fields = [
            "id",
            "created_at"
        ]

    def get_image_url(self, obj):

        request = self.context.get(
            "request"
        )

        if obj.image and request:

            return request.build_absolute_uri(
                obj.image.url
            )

        return None

    

    def validate_image(self, value):

        if value.size > 5 * 1024 * 1024:

            raise serializers.ValidationError(
                "Image size must be below 5MB"
            )

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