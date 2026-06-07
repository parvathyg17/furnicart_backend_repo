from decimal import Decimal

from django.db.models import (
    ExpressionWrapper,
    F,
    Q,
    Sum,
)
from django.db.models.fields import DecimalField

from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from catalog.models import ProductVariant
from core.pagination import CustomPagination
from core.utils.permissions import IsAdminUserCustom


class AdminVariantStockSerializer(
    serializers.ModelSerializer,
):

    product_id = serializers.IntegerField(
        source="product.id",
        read_only=True,
    )

    product_name = serializers.CharField(
        source="product.name",
        read_only=True,
    )

    class Meta:

        model = ProductVariant

        fields = [
            "id",
            "product_id",
            "product_name",
            "variant_name",
            "color",
            "sku",
            "stock",
            "is_active",
            "price",
        ]


class AdminVariantStockListView(
    APIView,
):

    permission_classes = [
        IsAuthenticated,
        IsAdminUserCustom,
    ]

    LOW_STOCK_THRESHOLD = 10

    def _build_summary(
        self,
    ):

        base = ProductVariant.objects.all()

        value_expr = ExpressionWrapper(
            F(
                "price",
            )
            * F(
                "stock",
            ),
            output_field=DecimalField(
                max_digits=18,
                decimal_places=2,
            ),
        )

        agg = base.aggregate(
            inventory_value=Sum(
                value_expr,
            ),
        )

        total_val = agg[
            "inventory_value"
        ]

        if total_val is None:

            total_val = Decimal(
                "0",
            )

        return {
            "total_skus": base.count(),
            "low_stock_alerts": base.filter(
                stock__lte=self.LOW_STOCK_THRESHOLD,
            ).count(),
            "inventory_value": str(
                total_val.quantize(
                    Decimal(
                        "0.01",
                    ),
                ),
            ),
            "low_stock_threshold": self.LOW_STOCK_THRESHOLD,
        }

    def get(
        self,
        request,
    ):

        queryset = ProductVariant.objects.select_related(
            "product",
        ).all()

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
                    sku__icontains=search,
                )
                | Q(
                    variant_name__icontains=search,
                )
                | Q(
                    product__name__icontains=search,
                ),
            )

        low_only = (
            request.query_params.get(
                "low_stock",
                "",
            )
            or ""
        ).strip().lower() in (
            "1",
            "true",
            "yes",
        )

        if low_only:

            queryset = queryset.filter(
                stock__gt=0,
                stock__lte=self.LOW_STOCK_THRESHOLD,
            )

        ordering_param = (
            request.query_params.get(
                "ordering",
                "",
            )
            or ""
        ).strip()

        allowed_ordering = {
            "-id",
            "id",
            "stock",
            "-stock",
            "sku",
            "-sku",
            "product__name",
            "-product__name",
        }

        if ordering_param not in allowed_ordering:

            ordering_param = "-id"

        queryset = queryset.order_by(
            ordering_param,
        )

        paginator = CustomPagination()

        page = paginator.paginate_queryset(
            queryset,
            request,
            view=self,
        )

        serializer = AdminVariantStockSerializer(
            page,
            many=True,
        )

        summary = self._build_summary()

        if page is not None:

            response = paginator.get_paginated_response(
                serializer.data,
            )

            response.data[
                "summary"
            ] = summary

            return response

        return Response(
            {
                "results": serializer.data,
                "summary": summary,
            },
        )
