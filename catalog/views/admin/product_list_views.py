from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from core.pagination import CustomPagination

from catalog.selectors.product_selectors import (
    get_admin_filtered_products,
)

from catalog.serializers.product_serializers import (
    ProductSerializer,
)

from core.utils.permissions import (
    IsAdminUserCustom,
)


class ProductListCreateView(APIView):

    permission_classes = [
        IsAuthenticated,
        IsAdminUserCustom,
    ]

    def get(self, request):

        products = get_admin_filtered_products(
            request.GET,
        )

        paginator = CustomPagination()

        paginated_products = paginator.paginate_queryset(
            products,
            request,
        )

        serializer = ProductSerializer(
            paginated_products,
            many=True,
            context={
                "request": request,
            },
        )

        return paginator.get_paginated_response(
            serializer.data,
        )

    def post(self, request):

        serializer = ProductSerializer(
            data=request.data,
            context={
                "request": request,
            },
        )

        serializer.is_valid(
            raise_exception=True,
        )

        serializer.save()

        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
        )
