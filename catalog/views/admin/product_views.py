from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from catalog.services.product_services import (
    get_admin_product_by_id,
    soft_delete_product,
    toggle_product_status,
    validate_product_can_activate,
)

from catalog.serializers.product_serializers import (
    ProductSerializer
)

from core.utils.permissions import (
    IsAdminUserCustom
)


class ProductDetailView(APIView):

    permission_classes = [
        IsAuthenticated,
        IsAdminUserCustom
    ]

    def get(self, request, product_id):

        product = get_admin_product_by_id(
            product_id
        )

        if not product:

            return Response(
                {
                    "error": "Product not found"
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

    def put(self, request, product_id):

        product = get_admin_product_by_id(
            product_id
        )

        if not product:

            return Response(
                {
                    "error": "Product not found"
                },
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = ProductSerializer(
            product,
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

        return Response(
            serializer.data
        )

class ProductSoftDeleteView(APIView):

    permission_classes = [
        IsAuthenticated,
        IsAdminUserCustom
    ]

    def patch(self, request, product_id):

        product = get_admin_product_by_id(
            product_id
        )

        if not product:

            return Response(
                {
                    "error": "Product not found"
                },
                status=status.HTTP_404_NOT_FOUND
            )

        soft_delete_product(product)

        return Response({
            "message":
            "Product deleted successfully"
        })


class ProductToggleStatusView(APIView):

    permission_classes = [
        IsAuthenticated,
        IsAdminUserCustom
    ]

    def patch(self, request, product_id):

        product = get_admin_product_by_id(
            product_id
        )

        if not product:

            return Response(
                {
                    "error": "Product not found"
                },
                status=status.HTTP_404_NOT_FOUND
            )
        
        if not product.is_active:

            is_valid, error = validate_product_can_activate(
                product
            )

            if not is_valid:

                return Response(
                    {
                        "error": error
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

        product = toggle_product_status(
            product
        )

        return Response({

            "id": product.id,

            "is_active": product.is_active,

            "message": (
                "Product activated"
                if product.is_active
                else "Product deactivated"
            )
        })