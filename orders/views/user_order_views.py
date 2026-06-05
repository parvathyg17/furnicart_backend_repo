from django.db.models import Count, Prefetch, Q

from django.http import HttpResponse

from rest_framework import status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.pagination import CustomPagination

from orders.models import Order, OrderLine
from orders.serializers import (
    OrderCancelRequestSerializer,
    OrderCreateSerializer,
    OrderDetailSerializer,
    OrderListSerializer,
)
from orders.services.invoice_pdf import build_order_invoice_pdf
from orders.services.order_services import (
    cancel_entire_order_for_user,
    cancel_order_line_for_user,
    create_order_from_cart,
    get_order_for_user,
)


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


class OrderCreateView(APIView):

    permission_classes = [IsAuthenticated]

    def get(
        self,
        request,
    ):

        queryset = Order.objects.filter(
            user=request.user,
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
                Q(
                    order_number__icontains=search,
                )
                | Q(
                    lines__product_name__icontains=search,
                )
                | Q(
                    lines__variant_name__icontains=search,
                ),
            ).distinct()

        status_param = (
            request.query_params.get(
                "status",
                "",
            )
            or ""
        ).strip()

        if status_param:

            valid_statuses = {
                v
                for v, _ in Order.Status.choices
            }

            if status_param in valid_statuses:

                queryset = queryset.filter(
                    status=status_param,
                )

        queryset = (
            queryset.annotate(
                line_count=Count(
                    "lines",
                    distinct=True,
                ),
            )
            .order_by(
                "-placed_at",
            )
            .prefetch_related(
                Prefetch(
                    "lines",
                    queryset=OrderLine.objects.order_by(
                        "id",
                    ),
                ),
            )
        )

        paginator = CustomPagination()

        page = paginator.paginate_queryset(
            queryset,
            request,
            view=self,
        )

        if page is not None:

            serializer = OrderListSerializer(
                page,
                many=True,
            )

            return paginator.get_paginated_response(
                serializer.data,
            )

        serializer = OrderListSerializer(
            queryset,
            many=True,
        )

        return Response(
            serializer.data,
        )

    def post(self, request):

        serializer = OrderCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:

            order = create_order_from_cart(
                request.user,
                data["address_id"],
                payment_method=data.get(
                    "payment_method",
                ),
            )

        except ValidationError as exc:

            return _validation_error_response(exc)

        return Response(
            OrderDetailSerializer(order).data,
            status=status.HTTP_201_CREATED,
        )


class OrderDetailView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request, order_number):

        try:

            order = get_order_for_user(
                request.user,
                order_number,
            )

        except Order.DoesNotExist:

            raise NotFound(detail="Order not found.")

        return Response(OrderDetailSerializer(order).data)


class OrderCancelView(APIView):

    permission_classes = [IsAuthenticated]

    def post(
        self,
        request,
        order_number,
    ):

        serializer = OrderCancelRequestSerializer(
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        try:

            cancel_entire_order_for_user(
                request.user,
                order_number,
                reason=serializer.validated_data.get(
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

        order = get_order_for_user(
            request.user,
            order_number,
        )

        return Response(
            OrderDetailSerializer(
                order,
            ).data,
        )


class OrderLineCancelView(APIView):

    permission_classes = [IsAuthenticated]

    def post(
        self,
        request,
        order_number,
        line_id,
    ):

        serializer = OrderCancelRequestSerializer(
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        try:

            cancel_order_line_for_user(
                request.user,
                order_number,
                line_id,
                reason=serializer.validated_data.get(
                    "reason",
                ),
            )

        except Order.DoesNotExist:

            raise NotFound(
                detail="Order not found.",
            )

        except OrderLine.DoesNotExist:

            raise NotFound(
                detail="Order line not found.",
            )

        except ValidationError as exc:

            return _validation_error_response(
                exc,
            )

        order = get_order_for_user(
            request.user,
            order_number,
        )

        return Response(
            OrderDetailSerializer(
                order,
            ).data,
        )


class OrderInvoicePdfView(APIView):

    permission_classes = [IsAuthenticated]

    def get(
        self,
        request,
        order_number,
    ):

        try:

            order = get_order_for_user(
                request.user,
                order_number,
            )

        except Order.DoesNotExist:

            raise NotFound(detail="Order not found.")

        pdf_bytes = build_order_invoice_pdf(
            order,
        )

        safe_name = "".join(
            c if c.isalnum() or c in "-._" else "_"
            for c in order.order_number
        )

        filename = f"FurniCart-invoice-{safe_name}.pdf"

        response = HttpResponse(
            pdf_bytes,
            content_type="application/pdf",
        )

        response["Content-Disposition"] = (
            f'attachment; filename="{filename}"'
        )

        return response
