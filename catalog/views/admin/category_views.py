from core.pagination import CustomPagination


from catalog.selectors.category_selectors import (
    get_admin_filtered_categories
)

from catalog.services.category_services import (
    get_category_by_id,
    soft_delete_category,
)

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from catalog.serializers import CategorySerializer
from rest_framework.parsers import MultiPartParser, FormParser
from core.utils.permissions import IsAdminUserCustom


class CategoryListCreateView(APIView):

    permission_classes = [
        IsAuthenticated,
        IsAdminUserCustom
    ]

    parser_classes = [
    MultiPartParser,
    FormParser
    ]

    def get(self, request):

        categories = get_admin_filtered_categories(
            request.GET
        )

        paginator = CustomPagination()

        paginated_categories = paginator.paginate_queryset(
            categories,
            request
        )

        serializer = CategorySerializer(
            paginated_categories,
            many=True,
            context={
                "request": request
            }
        )

        return paginator.get_paginated_response(
            serializer.data
        )

    def post(self, request):

        serializer = CategorySerializer(
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
    

class CategoryDetailView(APIView):

    permission_classes = [
        IsAuthenticated,
        IsAdminUserCustom
    ]

    parser_classes = [
        MultiPartParser,
        FormParser
    ]

    def get(self, request, category_id):

        category = get_category_by_id(
            category_id
        )

        if not category:

            return Response(
                {
                    "error": "Category not found"
                },
                status=404
            )

        serializer = CategorySerializer(
            category,
            context={
                "request": request
            }
        )

        return Response(
            serializer.data
        )

    def put(self, request, category_id):

        category = get_category_by_id(
            category_id
        )

        if not category:

            return Response(
                {
                    "error": "Category not found"
                },
                status=404
            )

        serializer = CategorySerializer(
            category,
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
    

class CategorySoftDeleteView(APIView):

    permission_classes = [
        IsAuthenticated,
        IsAdminUserCustom
    ]

    def patch(self, request, category_id):

        category = get_category_by_id(
            category_id
        )

        if not category:

            return Response(
                {
                    "error": "Category not found"
                },
                status=404
            )

        soft_delete_category(category)

        return Response({
            "message":
            "Category deleted successfully"
        })