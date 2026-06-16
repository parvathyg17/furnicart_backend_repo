from rest_framework import serializers
from PIL import Image

from catalog.models import VariantImage
from core.utils.media import resolve_media_url


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

        return resolve_media_url(
            obj.image,
            request,
        )

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

            try:

                img.verify()

            finally:

                img.close()

        except Exception:

            raise serializers.ValidationError(
                "Invalid image file"
            )

       
        try:

            value.seek(0)

        except (AttributeError, OSError, ValueError):

            pass

        return value