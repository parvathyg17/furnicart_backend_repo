from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.pagination import CustomPagination
from core.utils.media import resolve_media_url

from catalog.selectors.review_selectors import (
    get_approved_reviews_for_product,
    get_eligible_products_for_user,
    get_user_product_by_ref,
    get_user_review_for_product,
    user_can_review_product,
)
from catalog.serializers.review_serializers import (
    EligibleProductSerializer,
    ProductReviewCreateSerializer,
    ProductReviewSerializer,
    ProductReviewUpdateSerializer,
)
from catalog.services.review_services import (
    create_review_for_user,
    delete_review_for_user,
    update_review_for_user,
)


def _validation_error_response(
    exc,
):

    if isinstance(
        exc.detail,
        dict,
    ):

        return Response(
            exc.detail,
            status=status.HTTP_400_BAD_REQUEST,
        )

    if isinstance(
        exc.detail,
        list,
    ):

        return Response(
            {
                "detail": exc.detail,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    return Response(
        {
            "detail": str(
                exc.detail,
            ),
        },
        status=status.HTTP_400_BAD_REQUEST,
    )


def _product_thumbnail(
    product,
    request,
):

    primary_image = None

    for variant in product.variants.all():

        if not variant.is_active:

            continue

        images = sorted(
            variant.images.all(),
            key=lambda img: (
                img.display_order,
                -img.created_at.timestamp(),
            ),
        )

        for image in images:

            if image.is_primary:

                primary_image = image
                break

        if not primary_image and images:

            primary_image = images[0]

        if primary_image:

            break

    if not primary_image:

        return None

    return resolve_media_url(
        primary_image.image,
        request,
    )


class ProductReviewListCreateView(
    APIView,
):

    def get_permissions(
        self,
    ):

        if self.request.method == "POST":

            return [
                IsAuthenticated(),
            ]

        return []

    def get(
        self,
        request,
        product_ref,
    ):

        product = get_user_product_by_ref(
            product_ref,
        )

        if not product:

            return Response(
                {
                    "error": "Product not available.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        reviews = get_approved_reviews_for_product(
            product,
        )

        paginator = CustomPagination()

        paginated = paginator.paginate_queryset(
            reviews,
            request,
        )

        serializer = ProductReviewSerializer(
            paginated,
            many=True,
            context={
                "request": request,
            },
        )

        return paginator.get_paginated_response(
            serializer.data,
        )

    def post(
        self,
        request,
        product_ref,
    ):

        ser = ProductReviewCreateSerializer(
            data=request.data,
        )

        ser.is_valid(
            raise_exception=True,
        )

        try:

            review = create_review_for_user(
                request.user,
                product_ref,
                rating=ser.validated_data[
                    "rating"
                ],
                title=ser.validated_data.get(
                    "title",
                    "",
                ),
                body=ser.validated_data[
                    "body"
                ],
            )

        except ValidationError as exc:

            return _validation_error_response(
                exc,
            )

        out = ProductReviewSerializer(
            review,
            context={
                "request": request,
            },
        )

        return Response(
            out.data,
            status=status.HTTP_201_CREATED,
        )


class UserReviewDetailView(
    APIView,
):

    permission_classes = [
        IsAuthenticated,
    ]

    def patch(
        self,
        request,
        review_id,
    ):

        ser = ProductReviewUpdateSerializer(
            data=request.data,
            partial=True,
        )

        ser.is_valid(
            raise_exception=True,
        )

        if not ser.validated_data:

            return Response(
                {
                    "detail": "No fields to update.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:

            review = update_review_for_user(
                request.user,
                review_id,
                **ser.validated_data,
            )

        except ValidationError as exc:

            return _validation_error_response(
                exc,
            )

        out = ProductReviewSerializer(
            review,
            context={
                "request": request,
            },
        )

        return Response(
            out.data,
        )

    def delete(
        self,
        request,
        review_id,
    ):

        try:

            delete_review_for_user(
                request.user,
                review_id,
            )

        except ValidationError as exc:

            return _validation_error_response(
                exc,
            )

        return Response(
            status=status.HTTP_204_NO_CONTENT,
        )


class UserReviewListView(
    APIView,
):

    permission_classes = [
        IsAuthenticated,
    ]

    def get(
        self,
        request,
    ):

        from catalog.models import ProductReview

        reviews = ProductReview.objects.filter(
            user=request.user,
        ).select_related(
            "product",
            "order_line",
        ).order_by(
            "-created_at",
        )

        paginator = CustomPagination()

        paginated = paginator.paginate_queryset(
            reviews,
            request,
        )

        serializer = ProductReviewSerializer(
            paginated,
            many=True,
            context={
                "request": request,
            },
        )

        return paginator.get_paginated_response(
            serializer.data,
        )


class EligibleReviewProductsView(
    APIView,
):

    permission_classes = [
        IsAuthenticated,
    ]

    def get(
        self,
        request,
    ):

        from catalog.selectors.review_selectors import (
            get_delivered_order_line_for_product,
        )

        products = get_eligible_products_for_user(
            request.user,
        ).prefetch_related(
            "variants__images",
        )

        payload = []

        for product in products:

            line = get_delivered_order_line_for_product(
                request.user,
                product,
            )

            payload.append(
                {
                    "id": product.id,
                    "name": product.name,
                    "slug": product.slug,
                    "thumbnail": _product_thumbnail(
                        product,
                        request,
                    ),
                    "order_line_id": (
                        line.id if line else None
                    ),
                },
            )

        serializer = EligibleProductSerializer(
            payload,
            many=True,
        )

        return Response(
            serializer.data,
        )


class ProductReviewEligibilityView(
    APIView,
):

    permission_classes = [
        IsAuthenticated,
    ]

    def get(
        self,
        request,
        product_ref,
    ):

        product = get_user_product_by_ref(
            product_ref,
        )

        if not product:

            return Response(
                {
                    "error": "Product not available.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        user_review = get_user_review_for_product(
            request.user,
            product,
        )

        review_data = None

        if user_review:

            review_data = ProductReviewSerializer(
                user_review,
                context={
                    "request": request,
                },
            ).data

        return Response(
            {
                "can_review": user_can_review_product(
                    request.user,
                    product,
                ),
                "user_review": review_data,
            },
        )
