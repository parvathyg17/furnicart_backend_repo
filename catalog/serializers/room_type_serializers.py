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