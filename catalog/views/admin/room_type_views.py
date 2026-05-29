import logging

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import (
    IsAuthenticated
)

from rest_framework.parsers import (
    MultiPartParser,
    FormParser
)

from core.pagination import (
    CustomPagination
)

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
    restore_room_type,
    soft_delete_room_type,
)

logger = logging.getLogger(__name__)


# ==========================================
# ROOM TYPE LIST CREATE
# ==========================================

class RoomTypeListCreateView(APIView):

    permission_classes = [
        IsAuthenticated,
        IsAdminUserCustom
    ]

    parser_classes = [
        MultiPartParser,
        FormParser
    ]

    # ==========================================
    # GET ROOM TYPES
    # ==========================================

    def get(self, request):

        room_types = (
            get_admin_filtered_room_types(
                request.GET
            )
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

        logger.info(
            "Admin fetched room types list"
        )

        return paginator.get_paginated_response(
            serializer.data
        )

    # ==========================================
    # CREATE ROOM TYPE
    # ==========================================

    def post(self, request):

        serializer = RoomTypeSerializer(
            data=request.data,
            context={
                "request": request
            }
        )

        serializer.is_valid(
            raise_exception=True
        )

        serializer.save()

        logger.info(
            f"Room type created: "
            f"{serializer.instance.id}"
        )

        return Response(
            {
                "success": True,
                "message":
                "Room type created successfully",
                "data":
                serializer.data,
            },
            status=201
        )


# ==========================================
# ROOM TYPE DETAIL
# ==========================================

class RoomTypeDetailView(APIView):

    permission_classes = [
        IsAuthenticated,
        IsAdminUserCustom
    ]

    parser_classes = [
        MultiPartParser,
        FormParser
    ]

    # ==========================================
    # GET SINGLE ROOM TYPE
    # ==========================================

    def get(
        self,
        request,
        room_type_id
    ):

        room_type = (
            get_room_type_by_id(
                room_type_id
            )
        )

        if not room_type:

            logger.warning(
                f"Room type not found: "
                f"{room_type_id}"
            )

            return Response(
                {
                    "success": False,
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

        logger.info(
            f"Room type fetched: "
            f"{room_type.id}"
        )

        return Response(
            {
                "success": True,
                "data":
                serializer.data,
            }
        )

    # ==========================================
    # UPDATE ROOM TYPE
    # ==========================================

    def put(
        self,
        request,
        room_type_id
    ):

        room_type = (
            get_room_type_by_id(
                room_type_id
            )
        )

        if not room_type:

            logger.warning(
                f"Room type not found "
                f"for update: "
                f"{room_type_id}"
            )

            return Response(
                {
                    "success": False,
                    "error":
                    "Room type not found"
                },
                status=404
            )

        serializer = RoomTypeSerializer(
            room_type,
            data=request.data,
            partial=True,
            context={
                "request": request
            }
        )

        serializer.is_valid(
            raise_exception=True
        )

        serializer.save()

        logger.info(
            f"Room type updated: "
            f"{room_type.id}"
        )

        return Response(
            {
                "success": True,
                "message":
                "Room type updated successfully",
                "data":
                serializer.data,
            }
        )


# ==========================================
# SOFT DELETE ROOM TYPE
# ==========================================

class RoomTypeSoftDeleteView(APIView):

    permission_classes = [
        IsAuthenticated,
        IsAdminUserCustom
    ]

    def patch(
        self,
        request,
        room_type_id
    ):

        room_type = (
            get_room_type_by_id(
                room_type_id
            )
        )

        if not room_type:

            logger.warning(
                f"Room type not found "
                f"for delete: "
                f"{room_type_id}"
            )

            return Response(
                {
                    "success": False,
                    "error":
                    "Room type not found"
                },
                status=404
            )

        soft_delete_room_type(
            room_type
        )

        logger.info(
            f"Room type deleted: "
            f"{room_type.id}"
        )

        return Response(
            {
                "success": True,
                "message":
                "Room type deleted successfully",
                "room_type_id":
                room_type.id,
            }
        )


# ==========================================
# RESTORE ROOM TYPE
# ==========================================

class RoomTypeRestoreView(APIView):

    permission_classes = [
        IsAuthenticated,
        IsAdminUserCustom
    ]

    def patch(
        self,
        request,
        room_type_id
    ):

        room_type = (
            get_room_type_by_id(
                room_type_id
            )
        )

        if not room_type:

            logger.warning(
                f"Room type not found "
                f"for restore: "
                f"{room_type_id}"
            )

            return Response(
                {
                    "success": False,
                    "error":
                    "Room type not found"
                },
                status=404
            )

        restore_room_type(
            room_type
        )

        logger.info(
            f"Room type restored: "
            f"{room_type.id}"
        )

        return Response(
            {
                "success": True,
                "message":
                "Room type restored successfully",
                "room_type_id":
                room_type.id,
            }
        )

