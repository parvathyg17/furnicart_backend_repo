from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from catalog.models import VariantImage
from catalog.models import ProductVariant
from catalog.serializers import ProductVariantSerializer

from catalog.models import (
    Product,
    ProductVariant,
)

from catalog.serializers import (
    ProductVariantSerializer
)
from catalog.services.variant_services import (
    toggle_variant_status,
    validate_variant_can_activate,
)
from core.utils.permissions import (
    IsAdminUserCustom
)

class ProductVariantCreateView(APIView):

    permission_classes = [
        IsAuthenticated,
        IsAdminUserCustom
    ]

    def post(self, request, product_id):

        try:

            product = Product.objects.get(
                id=product_id
            )

        except Product.DoesNotExist:

            return Response(
                {
                    "error": "Product not found"
                },
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = ProductVariantSerializer(
            data=request.data,
            context={
                "request": request
            }
        )

        serializer.is_valid(
            raise_exception=True
        )

        serializer.save(
            product=product
        )

        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
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

        remaining_images = (
            variant.images.count() - 1
        )

        if (
            variant.is_active
            and
            remaining_images < 3
        ):

            return Response(
                {
                    "error":
                    "Active variants require minimum 3 images"
                },
                status=status.HTTP_400_BAD_REQUEST
            )

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

        if not variant.is_active:

            is_valid, error = validate_variant_can_activate(
                variant
            )

            if not is_valid:

                return Response(
                    {
                        "error": error
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