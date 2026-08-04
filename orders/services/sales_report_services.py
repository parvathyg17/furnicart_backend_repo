from datetime import date, datetime, timedelta
from decimal import Decimal

from django.db.models import Count, DecimalField, Q, Sum, Value
from django.db.models.functions import Coalesce, TruncDate, TruncMonth
from django.utils import timezone

from orders.models import Order, OrderLine


def _quantize_money(
    value,
):

    return Decimal(
        value or "0.00",
    ).quantize(
        Decimal(
            "0.01",
        ),
    )


def _parse_date_param(
    raw,
    *,
    field_name,
):

    if not raw:

        return None

    cleaned = str(
        raw,
    ).strip()

    if not cleaned:

        return None

    try:

        if (
            len(
                cleaned,
            )
            == 10
        ):

            return date.fromisoformat(
                cleaned,
            )

        parsed = datetime.fromisoformat(
            cleaned.replace(
                "Z",
                "+00:00",
            ),
        )

        if timezone.is_aware(
            parsed,
        ):

            return timezone.localdate(
                parsed,
            )

        return parsed.date()

    except ValueError as exc:

        raise ValueError(
            f"Invalid {field_name}. Use YYYY-MM-DD.",
        ) from exc


def resolve_sales_report_date_range(
    period,
    *,
    date_from_raw=None,
    date_to_raw=None,
):

    period = (
        str(
            period or "weekly",
        )
        .strip()
        .lower()
    )

    today = timezone.localdate()

    if period == "daily":

        return today, today, period

    if period == "weekly":

        return (
            today
            - timedelta(
                days=6,
            ),
            today,
            period,
        )

    if period == "yearly":

        return (
            today.replace(
                month=1,
                day=1,
            ),
            today,
            period,
        )

    if period == "custom":

        date_from = _parse_date_param(
            date_from_raw,
            field_name="date_from",
        )

        date_to = _parse_date_param(
            date_to_raw,
            field_name="date_to",
        )

        if date_from is None or date_to is None:

            raise ValueError(
                "date_from and date_to are required for custom reports.",
            )

        if date_to < date_from:

            raise ValueError(
                "date_to must be on or after date_from.",
            )

        return date_from, date_to, period

    raise ValueError(
        "period must be one of: daily, weekly, yearly, custom.",
    )


def sales_report_base_queryset(
    date_from,
    date_to,
):

    start_dt = timezone.make_aware(
        datetime.combine(
            date_from,
            datetime.min.time(),
        ),
    )

    end_dt = timezone.make_aware(
        datetime.combine(
            date_to,
            datetime.max.time(),
        ),
    )

    return (
        Order.objects.filter(
            placed_at__gte=start_dt,
            placed_at__lte=end_dt,
        )
        .exclude(
            status=Order.Status.CANCELLED,
        )
        .select_related(
            "user",
        )
    )


def annotate_offer_discount(
    queryset,
):

    return queryset.annotate(
        offer_discount_total=Coalesce(
            Sum(
                "lines__discount_amount",
                filter=Q(
                    lines__status=OrderLine.LineStatus.ACTIVE,
                ),
            ),
            Value(
                Decimal(
                    "0.00",
                ),
            ),
            output_field=DecimalField(
                max_digits=12,
                decimal_places=2,
            ),
        ),
    )


def _zero_decimal_value():

    return Value(
        Decimal(
            "0.00",
        ),
        output_field=DecimalField(
            max_digits=12,
            decimal_places=2,
        ),
    )


def _sum_active_line_offer_discount(
    queryset,
):

    result = OrderLine.objects.filter(
        order__in=queryset,
        status=OrderLine.LineStatus.ACTIVE,
    ).aggregate(
        total=Coalesce(
            Sum(
                "discount_amount",
            ),
            _zero_decimal_value(),
        ),
    )

    return _quantize_money(
        result.get(
            "total",
        ),
    )


def _offer_discount_by_bucket(
    queryset,
    *,
    granularity,
):

    line_qs = OrderLine.objects.filter(
        order__in=queryset,
        status=OrderLine.LineStatus.ACTIVE,
    )

    if granularity == "month":

        grouped = line_qs.annotate(
            bucket=TruncMonth(
                "order__placed_at",
            ),
        )

    else:

        grouped = line_qs.annotate(
            bucket=TruncDate(
                "order__placed_at",
            ),
        )

    rows = grouped.values(
        "bucket",
    ).annotate(
        offer_discount_sum=Coalesce(
            Sum(
                "discount_amount",
            ),
            _zero_decimal_value(),
        ),
    )

    mapping = {}

    for row in rows:

        bucket = row["bucket"]

        if bucket is None:

            continue

        if hasattr(
            bucket,
            "date",
        ):

            bucket_date = bucket.date()

        else:

            bucket_date = bucket

        mapping[bucket_date.isoformat()] = _quantize_money(
            row["offer_discount_sum"],
        )

    return mapping


