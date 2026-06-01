from rest_framework import serializers
from PIL import Image

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
            "width",
            "height",
            "file_size",
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

      

        valid_mime_types = [

            "image/jpeg",
            "image/jpg",
            "image/png",
            "image/webp",
        ]

        if value.content_type not in valid_mime_types:

            raise serializers.ValidationError(
                "Only JPG, JPEG, PNG, WEBP allowed"
            )

        

        try:

            img = Image.open(value)

            img.verify()

        except Exception:

            raise serializers.ValidationError(
                "Invalid image file"
            )

        return value