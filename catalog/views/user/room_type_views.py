from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import (
    AllowAny
)

from catalog.selectors.room_type_selectors import (
    get_filtered_room_types
)

from catalog.serializers.room_type_serializers import (
    RoomTypeSerializer
)


class UserRoomTypeListView(APIView):

    permission_classes = [AllowAny]

    def get(self, request):

        room_types = get_filtered_room_types(
            request.GET
        )

        serializer = RoomTypeSerializer(
            room_types,
            many=True,
            context={
                "request": request
            }
        )

        return Response(
            serializer.data
        )