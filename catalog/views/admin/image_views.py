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

from catalog.serializers.variant_image_serializers import (
    VariantImageUploadSerializer
)

from core.utils.permissions import (
    IsAdminUserCustom
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

        serializer = VariantImageUploadSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        serializer.save()

        variant = serializer.instance.variant

        image_count = variant.images.count()

        if image_count == 1:

            serializer.instance.is_primary = True
            serializer.instance.save()

        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )