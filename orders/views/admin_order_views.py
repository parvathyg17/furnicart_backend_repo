from django.db.models import Count, Prefetch, Q

from rest_framework import status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.pagination import CustomPagination
from core.utils.permissions import IsAdminUserCustom

from orders.models import Order, OrderLine, ReturnRequest
from orders.serializers import (
    AdminFulfillmentUpdateSerializer,
    AdminOrderDetailSerializer,
    AdminOrderListSerializer,
    AdminReturnListSerializer,
    AdminReturnStatusSerializer,
    OrderCancelRequestSerializer,
)
from orders.services.admin_order_services import admin_set_order_line_fulfillment
from orders.services.order_services import cancel_entire_order_for_admin
from orders.services.return_services import admin_set_return_request_status


def _validation_error_response(exc):

    if isinstance(exc.detail, dict):

        return Response(
            exc.detail,
            status=status.HTTP_400_BAD_REQUEST,
        )

    if isinstance(exc.detail, list):

        return Response(
            {"detail": exc.detail},
            status=status.HTTP_400_BAD_REQUEST,
        )

    return Response(
        {"detail": str(exc.detail)},
        status=status.HTTP_400_BAD_REQUEST,
    )


class AdminOrderListView(APIView):

    permission_classes = [
        IsAuthenticated,
        IsAdminUserCustom,
    ]

    def get(self, request):

        queryset = Order.objects.select_related(
            "user",
        )

        search = (
            request.query_params.get(
                "search",
                "",
            )
            or ""
        ).strip()

        if search:

            queryset = queryset.filter(
                Q(order_number__icontains=search)
                | Q(user__email__icontains=search)
                | Q(lines__product_name__icontains=search)
                | Q(lines__variant_name__icontains=search)
                | Q(lines__sku__icontains=search),
            ).distinct()

        status_param = (
            request.query_params.get(
                "status",
                "",
            )
            or ""
        ).strip()

        if status_param:

            valid = {c for c, _ in Order.Status.choices}

            if status_param in valid:

                queryset = queryset.filter(
                    status=status_param,
                )

        ordering_param = (
            request.query_params.get(
                "ordering",
                "",
            )
            or ""
        ).strip()

        allowed_ordering = {
            "-placed_at",
            "placed_at",
            "-grand_total",
            "grand_total",
        }

        if ordering_param not in allowed_ordering:

            ordering_param = "-placed_at"

        queryset = (
            queryset.annotate(
                line_count=Count(
                    "lines",
                    distinct=True,
                ),
            )
            .prefetch_related(
                Prefetch(
                    "lines",
                    queryset=OrderLine.objects.order_by(
                        "id",
                    ).only(
                        "id",
                        "product_name",
                        "variant_name",
                        "sku",
                        "quantity",
                        "variant_id",
                        "image_url",
                        "order_id",
                    ),
                ),
            )
            .order_by(
                ordering_param,
            )
        )

        paginator = CustomPagination()

        page = paginator.paginate_queryset(
            queryset,
            request,
            view=self,
        )

        serializer = AdminOrderListSerializer(
            page,
            many=True,
        )

        if page is not None:

            return paginator.get_paginated_response(
                serializer.data,
            )

        return Response(
            serializer.data,
        )


class AdminOrderCancelView(APIView):

    permission_classes = [
        IsAuthenticated,
        IsAdminUserCustom,
    ]

    def post(
        self,
        request,
        order_number,
    ):

        ser = OrderCancelRequestSerializer(
            data=request.data,
        )

        ser.is_valid(
            raise_exception=True,
        )

        try:

            cancel_entire_order_for_admin(
                order_number,
                reason=ser.validated_data.get(
                    "reason",
                ),
            )

        except Order.DoesNotExist:

            raise NotFound(
                detail="Order not found.",
            )

        except ValidationError as exc:

            return _validation_error_response(
                exc,
            )

        order = Order.objects.prefetch_related(
            Prefetch(
                "lines",
                queryset=OrderLine.objects.select_related(
                    "variant",
                ).order_by(
                    "id",
                ),
            ),
        ).get(
            order_number=order_number,
        )

        return Response(
            AdminOrderDetailSerializer(
                order,
            ).data,
        )


