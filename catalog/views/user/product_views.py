from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from core.pagination import CustomPagination

from catalog.selectors.product_selectors import (
    get_user_filtered_products
)

from catalog.services.product_services import (
    get_user_product_by_id
)

from catalog.serializers.product_serializers import (
    ProductSerializer
)


class UserProductListView(APIView):

    permission_classes = []

    def get(self, request):

        products = get_user_filtered_products(
            request.GET
        )

        paginator = CustomPagination()

        paginated_products = paginator.paginate_queryset(
            products,
            request
        )

        serializer = ProductSerializer(
            paginated_products,
            many=True,
            context={
                "request": request,
                "exclude_related": True,
            }
        )

        return paginator.get_paginated_response(
            serializer.data
        )


class UserProductDetailView(APIView):

    permission_classes = []

    def get(self, request, product_id):

        product = get_user_product_by_id(
            product_id
        )

        if not product:

            return Response(
                {
                    "error":
                    "Product not available"
                },
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = ProductSerializer(
            product,
            context={
                "request": request
            }
        )

        return Response(
            serializer.data
        )