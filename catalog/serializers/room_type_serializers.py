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
        ]

        read_only_fields = [
            "id",
            "slug",
        ]