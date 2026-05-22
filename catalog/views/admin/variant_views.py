from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from catalog.models import VariantImage
from catalog.models import ProductVariant
from catalog.serializers import ProductVariantSerializer
from catalog.services.variant_services import (
   
    toggle_variant_status,
)
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


    
    # def delete(self, request, variant_id):

    #     variant = self.get_object(
    #         variant_id
    #     )

    #     if not variant:

    #         return Response(
    #             {
    #                 "error": "Variant not found"
    #             },
    #             status=status.HTTP_404_NOT_FOUND
    #         )

    #     success, message = delete_variant(
    #         variant
    #     )

    #     if not success:

    #         return Response(
    #             {
    #                 "error": message
    #             },
    #             status=status.HTTP_400_BAD_REQUEST
    #         )

    #     return Response(
    #         {
    #             "message": message
    #         },
    #         status=status.HTTP_200_OK
    #     )
    

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

        variant = image.variant

        was_primary = image.is_primary

        image.delete()

        # =========================
        # ASSIGN NEW PRIMARY IMAGE
        # =========================

        if was_primary:

            next_image = variant.images.order_by(
                "display_order",
                "-created_at"
            ).first()

            if next_image:

                next_image.is_primary = True
                next_image.save()

        return Response({

            "message":
            "Image deleted successfully"

        }, status=status.HTTP_200_OK)
    

class ProductVariantToggleStatusView(APIView):

    permission_classes = [
        IsAuthenticated,
        IsAdminUserCustom
    ]

    def patch(self, request, variant_id):

        variant = ProductVariant.objects.filter(
            id=variant_id
        ).first()

        if not variant:

            return Response(
                {
                    "error": "Variant not found"
                },
                status=status.HTTP_404_NOT_FOUND
            )

        # =========================
        # PREVENT ALL VARIANTS DISABLED
        # =========================

        active_variants_count = (
            variant.product.variants.filter(
                is_active=True
            ).count()
        )

        if (
            variant.is_active
            and
            active_variants_count <= 1
        ):

            return Response(
                {
                    "error":
                    "Product must have at least one active variant"
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        variant = toggle_variant_status(
            variant
        )

        return Response({

            "id": variant.id,

            "is_active": variant.is_active,

            "message": (
                "Variant activated"
                if variant.is_active
                else "Variant deactivated"
            )
        })