class AdminOrderDetailView(APIView):

    permission_classes = [
        IsAuthenticated,
        IsAdminUserCustom,
    ]

    def get(
        self,
        request,
        order_number,
    ):

        try:

            order = (
                Order.objects.select_related(
                    "user",
                )
                .prefetch_related(
                    Prefetch(
                        "lines",
                        queryset=OrderLine.objects.select_related(
                            "variant",
                        ).order_by(
                            "id",
                        ),
                    ),
                )
                .get(
                    order_number=order_number,
                )
            )

        except Order.DoesNotExist:

            raise NotFound(
                detail="Order not found.",
            )

        return Response(
            AdminOrderDetailSerializer(
                order,
            ).data,
        )


class AdminOrderLineFulfillmentView(APIView):

    permission_classes = [
        IsAuthenticated,
        IsAdminUserCustom,
    ]

    def patch(
        self,
        request,
        order_number,
        line_id,
    ):

        ser = AdminFulfillmentUpdateSerializer(
            data=request.data,
        )

        ser.is_valid(
            raise_exception=True,
        )

        try:

            admin_set_order_line_fulfillment(
                order_number=order_number,
                line_id=line_id,
                fulfillment_status=ser.validated_data[
                    "fulfillment_status"
                ],
            )

        except OrderLine.DoesNotExist:

            raise NotFound(
                detail="Order line not found.",
            )

        except ValidationError as exc:

            return _validation_error_response(
                exc,
            )

        order = Order.objects.prefetch_related(
            Prefetch(
                "lines",
                queryset=OrderLine.objects.select_related(
                    "variant",
                ).order_by(
                    "id",
                ),
            ),
        ).get(
            order_number=order_number,
        )

        return Response(
            AdminOrderDetailSerializer(
                order,
            ).data,
        )


class AdminReturnListView(APIView):

    permission_classes = [
        IsAuthenticated,
        IsAdminUserCustom,
    ]

    def get(self, request):

        qs = ReturnRequest.objects.select_related(
            "order_line",
            "order_line__order",
            "user",
        ).order_by(
            "-created_at",
        )

        search = (
            request.query_params.get(
                "search",
                "",
            )
            or ""
        ).strip()

        if search:

            q = (
                Q(
                    order_line__order__order_number__icontains=search,
                )
                | Q(
                    user__email__icontains=search,
                )
                | Q(
                    order_line__product_name__icontains=search,
                )
                | Q(
                    order_line__variant_name__icontains=search,
                )
                | Q(
                    order_line__sku__icontains=search,
                )
                | Q(
                    reason__icontains=search,
                )
            )

            if search.isdigit():

                q = q | Q(
                    pk=int(
                        search,
                    ),
                )

            qs = qs.filter(
                q,
            ).distinct()

        st = (
            request.query_params.get(
                "status",
                "",
            )
            or ""
        ).strip()

        if st:

            valid = {c for c, _ in ReturnRequest.Status.choices}

            if st == "accepted":

                qs = qs.filter(
                    status__in=[
                        ReturnRequest.Status.APPROVED,
                        ReturnRequest.Status.COMPLETED,
                    ],
                )

            elif st in valid:

                qs = qs.filter(
                    status=st,
                )

        paginator = CustomPagination()

        page = paginator.paginate_queryset(
            qs,
            request,
            view=self,
        )

        ser = AdminReturnListSerializer(
            page,
            many=True,
        )

        if page is not None:

            return paginator.get_paginated_response(
                ser.data,
            )

        return Response(
            ser.data,
        )


class AdminReturnDetailView(APIView):

    permission_classes = [
        IsAuthenticated,
        IsAdminUserCustom,
    ]

    def patch(
        self,
        request,
        pk,
    ):

        ser = AdminReturnStatusSerializer(
            data=request.data,
        )

        ser.is_valid(
            raise_exception=True,
        )

        try:

            admin_set_return_request_status(
                return_id=pk,
                new_status=ser.validated_data[
                    "status"
                ],
                admin_note=ser.validated_data.get(
                    "admin_note",
                    "",
                ),
            )

        except ReturnRequest.DoesNotExist:

            raise NotFound(
                detail="Return request not found.",
            )

        except ValidationError as exc:

            return _validation_error_response(
                exc,
            )

        req = ReturnRequest.objects.select_related(
            "order_line",
            "order_line__order",
            "user",
        ).get(
            pk=pk,
        )

        return Response(
            AdminReturnListSerializer(
                req,
            ).data,
        )
