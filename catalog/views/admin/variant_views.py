from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from catalog.models import VariantImage
from catalog.models import ProductVariant
from catalog.serializers import ProductVariantSerializer

from core.utils.permissions import (
    IsAdminUserCustom
)


class ProductVariantDetailView(APIView):

    permission_classes = [
        IsAuthenticated,
        IsAdminUserCustom
    ]

    def get_object(self, variant_id):

        try:

            return ProductVariant.objects.get(
                id=variant_id
            )

        except ProductVariant.DoesNotExist:

            return None

    # =========================
    # UPDATE VARIANT
    # =========================

    def put(self, request, variant_id):

        variant = self.get_object(
            variant_id
        )

        if not variant:

            return Response(
                {
                    "error": "Variant not found"
                },
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = ProductVariantSerializer(
            variant,
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

    # =========================
    # DELETE VARIANT
    # =========================


    
    def delete(self, request, variant_id):

        variant = self.get_object(
            variant_id
        )

        if not variant:

            return Response(
                {
                    "error": "Variant not found"
                },
                status=status.HTTP_404_NOT_FOUND
            )

        product = variant.product

        variant_count = product.variants.count()

        if variant_count <= 1:

            return Response(
                {
                    "error":
                    "Cannot delete the last variant"
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        variant.delete()

        return Response({

            "message":
            "Variant deleted successfully"

        }, status=status.HTTP_204_NO_CONTENT)
    

class VariantImageDeleteView(APIView):

    permission_classes = [
        IsAuthenticated,
        IsAdminUserCustom
    ]

    def delete(self, request, image_id):

        try:

            image = VariantImage.objects.get(
                id=image_id
            )

        except VariantImage.DoesNotExist:

            return Response(
                {
                    "error": "Image not found"
                },
                status=status.HTTP_404_NOT_FOUND
            )

        image.delete()

        return Response({

            "message":
            "Image deleted successfully"

        }, status=status.HTTP_204_NO_CONTENT)