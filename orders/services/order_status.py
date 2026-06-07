"""
Derive aggregate ``Order.status`` from ``OrderLine`` rows (fulfillment + cancel).
"""

from django.db import transaction
from django.utils import timezone

from orders.models import Order, OrderLine


def _rollup_bucket(
    line,
):
    """Bucket each line for aggregation (active lines only)."""

    if line.status == OrderLine.LineStatus.CANCELLED:

        return "cancelled_line"

    fs = line.fulfillment_status

    if fs in (
        OrderLine.FulfillmentStatus.DELIVERED,
        OrderLine.FulfillmentStatus.RETURNED,
    ):

        return "done"

    if fs == OrderLine.FulfillmentStatus.OUT_FOR_DELIVERY:

        return "ofd"

    if fs == OrderLine.FulfillmentStatus.SHIPPED:

        return "shipped"

    return "pending"


def compute_derived_order_status(
    order,
):
    """
    Pure function: inspect prefetched or queried ``order.lines``.
    """

    lines = list(
        order.lines.all(),
    )

    active = [
        ln
        for ln in lines
        if ln.status == OrderLine.LineStatus.ACTIVE
    ]

    if not active:

        return Order.Status.CANCELLED

    buckets = [
        _rollup_bucket(
            ln,
        )
        for ln in active
    ]

    has_cancelled_line = any(
        ln.status == OrderLine.LineStatus.CANCELLED
        for ln in lines
    )

    if all(
        b == "done"
        for b in buckets
    ):

        return Order.Status.DELIVERED

    if all(
        b == "ofd"
        for b in buckets
    ):

        return Order.Status.OUT_FOR_DELIVERY

    if all(
        b == "shipped"
        for b in buckets
    ):

        return Order.Status.SHIPPED

    if all(
        b == "pending"
        for b in buckets
    ):

        if has_cancelled_line:

            return Order.Status.PARTIALLY_CANCELLED

        return Order.Status.PENDING

    if any(
        b == "done"
        for b in buckets
    ):

        return Order.Status.PARTIALLY_DELIVERED

    if any(
        b in (
            "ofd",
            "shipped",
        )
        for b in buckets
    ):

        return Order.Status.PARTIALLY_SHIPPED

    return Order.Status.PENDING


@transaction.atomic
def persist_derived_order_status(
    order_id,
):
    """
    Lock order row, recompute status from lines, persist ``status`` and
    container-level cancel timestamps when appropriate.
    """

    order = (
        Order.objects.select_for_update()
        .prefetch_related(
            "lines",
        )
        .get(
            pk=order_id,
        )
    )

    new_status = compute_derived_order_status(
        order,
    )

    update_fields = [
        "status",
    ]

    order.status = new_status

    if new_status == Order.Status.CANCELLED:

        if order.cancelled_at is None:

            order.cancelled_at = timezone.now()

            update_fields.append(
                "cancelled_at",
            )

    else:

        if order.cancelled_at is not None:

            order.cancelled_at = None

            order.cancellation_reason = ""

            update_fields.extend(
                [
                    "cancelled_at",
                    "cancellation_reason",
                ],
            )

    order.save(
        update_fields=list(
            set(
                update_fields + ["updated_at"],
            ),
        ),
    )

    return order
