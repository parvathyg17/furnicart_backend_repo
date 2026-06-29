from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from core.pagination import CustomPagination

from catalog.selectors.product_selectors import (
    get_user_filtered_products
)

from catalog.services.product_services import (
    get_user_product_by_id_or_slug,
)

from catalog.serializers.product_serializers import (
    ProductSerializer
)

from promotions.services.offer_display import (
    extend_serializer_context_with_offers,
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
            context=extend_serializer_context_with_offers(
                {
                    "request": request,
                    "exclude_related": True,
                },
                paginated_products or [],
            ),
        )

        return paginator.get_paginated_response(
            serializer.data
        )


class UserProductDetailView(APIView):

    permission_classes = []

    def get(
        self,
        request,
        product_ref=None,
        product_id=None,
    ):

        ref = (
            product_ref
            if product_ref is not None
            else (
                str(product_id)
                if product_id is not None
                else None
            )
        )

        if (
            ref is None
            or ref == ""
        ):

            return Response(
                {
                    "error": "Product reference required.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        product = get_user_product_by_id_or_slug(
            ref,
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
            context=extend_serializer_context_with_offers(
                {
                    "request": request,
                },
                [
                    product,
                ],
            ),
        )

        return Response(
            serializer.data
        )