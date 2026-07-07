import re
from decimal import ROUND_HALF_UP, Decimal

from django.conf import settings

from accounts.models.wallet import WalletTransaction
from orders.models import Order, OrderLine, ReturnRequest

CENTS = Decimal(
    "0.01",
)

_LINE_NOTE_RE = re.compile(
    r"line #(\d+)",
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


def _gst_rate():

    raw = getattr(
        settings,
        "CHECKOUT_GST_RATE",
        "0.18",
    )

    if isinstance(
        raw,
        Decimal,
    ):

        return raw

    return Decimal(
        str(
            raw,
        ),
    )


def _order_original_subtotal(
    order,
    lines=None,
):

    if lines is None:

        lines = order.lines.all()

    total = Decimal(
        "0.00",
    )

    for ln in lines:

        total += _q(
            ln.line_total,
        )

    return _q(
        total,
    )


def _order_original_coupon(
    order,
    original_subtotal,
):

    if order.applied_coupon_id and original_subtotal > Decimal(
        "0.00",
    ):

        from promotions.services.coupon_validation import \
            compute_coupon_discount_amount

        return _q(
            compute_coupon_discount_amount(
                order.applied_coupon,
                original_subtotal,
            ),
        )

    return _q(
        order.discount_total,
    )


def line_coupon_share(
    order,
    line,
    *,
    original_subtotal=None,
    original_coupon=None,
):
    

    if original_subtotal is None:

        original_subtotal = _order_original_subtotal(
            order,
        )

    if original_subtotal <= Decimal(
        "0.00",
    ):

        return Decimal(
            "0.00",
        )

    if original_coupon is None:

        original_coupon = _order_original_coupon(
            order,
            original_subtotal,
        )

    if original_coupon <= Decimal(
        "0.00",
    ):

        return Decimal(
            "0.00",
        )

    return _q(
        original_coupon * _q(
            line.line_total,
        ) / original_subtotal,
    )


def proportional_coupon_for_subtotal(
    order,
    active_subtotal,
    *,
    lines=None,
):
    

    active_subtotal = _q(
        active_subtotal,
    )

    if lines is None:

        lines = order.lines.all()

    original_subtotal = _order_original_subtotal(
        order,
        lines,
    )

    original_coupon = _order_original_coupon(
        order,
        original_subtotal,
    )

    if (
        original_subtotal <= Decimal(
            "0.00",
        )
        or original_coupon <= Decimal(
            "0.00",
        )
        or active_subtotal <= Decimal(
            "0.00",
        )
    ):

        return Decimal(
            "0.00",
        )

    return _q(
        original_coupon * active_subtotal / original_subtotal,
    )


def line_paid_amount(
    order,
    line,
):
    

    line_total = _q(
        line.line_total,
    )

    coupon_share = line_coupon_share(
        order,
        line,
    )

    tax_share = (line_total * _gst_rate()).quantize(
        CENTS,
        rounding=ROUND_HALF_UP,
    )

    amount = _q(
        line_total + tax_share - coupon_share,
    )

    if amount < Decimal(
        "0.00",
    ):

        return Decimal(
            "0.00",
        )

    return amount


def _distribute_unattributed_cancel(
    lines,
    unattributed_cancel,
    line_refund,
):
    

    result = {}

    if unattributed_cancel <= Decimal(
        "0.00",
    ):

        return result

    pool = [
        ln
        for ln in lines
        if ln.status == OrderLine.LineStatus.CANCELLED
        and ln.id not in line_refund
    ]

    base = Decimal(
        "0.00",
    )

    for ln in pool:

        base += _q(
            ln.line_total,
        )

    if base <= Decimal(
        "0.00",
    ):

        return result

    allocated = Decimal(
        "0.00",
    )

    last = len(
        pool,
    ) - 1

    for idx, ln in enumerate(
        pool,
    ):

        if idx == last:

            share = _q(
                unattributed_cancel - allocated,
            )

        else:

            share = _q(
                unattributed_cancel * _q(
                    ln.line_total,
                ) / base,
            )

            allocated += share

        result[ln.id] = share

    return result


def _apply_cod_return_pickup_refunds(
    order,
    lines,
    line_refund,
    return_total,
    txn_rows,
):
    

    if order.payment_method != Order.PaymentMethod.COD:

        return return_total, txn_rows

    from orders.services.order_services import \
        line_paid_amount_for_qty

    completed_returns = ReturnRequest.objects.filter(
        order_line__order=order,
        status=ReturnRequest.Status.COMPLETED,
    ).select_related(
        "order_line",
    )

    cod_return_delta = Decimal(
        "0.00",
    )

    for rr in completed_returns:

        ln = rr.order_line

        return_qty = int(
            rr.quantity,
        )

        amt = line_paid_amount_for_qty(
            order,
            ln,
            return_qty,
        )

        if amt <= Decimal(
            "0.00",
        ):

            continue

        existing = line_refund.get(
            ln.id,
            Decimal(
                "0.00",
            ),
        )

        line_refund[ln.id] = _q(
            existing + amt,
        )

        cod_return_delta += amt

        resolved_at = (
            rr.resolved_at
            if rr.resolved_at
            else order.updated_at
        )

        txn_rows.append(
            {
                "id": -rr.id,
                "amount": str(
                    amt,
                ),
                "reason": WalletTransaction.Reason.RETURN_REFUND,
                "reason_label": "Return refund (COD)",
                "line_id": ln.id,
                "reference_note": (
                    f"Cash refunded on return pickup — {ln.sku} "
                    f"×{return_qty} (order {order.order_number})"
                ),
                "created_at": resolved_at.isoformat(),
            },
        )

    return _q(
        return_total + cod_return_delta,
    ), txn_rows


def order_refund_report(
    order,
):
    

    lines = list(
        order.lines.all(),
    )

    txns = list(
        WalletTransaction.objects.filter(
            order=order,
            type=WalletTransaction.Type.CREDIT,
            reason__in=(
                WalletTransaction.Reason.ORDER_CANCEL,
                WalletTransaction.Reason.RETURN_REFUND,
            ),
        )
        .select_related(
            "return_request",
        )
        .order_by(
            "created_at",
        )
    )

    line_refund = {}

    cancel_total = Decimal(
        "0.00",
    )

    return_total = Decimal(
        "0.00",
    )

    unattributed_cancel = Decimal(
        "0.00",
    )

    txn_rows = []

    for t in txns:

        amt = _q(
            t.amount,
        )

        line_id = None

        if (
            t.reason == WalletTransaction.Reason.RETURN_REFUND
            and t.return_request_id
        ):

            line_id = t.return_request.order_line_id

            return_total += amt

        elif t.reason == WalletTransaction.Reason.ORDER_CANCEL:

            cancel_total += amt

            match = _LINE_NOTE_RE.search(
                t.reference_note or "",
            )

            if match:

                line_id = int(
                    match.group(
                        1,
                    ),
                )

            else:

                
                unattributed_cancel += amt

        if line_id is not None:

            line_refund[line_id] = _q(
                line_refund.get(
                    line_id,
                    Decimal(
                        "0.00",
                    ),
                )
                + amt,
            )

        txn_rows.append(
            {
                "id": t.id,
                "amount": str(
                    amt,
                ),
                "reason": t.reason,
                "reason_label": t.get_reason_display(),
                "line_id": line_id,
                "reference_note": t.reference_note,
                "created_at": t.created_at.isoformat(),
            },
        )

    return_total, txn_rows = _apply_cod_return_pickup_refunds(
        order,
        lines,
        line_refund,
        return_total,
        txn_rows,
    )

    total_refunded = _q(
        cancel_total + return_total,
    )

    original_subtotal = _order_original_subtotal(
        order,
        lines,
    )

    original_coupon = _order_original_coupon(
        order,
        original_subtotal,
    )

    distributed_refund = _distribute_unattributed_cancel(
        lines,
        unattributed_cancel,
        line_refund,
    )

    gst = _gst_rate()

    line_map = {}

    allocated_coupon = Decimal(
        "0.00",
    )

    count = len(
        lines,
    )

    for idx, ln in enumerate(
        lines,
    ):

        line_total = _q(
            ln.line_total,
        )

        if original_subtotal > Decimal(
            "0.00",
        ) and original_coupon > Decimal(
            "0.00",
        ):

            if idx == count - 1:

                coupon_share = _q(
                    original_coupon - allocated_coupon,
                )

            else:

                coupon_share = _q(
                    original_coupon * line_total / original_subtotal,
                )

                allocated_coupon += coupon_share

        else:

            coupon_share = Decimal(
                "0.00",
            )

        tax_share = (line_total * gst).quantize(
            CENTS,
            rounding=ROUND_HALF_UP,
        )

        refund_amt = line_refund.get(
            ln.id,
        )

        if refund_amt is None:

            refund_amt = distributed_refund.get(
                ln.id,
            )

        line_map[ln.id] = {
            "coupon_share": str(
                coupon_share,
            ),
            "tax_share": str(
                tax_share,
            ),
            "refund_amount": (
                str(
                    _q(
                        refund_amt,
                    ),
                )
                if refund_amt is not None
                else None
            ),
        }

    grand_total = _q(
        order.grand_total,
    )

    original_paid = _q(
        grand_total + cancel_total,
    )

    remaining_value = _q(
        grand_total - return_total,
    )

    if remaining_value < Decimal(
        "0.00",
    ):

        remaining_value = Decimal(
            "0.00",
        )

    return {
        "lines": line_map,
        "original_paid": str(
            original_paid,
        ),
        "total_refunded": str(
            total_refunded,
        ),
        "cancel_refund_total": str(
            cancel_total,
        ),
        "return_refund_total": str(
            return_total,
        ),
        "remaining_value": str(
            remaining_value,
        ),
        "refund_transactions": txn_rows,
    }