def _summary_from_aggregates(
    agg,
):

    subtotal = _quantize_money(
        agg.get(
            "subtotal_sum",
        ),
    )

    offer_discount = _quantize_money(
        agg.get(
            "offer_discount_sum",
        ),
    )

    coupon_discount = _quantize_money(
        agg.get(
            "coupon_discount_sum",
        ),
    )

    tax_total = _quantize_money(
        agg.get(
            "tax_sum",
        ),
    )

    shipping_total = _quantize_money(
        agg.get(
            "shipping_sum",
        ),
    )

    grand_total = _quantize_money(
        agg.get(
            "grand_total_sum",
        ),
    )

    subtotal_gross = _quantize_money(
        subtotal + offer_discount,
    )

    total_discount = _quantize_money(
        offer_discount + coupon_discount,
    )

    return {
        "order_count": int(
            agg.get(
                "order_count",
            )
            or 0,
        ),
        "subtotal_gross": subtotal_gross,
        "offer_discount_total": offer_discount,
        "subtotal": subtotal,
        "coupon_discount_total": coupon_discount,
        "total_discount": total_discount,
        "tax_total": tax_total,
        "shipping_total": shipping_total,
        "grand_total": grand_total,
    }


def _serialize_summary(
    summary,
):

    return {
        key: (
            str(
                value,
            )
            if isinstance(
                value,
                Decimal,
            )
            else value
        )
        for key, value in summary.items()
    }


def _breakdown_granularity(
    period,
    date_from,
    date_to,
):

    span_days = (date_to - date_from).days + 1

    if period == "yearly":

        return "month"

    if period == "weekly" or span_days <= 31:

        return "day"

    if span_days <= 366:

        return "month"

    return "month"


