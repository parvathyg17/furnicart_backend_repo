from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from core.pagination import CustomPagination
from core.utils.permissions import (
    IsAdminUserCustom
)

from catalog.serializers.room_type_serializers import (
    RoomTypeSerializer
)

from catalog.selectors.room_type_selectors import (
    get_admin_filtered_room_types
)

from catalog.services.room_type_services import (
    get_room_type_by_id,
    soft_delete_room_type,
)

from rest_framework.parsers import (
    MultiPartParser,
    FormParser
)

class RoomTypeListCreateView(APIView):

    permission_classes = [
        IsAuthenticated,
        IsAdminUserCustom
    ]

    parser_classes = [
        MultiPartParser,
        FormParser
    ]

    def get(self, request):

        room_types = get_admin_filtered_room_types(
            request.GET
        )

        paginator = CustomPagination()

        paginated_room_types = (
            paginator.paginate_queryset(
                room_types,
                request
            )
        )

        serializer = RoomTypeSerializer(
            paginated_room_types,
            many=True,
            context={
                "request": request
            }
        )

        return paginator.get_paginated_response(
            serializer.data
        )

    def post(self, request):

        serializer = RoomTypeSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        serializer.save()

        return Response(
            serializer.data,
            status=201
        )


class RoomTypeDetailView(APIView):

    permission_classes = [
        IsAuthenticated,
        IsAdminUserCustom
    ]

    parser_classes = [
        MultiPartParser,
        FormParser
    ]

    def get(self, request, room_type_id):

        room_type = get_room_type_by_id(
            room_type_id
        )

        if not room_type:

            return Response(
                {
                    "error":
                    "Room type not found"
                },
                status=404
            )

        serializer = RoomTypeSerializer(
            room_type,
            context={
                "request": request
            }
        )

        return Response(
            serializer.data
        )

    def put(self, request, room_type_id):

        room_type = get_room_type_by_id(
            room_type_id
        )

        if not room_type:

            return Response(
                {
                    "error":
                    "Room type not found"
                },
                status=404
            )

        serializer = RoomTypeSerializer(
            room_type,
            data=request.data,
            partial=True
        )

        serializer.is_valid(
            raise_exception=True
        )

        serializer.save()

        return Response(
            serializer.data
        )


class RoomTypeSoftDeleteView(APIView):

    permission_classes = [
        IsAuthenticated,
        IsAdminUserCustom
    ]

    def patch(self, request, room_type_id):

        room_type = get_room_type_by_id(
            room_type_id
        )

        if not room_type:

            return Response(
                {
                    "error":
                    "Room type not found"
                },
                status=404
            )

        soft_delete_room_type(
            room_type
        )

        return Response({
            "message":
            "Room type deleted successfully"
        })