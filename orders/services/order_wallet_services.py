from decimal import Decimal

from accounts.models.wallet import WalletTransaction
from accounts.services.wallet_services import credit_wallet
from orders.models import Order


def order_eligible_for_wallet_refund(
    order,
):
    """
    Only prepaid online methods are refunded to the wallet.
    COD orders are excluded — no payment was collected through the app.
    """

    return order.payment_method in (
        Order.PaymentMethod.RAZORPAY,
        Order.PaymentMethod.WALLET,
    )


def credit_wallet_for_order_cancellation(
    order,
    amount,
    *,
    line_id=None,
):

    if not order_eligible_for_wallet_refund(
        order,
    ):

        return

    amount = (
        Decimal(
            str(
                amount,
            ),
        ).quantize(
            Decimal(
                "0.01",
            ),
        )
    )

    if amount <= Decimal(
        "0.00",
    ):

        return

    note = (
        f"Cancellation refund for order {order.order_number}"
    )

    if line_id is not None:

        note = (
            f"{note} (line #{line_id})"
        )

    credit_wallet(
        order.user,
        amount,
        reason=WalletTransaction.Reason.ORDER_CANCEL,
        order=order,
        reference_note=note,
    )


def credit_wallet_for_return_completion(
    return_request,
    amount,
):

    line = return_request.order_line

    order = line.order

    if not order_eligible_for_wallet_refund(
        order,
    ):

        return

    amount = (
        Decimal(
            str(
                amount,
            ),
        ).quantize(
            Decimal(
                "0.01",
            ),
        )
    )

    if amount <= Decimal(
        "0.00",
    ):

        return

    credit_wallet(
        return_request.user,
        amount,
        reason=WalletTransaction.Reason.RETURN_REFUND,
        order=order,
        return_request=return_request,
        reference_note=(
            f"Return refund for {line.sku} "
            f"(order {order.order_number})"
        ),
    )


def wallet_refund_delta_on_partial_cancel(
    order,
    old_grand_total,
    *,
    line_id=None,
):

    refund_amount = (
        old_grand_total - order.grand_total
    ).quantize(
        Decimal(
            "0.01",
        ),
    )

    if refund_amount <= Decimal(
        "0.00",
    ):

        return

    credit_wallet_for_order_cancellation(
        order,
        refund_amount,
        line_id=line_id,
    )

    if (
        order_eligible_for_wallet_refund(
            order,
        )
        and order.payment_status in (
            Order.PaymentStatus.PAID,
            Order.PaymentStatus.PARTIALLY_REFUNDED,
        )
    ):

        order.payment_status = (
            Order.PaymentStatus.PARTIALLY_REFUNDED
        )


def wallet_refund_on_full_cancel(
    order,
):

    refund_amount = order.grand_total.quantize(
        Decimal(
            "0.01",
        ),
    )

    if refund_amount > Decimal(
        "0.00",
    ):

        credit_wallet_for_order_cancellation(
            order,
            refund_amount,
        )

    if (
        order_eligible_for_wallet_refund(
            order,
        )
        and order.payment_status in (
            Order.PaymentStatus.PAID,
            Order.PaymentStatus.PARTIALLY_REFUNDED,
            Order.PaymentStatus.PROCESSING,
        )
    ):

        order.payment_status = (
            Order.PaymentStatus.REFUNDED
        )