def _aggregate_breakdown(
    queryset,
    *,
    granularity,
    return_deductions_by_bucket=None,
):

    if granularity == "month":

        grouped = queryset.annotate(
            bucket=TruncMonth(
                "placed_at",
            ),
        )

        label_fmt = "%Y-%m"

    else:

        grouped = queryset.annotate(
            bucket=TruncDate(
                "placed_at",
            ),
        )

        label_fmt = "%Y-%m-%d"

    rows = (
        grouped.values(
            "bucket",
        )
        .annotate(
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
        .order_by(
            "bucket",
        )
    )

    offer_by_bucket = _offer_discount_by_bucket(
        queryset,
        granularity=granularity,
    )

    breakdown = []

    for row in rows:

        bucket = row["bucket"]

        if bucket is None:

            continue

        if hasattr(
            bucket,
            "date",
        ):

            bucket_date = bucket.date()

        else:

            bucket_date = bucket

        row["offer_discount_sum"] = offer_by_bucket.get(
            bucket_date.isoformat(),
            Decimal(
                "0.00",
            ),
        )

        if return_deductions_by_bucket:
            bucket_deductions = return_deductions_by_bucket.get(
                bucket_date.isoformat(),
                {},
            )
            if bucket_deductions:
                row["subtotal_sum"] -= bucket_deductions.get(
                    "subtotal_sum", Decimal("0.00")
                )
                row["coupon_discount_sum"] -= bucket_deductions.get(
                    "coupon_discount_sum", Decimal("0.00")
                )
                row["tax_sum"] -= bucket_deductions.get("tax_sum", Decimal("0.00"))
                row["grand_total_sum"] -= bucket_deductions.get(
                    "grand_total_sum", Decimal("0.00")
                )
                row["offer_discount_sum"] -= bucket_deductions.get(
                    "offer_discount_sum", Decimal("0.00")
                )

        summary = _summary_from_aggregates(
            row,
        )

        breakdown.append(
            {
                "label": bucket_date.strftime(
                    label_fmt,
                ),
                "date": bucket_date.isoformat(),
                **_serialize_summary(
                    summary,
                ),
            },
        )

    return breakdown


def _calculate_returns_deductions(
    queryset,
    granularity,
):

    from decimal import ROUND_HALF_UP, Decimal

    from django.utils import timezone

    from orders.services.refund_reporting import (CENTS, _gst_rate,
                                                  _order_original_coupon,
                                                  _order_original_subtotal)

    orders_with_returns = (
        queryset.filter(
            lines__returned_quantity__gt=0,
        )
        .prefetch_related(
            "lines",
        )
        .distinct()
    )

    total_deductions = {
        "subtotal_sum": Decimal("0.00"),
        "offer_discount_sum": Decimal("0.00"),
        "coupon_discount_sum": Decimal("0.00"),
        "tax_sum": Decimal("0.00"),
        "grand_total_sum": Decimal("0.00"),
    }

    by_bucket = {}

    gst = _gst_rate()

    for order in orders_with_returns:
        dt = timezone.localtime(order.placed_at).date()
        if granularity == "month":
            dt = dt.replace(day=1)

        bucket_key = dt.isoformat()

        if bucket_key not in by_bucket:
            by_bucket[bucket_key] = {
                "subtotal_sum": Decimal("0.00"),
                "offer_discount_sum": Decimal("0.00"),
                "coupon_discount_sum": Decimal("0.00"),
                "tax_sum": Decimal("0.00"),
                "grand_total_sum": Decimal("0.00"),
            }

        lines = list(order.lines.all())
        original_subtotal = _order_original_subtotal(order, lines)
        original_coupon = _order_original_coupon(order, original_subtotal)

        allocated_coupon = Decimal("0.00")
        count = len(lines)

        for idx, ln in enumerate(lines):
            line_total = Decimal(str(ln.line_total)).quantize(CENTS)

            if original_subtotal > Decimal("0.00") and original_coupon > Decimal(
                "0.00"
            ):
                if idx == count - 1:
                    coupon_share = (original_coupon - allocated_coupon).quantize(CENTS)
                else:
                    coupon_share = (
                        original_coupon * line_total / original_subtotal
                    ).quantize(CENTS)
                    allocated_coupon += coupon_share
            else:
                coupon_share = Decimal("0.00")

            tax_share = (line_total * gst).quantize(CENTS, rounding=ROUND_HALF_UP)

            if ln.returned_quantity > 0:
                ratio = Decimal(ln.returned_quantity) / Decimal(ln.quantity)

                ret_subtotal = (line_total * ratio).quantize(CENTS)
                ret_offer = (Decimal(str(ln.discount_amount)) * ratio).quantize(CENTS)
                ret_coupon = (coupon_share * ratio).quantize(CENTS)
                ret_tax = (tax_share * ratio).quantize(CENTS, rounding=ROUND_HALF_UP)

                ret_grand = ret_subtotal + ret_tax - ret_coupon
                if ret_grand < Decimal("0.00"):
                    ret_grand = Decimal("0.00")

                total_deductions["subtotal_sum"] += ret_subtotal
                total_deductions["offer_discount_sum"] += ret_offer
                total_deductions["coupon_discount_sum"] += ret_coupon
                total_deductions["tax_sum"] += ret_tax
                total_deductions["grand_total_sum"] += ret_grand

                by_bucket[bucket_key]["subtotal_sum"] += ret_subtotal
                by_bucket[bucket_key]["offer_discount_sum"] += ret_offer
                by_bucket[bucket_key]["coupon_discount_sum"] += ret_coupon
                by_bucket[bucket_key]["tax_sum"] += ret_tax
                by_bucket[bucket_key]["grand_total_sum"] += ret_grand

    return total_deductions, by_bucket


def build_sales_report_payload(
    *,
    period,
    date_from_raw=None,
    date_to_raw=None,
):

    date_from, date_to, normalized_period = resolve_sales_report_date_range(
        period,
        date_from_raw=date_from_raw,
        date_to_raw=date_to_raw,
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

    agg["offer_discount_sum"] = _sum_active_line_offer_discount(
        queryset,
    )

    annotated = annotate_offer_discount(
        queryset,
    )

    granularity = _breakdown_granularity(
        normalized_period,
        date_from,
        date_to,
    )

    total_deductions, by_bucket = _calculate_returns_deductions(
        queryset,
        granularity,
    )

    agg["subtotal_sum"] -= total_deductions["subtotal_sum"]
    agg["coupon_discount_sum"] -= total_deductions["coupon_discount_sum"]
    agg["tax_sum"] -= total_deductions["tax_sum"]
    agg["grand_total_sum"] -= total_deductions["grand_total_sum"]
    agg["offer_discount_sum"] -= total_deductions["offer_discount_sum"]

    summary = _serialize_summary(
        _summary_from_aggregates(
            agg,
        ),
    )

    breakdown = _aggregate_breakdown(
        queryset,
        granularity=granularity,
        return_deductions_by_bucket=by_bucket,
    )

    return {
        "period": normalized_period,
        "date_from": date_from.isoformat(),
        "date_to": date_to.isoformat(),
        "breakdown_granularity": granularity,
        "summary": summary,
        "breakdown": breakdown,
        "orders_queryset": annotated.prefetch_related(
            "lines",
        ).order_by(
            "-placed_at",
        ),
    }


def serialize_sales_report_order(
    order,
):

    from decimal import ROUND_HALF_UP, Decimal

    from orders.services.refund_reporting import (CENTS, _gst_rate,
                                                  _order_original_coupon,
                                                  _order_original_subtotal)

    subtotal = order.subtotal
    tax_total = order.tax_total
    discount_total = order.discount_total
    offer_discount = getattr(
        order,
        "offer_discount_total",
        Decimal(
            "0.00",
        ),
    )
    grand_total = order.grand_total

    has_returns = any(ln.returned_quantity > 0 for ln in order.lines.all())

    if has_returns:
        lines = list(order.lines.all())
        original_subtotal = _order_original_subtotal(order, lines)
        original_coupon = _order_original_coupon(order, original_subtotal)
        allocated_coupon = Decimal("0.00")
        count = len(lines)
        gst = _gst_rate()

        for idx, ln in enumerate(lines):
            line_total = Decimal(str(ln.line_total)).quantize(CENTS)

            if original_subtotal > Decimal("0.00") and original_coupon > Decimal(
                "0.00"
            ):
                if idx == count - 1:
                    coupon_share = (original_coupon - allocated_coupon).quantize(CENTS)
                else:
                    coupon_share = (
                        original_coupon * line_total / original_subtotal
                    ).quantize(CENTS)
                    allocated_coupon += coupon_share
            else:
                coupon_share = Decimal("0.00")

            tax_share = (line_total * gst).quantize(CENTS, rounding=ROUND_HALF_UP)

            if ln.returned_quantity > 0:
                ratio = Decimal(ln.returned_quantity) / Decimal(ln.quantity)

                ret_subtotal = (line_total * ratio).quantize(CENTS)
                ret_offer = (Decimal(str(ln.discount_amount)) * ratio).quantize(CENTS)
                ret_coupon = (coupon_share * ratio).quantize(CENTS)
                ret_tax = (tax_share * ratio).quantize(CENTS, rounding=ROUND_HALF_UP)

                ret_grand = ret_subtotal + ret_tax - ret_coupon
                if ret_grand < Decimal("0.00"):
                    ret_grand = Decimal("0.00")

                subtotal -= ret_subtotal
                offer_discount -= ret_offer
                discount_total -= ret_coupon
                tax_total -= ret_tax
                grand_total -= ret_grand

    offer_discount = _quantize_money(
        offer_discount,
    )

    subtotal = _quantize_money(
        subtotal,
    )

    return {
        "id": order.id,
        "order_number": order.order_number,
        "placed_at": order.placed_at.isoformat(),
        "status": order.status,
        "payment_method": order.payment_method,
        "payment_status": order.payment_status,
        "customer_email": order.user.email,
        "subtotal_gross": str(
            _quantize_money(
                subtotal + offer_discount,
            ),
        ),
        "offer_discount_total": str(
            offer_discount,
        ),
        "subtotal": str(
            subtotal,
        ),
        "coupon_discount_total": str(
            _quantize_money(
                discount_total,
            ),
        ),
        "total_discount": str(
            _quantize_money(
                offer_discount + discount_total,
            ),
        ),
        "tax_total": str(
            _quantize_money(
                tax_total,
            ),
        ),
        "shipping_total": str(
            _quantize_money(
                order.shipping_total,
            ),
        ),
        "grand_total": str(
            _quantize_money(
                grand_total,
            ),
        ),
        "coupon_code": order.coupon_code or "",
    }


def build_sales_report_for_export(
    *,
    period,
    date_from_raw=None,
    date_to_raw=None,
    max_orders=5000,
):

    payload = build_sales_report_payload(
        period=period,
        date_from_raw=date_from_raw,
        date_to_raw=date_to_raw,
    )

    orders_qs = payload.pop(
        "orders_queryset",
    )

    payload["orders"] = [
        serialize_sales_report_order(
            order,
        )
        for order in orders_qs[:max_orders]
    ]

    return payload


def load_report_for_export(
    request,
):

    from rest_framework.exceptions import ValidationError

    period = (
        request.query_params.get(
            "period",
            "weekly",
        )
        or "weekly"
    )

    date_from = request.query_params.get(
        "date_from",
    )

    date_to = request.query_params.get(
        "date_to",
    )

    try:

        return build_sales_report_for_export(
            period=period,
            date_from_raw=date_from,
            date_to_raw=date_to,
        )

    except ValueError as exc:

        raise ValidationError(
            {
                "detail": str(
                    exc,
                ),
            },
        ) from exc
