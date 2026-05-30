from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from rest_framework.exceptions import (
    ValidationError as DRFValidationError,
)

from .serializers import (
    WishlistItemSerializer,
)

from .services import (
    get_or_create_wishlist,
    toggle_wishlist_item,
)

from wishlist.models import WishlistItem


class WishlistListView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        wishlist = get_or_create_wishlist(
            request.user,
        )

        items = (
            WishlistItem.objects.filter(
                wishlist=wishlist,
            )
            .select_related(
                "variant",
                "variant__product",
                "variant__product__category",
            )
            .prefetch_related(
                "variant__images",
            )
            .order_by(
                "-created_at",
            )
        )

        serializer = WishlistItemSerializer(
            items,
            many=True,
            context={
                "request": request,
            },
        )

        return Response(
            {
                "results": serializer.data,
            }
        )


class WishlistToggleView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):

        variant_id = request.data.get(
            "variant_id",
        )

        if variant_id is None:

            return Response(
                {
                    "error": "variant_id is required.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:

            variant_id = int(variant_id)

        except (TypeError, ValueError):

            return Response(
                {
                    "error": "variant_id must be an integer.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:

            is_wishlisted = toggle_wishlist_item(
                request.user,
                variant_id,
            )

        except DRFValidationError as exc:

            return Response(
                exc.detail,
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "is_wishlisted": is_wishlisted,
            }
        )
