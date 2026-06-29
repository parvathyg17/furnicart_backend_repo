from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from rest_framework.exceptions import (
    ValidationError as DRFValidationError,
)

from core.pagination import CustomPagination

from promotions.services.offer_display import (
    extend_serializer_context_with_offers,
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

        paginator = CustomPagination()

        page = paginator.paginate_queryset(
            items,
            request,
            view=self,
        )

        if page is not None:

            products = [
                item.variant.product
                for item in page
            ]

            serializer = WishlistItemSerializer(
                page,
                many=True,
                context=extend_serializer_context_with_offers(
                    {
                        "request": request,
                    },
                    products,
                ),
            )

            return paginator.get_paginated_response(
                serializer.data,
            )

        products = [
            item.variant.product
            for item in items
        ]

        serializer = WishlistItemSerializer(
            items,
            many=True,
            context=extend_serializer_context_with_offers(
                {
                    "request": request,
                },
                products,
            ),
        )

        return Response(
            {
                "results": serializer.data,
            },
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
