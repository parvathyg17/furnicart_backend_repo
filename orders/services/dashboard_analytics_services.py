from datetime import timedelta
from decimal import Decimal

from django.db.models import (
    Count,
    Sum,
    Value,
)
from django.db.models.functions import Coalesce
from django.utils import timezone

from accounts.models.users import User
from orders.models import OrderLine
from orders.services.sales_report_services import (
    _aggregate_breakdown,
    _breakdown_granularity,
    _serialize_summary,
    _sum_active_line_offer_discount,
    _summary_from_aggregates,
    _zero_decimal_value,
    sales_report_base_queryset,
)


def resolve_chart_date_range(
    chart_period,
):
    

    chart_period = (
        str(
            chart_period or "monthly",
        )
        .strip()
        .lower()
    )

    today = timezone.localdate()

    if chart_period == "weekly":

        return (
            today - timedelta(
                days=6,
            ),
            today,
            chart_period,
        )

    if chart_period == "yearly":

        return (
            today.replace(
                month=1,
                day=1,
            ),
            today,
            chart_period,
        )

    
    return (
        today - timedelta(
            days=29,
        ),
        today,
        "monthly",
    )


def _top_selling_products(
    queryset,
    *,
    limit=10,
):

    rows = (
        OrderLine.objects.filter(
            order__in=queryset,
            status=OrderLine.LineStatus.ACTIVE,
        )
        .values(
            "variant__product_id",
            "product_name",
        )
        .annotate(
            quantity_sold=Coalesce(
                Sum(
                    "quantity",
                ),
                Value(
                    0,
                ),
            ),
            revenue=Coalesce(
                Sum(
                    "line_total",
                ),
                _zero_decimal_value(),
            ),
        )
        .order_by(
            "-revenue",
        )[
            :limit
        ]
    )

    return [
        {
            "id": row[
                "variant__product_id"
            ],
            "name": row[
                "product_name"
            ],
            "quantity_sold": int(
                row[
                    "quantity_sold"
                ]
                or 0,
            ),
            "revenue": str(
                Decimal(
                    row[
                        "revenue"
                    ]
                    or "0.00",
                ).quantize(
                    Decimal(
                        "0.01",
                    ),
                ),
            ),
        }
        for row in rows
    ]


def _top_selling_categories(
    queryset,
    *,
    limit=10,
):

    rows = (
        OrderLine.objects.filter(
            order__in=queryset,
            status=OrderLine.LineStatus.ACTIVE,
        )
        .values(
            "variant__product__category_id",
            "variant__product__category__name",
        )
        .annotate(
            quantity_sold=Coalesce(
                Sum(
                    "quantity",
                ),
                Value(
                    0,
                ),
            ),
            revenue=Coalesce(
                Sum(
                    "line_total",
                ),
                _zero_decimal_value(),
            ),
        )
        .order_by(
            "-revenue",
        )[
            :limit
        ]
    )

    return [
        {
            "id": row[
                "variant__product__category_id"
            ],
            "name": row[
                "variant__product__category__name"
            ]
            or "Uncategorized",
            "quantity_sold": int(
                row[
                    "quantity_sold"
                ]
                or 0,
            ),
            "revenue": str(
                Decimal(
                    row[
                        "revenue"
                    ]
                    or "0.00",
                ).quantize(
                    Decimal(
                        "0.01",
                    ),
                ),
            ),
        }
        for row in rows
        if row[
            "variant__product__category_id"
        ]
    ]


def _top_selling_brands(
    queryset,
    *,
    limit=10,
):

    rows = (
        OrderLine.objects.filter(
            order__in=queryset,
            status=OrderLine.LineStatus.ACTIVE,
            variant__product__brand__isnull=False,
        )
        .exclude(
            variant__product__brand="",
        )
        .values(
            "variant__product__brand",
        )
        .annotate(
            quantity_sold=Coalesce(
                Sum(
                    "quantity",
                ),
                Value(
                    0,
                ),
            ),
            revenue=Coalesce(
                Sum(
                    "line_total",
                ),
                _zero_decimal_value(),
            ),
        )
        .order_by(
            "-revenue",
        )[
            :limit
        ]
    )

    return [
        {
            "name": row[
                "variant__product__brand"
            ],
            "quantity_sold": int(
                row[
                    "quantity_sold"
                ]
                or 0,
            ),
            "revenue": str(
                Decimal(
                    row[
                        "revenue"
                    ]
                    or "0.00",
                ).quantize(
                    Decimal(
                        "0.01",
                    ),
                ),
            ),
        }
        for row in rows
    ]


def build_dashboard_analytics(
    *,
    chart_period="monthly",
):

    date_from, date_to, normalized_period = (
        resolve_chart_date_range(
            chart_period,
        )
    )

    queryset = sales_report_base_queryset(
        date_from,
        date_to,
    )

    agg = queryset.aggregate(
        order_count=Count(
            "id",
            distinct=True,
        ),
        subtotal_sum=Coalesce(
            Sum(
                "subtotal",
            ),
            _zero_decimal_value(),
        ),
        coupon_discount_sum=Coalesce(
            Sum(
                "discount_total",
            ),
            _zero_decimal_value(),
        ),
        tax_sum=Coalesce(
            Sum(
                "tax_total",
            ),
            _zero_decimal_value(),
        ),
        shipping_sum=Coalesce(
            Sum(
                "shipping_total",
            ),
            _zero_decimal_value(),
        ),
        grand_total_sum=Coalesce(
            Sum(
                "grand_total",
            ),
            _zero_decimal_value(),
        ),
    )

    agg[
        "offer_discount_sum"
    ] = _sum_active_line_offer_discount(
        queryset,
    )

    sales_summary = _serialize_summary(
        _summary_from_aggregates(
            agg,
        ),
    )

    granularity = _breakdown_granularity(
        "yearly"
        if normalized_period == "yearly"
        else "weekly",
        date_from,
        date_to,
    )

    if normalized_period == "monthly":

        granularity = "day"

    breakdown = _aggregate_breakdown(
        queryset,
        granularity=granularity,
    )

    total_users = User.objects.count()

    active_users = User.objects.filter(
        is_active=True,
    ).count()

    blocked_users = User.objects.filter(
        is_active=False,
    ).count()

    return {
        "chart_period": normalized_period,
        "date_from": date_from.isoformat(),
        "date_to": date_to.isoformat(),
        "breakdown_granularity": granularity,
        "user_stats": {
            "total_users": total_users,
            "active_users": active_users,
            "blocked_users": blocked_users,
        },
        "sales_summary": sales_summary,
        "sales_chart": breakdown,
        "top_products": _top_selling_products(
            queryset,
        ),
        "top_categories": _top_selling_categories(
            queryset,
        ),
        "top_brands": _top_selling_brands(
            queryset,
        ),
    }
