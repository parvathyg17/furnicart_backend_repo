from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from catalog.models import Category
from catalog.selectors.category_selectors import get_admin_filtered_categories
from catalog.serializers import CategorySerializer
from catalog.services.category_services import (
    restore_category,
    soft_delete_category,
)
from core.pagination import CustomPagination
from core.utils.permissions import IsAdminUserCustom


class AdminCategoryViewSet(viewsets.ModelViewSet):
    """Admin CRUD for categories; soft-delete and restore are custom actions."""

    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated, IsAdminUserCustom]
    parser_classes = [MultiPartParser, FormParser]
    pagination_class = CustomPagination
    lookup_field = "pk"
    lookup_url_kwarg = "category_id"
    http_method_names = ["get", "post", "put", "patch", "head", "options"]

    def get_queryset(self):
        if getattr(self, "action", None) == "list":
            return get_admin_filtered_categories(self.request.GET)
        return Category.objects.select_related("parent").prefetch_related(
            "children"
        )

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["request"] = self.request
        return ctx

    @action(detail=True, methods=["patch"], url_path="delete")
    def soft_delete(self, request, category_id=None):
        category = self.get_object()
        soft_delete_category(category)
        return Response(
            {"message": "Category deleted successfully"},
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["patch"], url_path="restore")
    def restore(self, request, category_id=None):
        category = self.get_object()
        try:
            restore_category(category)
        except ValueError as exc:
            return Response(
                {"error": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(
            {"message": "Category restored successfully"},
            status=status.HTTP_200_OK,
        )
