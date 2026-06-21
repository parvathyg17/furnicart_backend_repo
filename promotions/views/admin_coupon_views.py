import logging

from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.pagination import CustomPagination
from core.utils.permissions import IsAdminUserCustom
from promotions.models import Coupon
from promotions.selectors.admin_coupon_selectors import (
    get_admin_filtered_coupons,
)
from promotions.serializers import AdminCouponSerializer
from promotions.services.admin_coupon_services import (
    delete_coupon,
)

logger = logging.getLogger(__name__)


class AdminCouponListCreateView(APIView):

    """
    GET: paginated coupon list (search, is_active).
    POST: create coupon.
    """

    permission_classes = [
        IsAuthenticated,
        IsAdminUserCustom,
    ]

    def get(
        self,
        request,
    ):

        queryset = get_admin_filtered_coupons(
            request.query_params,
        )

        paginator = CustomPagination()

        page = paginator.paginate_queryset(
            queryset,
            request,
            view=self,
        )

        if page is not None:

            serializer = AdminCouponSerializer(
                page,
                many=True,
                context={
                    "request": request,
                },
            )

            logger.info(
                "Admin fetched coupons list",
            )

            return paginator.get_paginated_response(
                serializer.data,
            )

        serializer = AdminCouponSerializer(
            queryset,
            many=True,
            context={
                "request": request,
            },
        )

        logger.info(
            "Admin fetched coupons list",
        )

        return Response(
            serializer.data,
        )

    def post(
        self,
        request,
    ):

        serializer = AdminCouponSerializer(
            data=request.data,
            context={
                "request": request,
            },
        )

        serializer.is_valid(
            raise_exception=True,
        )

        serializer.save()

        logger.info(
            "Admin created coupon %s",
            serializer.instance.id,
        )

        return Response(
            {
                "success": True,
                "message": "Coupon created successfully",
                "data": serializer.data,
            },
            status=status.HTTP_201_CREATED,
        )


class AdminCouponDetailView(APIView):

    """
    GET: single coupon.
    PATCH: partial update.
    DELETE: remove coupon.
    """

    permission_classes = [
        IsAuthenticated,
        IsAdminUserCustom,
    ]

    def get(
        self,
        request,
        coupon_id,
    ):

        try:

            instance = Coupon.objects.get(
                pk=coupon_id,
            )

        except Coupon.DoesNotExist:

            raise NotFound(
                detail="Coupon not found.",
            )

        serializer = AdminCouponSerializer(
            instance,
            context={
                "request": request,
            },
        )

        logger.info(
            "Admin fetched coupon %s",
            instance.id,
        )

        return Response(
            {
                "success": True,
                "data": serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    def patch(
        self,
        request,
        coupon_id,
    ):

        try:

            instance = Coupon.objects.get(
                pk=coupon_id,
            )

        except Coupon.DoesNotExist:

            raise NotFound(
                detail="Coupon not found.",
            )

        serializer = AdminCouponSerializer(
            instance,
            data=request.data,
            partial=True,
            context={
                "request": request,
            },
        )

        serializer.is_valid(
            raise_exception=True,
        )

        serializer.save()

        logger.info(
            "Admin updated coupon %s",
            instance.id,
        )

        return Response(
            {
                "success": True,
                "message": "Coupon updated successfully",
                "data": serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    def put(
        self,
        request,
        coupon_id,
    ):

        return self.patch(
            request,
            coupon_id,
        )

    def delete(
        self,
        request,
        coupon_id,
    ):

        try:

            instance = Coupon.objects.get(
                pk=coupon_id,
            )

        except Coupon.DoesNotExist:

            raise NotFound(
                detail="Coupon not found.",
            )

        pk = delete_coupon(
            instance,
        )

        logger.info(
            "Admin deleted coupon %s",
            pk,
        )

        return Response(
            {
                "success": True,
                "message": "Coupon deleted successfully",
                "coupon_id": pk,
            },
            status=status.HTTP_200_OK,
        )
