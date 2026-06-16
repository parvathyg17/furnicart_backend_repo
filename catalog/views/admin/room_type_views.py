import logging

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from catalog.models import RoomType
from catalog.selectors.room_type_selectors import get_admin_filtered_room_types
from catalog.serializers.room_type_serializers import RoomTypeSerializer
from catalog.services.room_type_services import (
    restore_room_type,
    soft_delete_room_type,
)
from core.pagination import CustomPagination
from core.utils.permissions import IsAdminUserCustom

logger = logging.getLogger(__name__)


class AdminRoomTypeViewSet(viewsets.ModelViewSet):
    """Admin CRUD for room types; deactivate/reactivate via custom actions."""

    serializer_class = RoomTypeSerializer
    permission_classes = [IsAuthenticated, IsAdminUserCustom]
    parser_classes = [MultiPartParser, FormParser]
    pagination_class = CustomPagination
    lookup_field = "pk"
    lookup_url_kwarg = "room_type_id"
    http_method_names = ["get", "post", "put", "patch", "head", "options"]

    def get_queryset(self):
        if getattr(self, "action", None) == "list":
            return get_admin_filtered_room_types(self.request.GET)
        return RoomType.objects.all()

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["request"] = self.request
        return ctx

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        logger.info("Admin fetched room types list")
        return response

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        logger.info("Room type fetched: %s", instance.id)
        return Response(
            {"success": True, "data": serializer.data},
            status=status.HTTP_200_OK,
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        logger.info("Room type created: %s", serializer.instance.id)
        headers = self.get_success_headers(serializer.data)
        return Response(
            {
                "success": True,
                "message": "Room type created successfully",
                "data": serializer.data,
            },
            status=status.HTTP_201_CREATED,
            headers=headers,
        )

    def update(self, request, *args, **kwargs):
        kwargs.pop("partial", None)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        logger.info("Room type updated: %s", instance.id)
        return Response(
            {
                "success": True,
                "message": "Room type updated successfully",
                "data": serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["patch"], url_path="delete")
    def soft_delete(self, request, room_type_id=None):
        room_type = self.get_object()
        soft_delete_room_type(room_type)
        logger.info("Room type deleted: %s", room_type.id)
        return Response(
            {
                "success": True,
                "message": "Room type deleted successfully",
                "room_type_id": room_type.id,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["patch"], url_path="restore")
    def restore(self, request, room_type_id=None):
        room_type = self.get_object()
        restore_room_type(room_type)
        logger.info("Room type restored: %s", room_type.id)
        return Response(
            {
                "success": True,
                "message": "Room type restored successfully",
                "room_type_id": room_type.id,
            },
            status=status.HTTP_200_OK,
        )
