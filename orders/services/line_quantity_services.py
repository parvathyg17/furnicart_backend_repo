from decimal import ROUND_HALF_UP, Decimal

from django.db.models import Sum

from orders.models import OrderLine, ReturnRequest

CENTS = Decimal(
    "0.01",
)


def _q(
    value,
):

    return Decimal(
        str(
            value or "0",
        ),
    ).quantize(
        CENTS,
    )


def active_quantity(
    line,
):
    """Units still part of the order (not cancelled or returned)."""

    return max(
        0,
        int(
            line.quantity,
        )
        - int(
            line.cancelled_quantity,
        )
        - int(
            line.returned_quantity,
        ),
    )


def cancellable_quantity(
    line,
):
    """Units that can still be cancelled before shipping."""

    return max(
        0,
        int(
            line.quantity,
        )
        - int(
            line.cancelled_quantity,
        ),
    )


def deliverable_quantity(
    line,
):
    """Units that were ordered minus pre-ship cancellations."""

    return max(
        0,
        int(
            line.quantity,
        )
        - int(
            line.cancelled_quantity,
        ),
    )


def _in_flight_return_quantity(
    line,
):

    agg = ReturnRequest.objects.filter(
        order_line=line,
        status__in=(
            ReturnRequest.Status.PENDING,
            ReturnRequest.Status.APPROVED,
        ),
    ).aggregate(
        s=Sum(
            "quantity",
        ),
    )

    return int(
        agg.get(
            "s",
        )
        or 0,
    )


def returnable_quantity(
    line,
):
    """Units eligible for a new return request."""

    if _in_flight_return_quantity(
        line,
    ) > 0:

        return 0

    remaining = (
        deliverable_quantity(
            line,
        )
        - int(
            line.returned_quantity,
        )
    )

    return max(
        0,
        remaining,
    )


def proportional_amount(
    total,
    qty,
    line_quantity,
):
    """Split a line-level decimal across ``qty`` of ``line_quantity`` units."""

    total = _q(
        total,
    )

    line_quantity = int(
        line_quantity,
    )

    qty = int(
        qty,
    )

    if (
        qty <= 0
        or line_quantity <= 0
    ):

        return Decimal(
            "0.00",
        )

    if qty >= line_quantity:

        return total

    return _q(
        total * Decimal(
            qty,
        ) / Decimal(
            line_quantity,
        ),
    )


def active_line_subtotal(
    line,
):
    """Remaining merchandise value for non-cancelled units on a line."""

    active_qty = int(
        line.quantity,
    ) - int(
        line.cancelled_quantity,
    )

    if active_qty <= 0:

        return Decimal(
            "0.00",
        )

    return proportional_amount(
        line.line_total,
        active_qty,
        line.quantity,
    )


def line_paid_amount_for_qty(
    order,
    line,
    qty,
):
    from orders.services.refund_reporting import line_paid_amount

    full = line_paid_amount(
        order,
        line,
    )

    return proportional_amount(
        full,
        qty,
        line.quantity,
    )


def validate_cancel_quantity(
    line,
    quantity,
):

    if quantity is None:

        quantity = cancellable_quantity(
            line,
        )

    quantity = int(
        quantity,
    )

    max_qty = cancellable_quantity(
        line,
    )

    if quantity < 1:

        raise ValueError(
            "Quantity must be at least 1.",
        )

    if quantity > max_qty:

        raise ValueError(
            f"You can cancel at most {max_qty} unit(s) for this item.",
        )

    return quantity


def validate_return_quantity(
    line,
    quantity,
):

    if quantity is None:

        quantity = returnable_quantity(
            line,
        )

    quantity = int(
        quantity,
    )

    max_qty = returnable_quantity(
        line,
    )

    if quantity < 1:

        raise ValueError(
            "Quantity must be at least 1.",
        )

    if quantity > max_qty:

        raise ValueError(
            f"You can return at most {max_qty} unit(s) for this item.",
        )

    return quantity
