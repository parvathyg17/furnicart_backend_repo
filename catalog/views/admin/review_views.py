from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.pagination import CustomPagination
from core.utils.permissions import IsAdminUserCustom

from catalog.selectors.review_selectors import (
    get_admin_filtered_reviews,
)
from catalog.serializers.review_serializers import (
    AdminReviewModerationSerializer,
    ProductReviewSerializer,
)
from catalog.services.review_services import (
    moderate_review_for_admin,
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


class AdminReviewListView(
    APIView,
):

    permission_classes = [
        IsAuthenticated,
        IsAdminUserCustom,
    ]

    def get(
        self,
        request,
    ):

        reviews = get_admin_filtered_reviews(
            request.GET,
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


class AdminReviewDetailView(
    APIView,
):

    permission_classes = [
        IsAuthenticated,
        IsAdminUserCustom,
    ]

    def patch(
        self,
        request,
        review_id,
    ):

        ser = AdminReviewModerationSerializer(
            data=request.data,
        )

        ser.is_valid(
            raise_exception=True,
        )

        try:

            review = moderate_review_for_admin(
                review_id,
                status=ser.validated_data[
                    "status"
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
        )
