from rest_framework import serializers

from catalog.models import RoomType


class RoomTypeSerializer(
    serializers.ModelSerializer
):

    class Meta:

        model = RoomType

        fields = [
            "id",
            "name",
            "slug",
            "image",
            "is_active",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "slug",
            "created_at",
            "is_active",
            "updated_at",
        ]

    # ==========================================
    # NAME VALIDATION
    # ==========================================

    def validate_name(
        self,
        value
    ):

        value = value.strip()

        if len(value) < 2:

            raise serializers.ValidationError(
                "Room type name must contain at least 2 characters."
            )

        existing_room_type = (
            RoomType.objects.filter(
                name__iexact=value
            )
        )

        if self.instance:

            existing_room_type = (
                existing_room_type.exclude(
                    id=self.instance.id
                )
            )

        if existing_room_type.exists():

            raise serializers.ValidationError(
                "Room type with this name already exists."
            )

        return value

    # ==========================================
    # IMAGE VALIDATION
    # ==========================================

    def validate_image(
        self,
        value
    ):

        if not value:

            return value

        max_size = (
            5 * 1024 * 1024
        )

        if value.size > max_size:

            raise serializers.ValidationError(
                "Image size must be below 5MB."
            )

        allowed_types = [
            "image/jpeg",
            "image/png",
            "image/webp",
        ]

        if (
            value.content_type
            not in allowed_types
        ):

            raise serializers.ValidationError(
                "Only JPEG, PNG and WEBP images are allowed."
            )

        return value