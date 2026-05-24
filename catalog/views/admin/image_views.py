from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import (
    IsAuthenticated
)
from rest_framework import status
from rest_framework.parsers import (
    MultiPartParser,
    FormParser
)

from core.utils.permissions import (
    IsAdminUserCustom
)

from catalog.models import (
    ProductVariant
)

from catalog.serializers.variant_image_serializers import (
    VariantImageUploadSerializer
)

class VariantImageUploadView(APIView):

    permission_classes = [
        IsAuthenticated,
        IsAdminUserCustom
    ]

    parser_classes = [
        MultiPartParser,
        FormParser
    ]

    def post(self, request):

        variant_id = request.data.get(
            "variant"
        )

        files = request.FILES.getlist(
            "images"
        )

        # ==========================================
        # VALIDATE VARIANT
        # ==========================================

        try:

            variant = ProductVariant.objects.get(
                id=variant_id
            )

        except ProductVariant.DoesNotExist:

            return Response(
                {
                    "error":
                    "Variant not found"
                },
                status=404
            )

        # ==========================================
        # VALIDATE MINIMUM IMAGES
        # ==========================================

        existing_count = (
            variant.images.count()
        )

        total_count = (
            existing_count +
            len(files)
        )

        if total_count < 3:

            return Response(
                {
                    "error":
                    "Minimum 3 images required"
                },
                status=400
            )

        uploaded_images = []

        # ==========================================
        # MULTIPLE UPLOAD LOOP
        # ==========================================

        for index, file in enumerate(files):

            serializer = (
                VariantImageUploadSerializer(
                    data={
                        "variant":
                        variant.id,

                        "image":
                        file,

                        "display_order":
                        existing_count + index,
                    }
                )
            )

            serializer.is_valid(
                raise_exception=True
            )

            image = serializer.save()

            # ==========================================
            # AUTO PRIMARY
            # ==========================================

            if variant.images.count() == 1:

                image.is_primary = True

                image.save()

            uploaded_images.append(
                serializer.data
            )

        return Response(
            uploaded_images,
            status=status.HTTP_201_CREATED
        )