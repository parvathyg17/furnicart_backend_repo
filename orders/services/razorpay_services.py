import logging
import uuid
from decimal import Decimal

from django.conf import settings
from django.db import transaction
from django.utils import timezone

import razorpay

from rest_framework.exceptions import ValidationError

from accounts.models.address import Address

from cart.services import (
    get_cart_payload,
    get_or_create_cart,
    validate_cart_for_checkout,
)

from orders.models import Order, PaymentIntent
from orders.serializers import OrderDetailSerializer
from orders.services.checkout_pricing import compute_checkout_totals
from orders.services.order_services import create_order_from_cart
from orders.services.razorpay_client import get_razorpay_client


logger = logging.getLogger(__name__)


def _intent_lifetime():

    minutes = getattr(
        settings,
        "RAZORPAY_INTENT_EXPIRY_MINUTES",
        30,
    )

    return timezone.timedelta(
        minutes=minutes,
    )


def _user_prefill(user):

    name = (
        user.get_full_name()
        or user.first_name
        or user.email.split("@")[0]
    )

    return {
        "name": name,
        "email": user.email,
        "contact": user.phone_number or "",
    }


def compute_checkout_grand_total(
    user,
):

    cart = get_or_create_cart(
        user,
    )

    payload = get_cart_payload(
        user,
    )

    subtotal = payload["subtotal"]

    if subtotal <= Decimal(
        "0.00",
    ):

        raise ValidationError(
            "Your cart is empty.",
        )

    from promotions.services.coupon_cart_services import (
        resolve_applied_coupon_for_cart,
    )

    coupon = resolve_applied_coupon_for_cart(
        cart,
        user,
        subtotal,
    )

    if cart.applied_coupon_id and coupon is None:

        raise ValidationError(
            "The applied coupon is no longer valid. "
            "Remove it or update your cart and try again.",
        )

    pricing = compute_checkout_totals(
        subtotal,
        coupon=coupon,
    )

    return {
        "grand_total": pricing[
            "grand_total"
        ],
        "applied_coupon_id": (
            coupon.pk
            if coupon
            else None
        ),
    }


def _expire_stale_pending_intents(
    user,
):

    PaymentIntent.objects.filter(
        user=user,
        status=PaymentIntent.Status.PENDING,
    ).exclude(
        expires_at__gt=timezone.now(),
    ).update(
        status=PaymentIntent.Status.EXPIRED,
    )


def _mark_pending_intents_expired(
    user,
):

    PaymentIntent.objects.filter(
        user=user,
        status=PaymentIntent.Status.PENDING,
    ).update(
        status=PaymentIntent.Status.EXPIRED,
    )


def refund_razorpay_payment(
    payment_id,
    amount_paise,
    *,
    notes=None,
):

    client = get_razorpay_client()

    payload = {
        "amount": amount_paise,
    }

    if notes:

        payload["notes"] = notes

    return client.payment.refund(
        payment_id,
        payload,
    )


def refund_razorpay_order_if_paid(
    order,
):

    if order.payment_method != Order.PaymentMethod.RAZORPAY:

        return

    if order.payment_status not in (
        Order.PaymentStatus.PAID,
        Order.PaymentStatus.PARTIALLY_REFUNDED,
        Order.PaymentStatus.PROCESSING,
    ):

        return

    if not order.gateway_payment_id:

        return

    amount_paise = int(
        order.grand_total * 100,
    )

    refund_razorpay_payment(
        order.gateway_payment_id,
        amount_paise,
        notes={
            "order_number": order.order_number,
            "reason": "order_cancelled",
        },
    )

    order.payment_status = Order.PaymentStatus.REFUNDED


def refund_razorpay_partial_on_order_change(
    order,
    old_grand_total,
    *,
    reason="line_cancelled",
    line_id=None,
):

    if order.payment_method != Order.PaymentMethod.RAZORPAY:

        return

    if order.payment_status not in (
        Order.PaymentStatus.PAID,
        Order.PaymentStatus.PARTIALLY_REFUNDED,
    ):

        return

    if not order.gateway_payment_id:

        return

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

    amount_paise = int(
        refund_amount * 100,
    )

    if amount_paise < 1:

        return

    notes = {
        "order_number": order.order_number,
        "reason": reason,
    }

    if line_id is not None:

        notes[
            "order_line_id"
        ] = str(
            line_id,
        )

    try:

        refund_razorpay_payment(
            order.gateway_payment_id,
            amount_paise,
            notes=notes,
        )

    except Exception:

        logger.exception(
            "Razorpay partial refund failed for order %s",
            order.order_number,
        )

        raise ValidationError(
            "Could not process the payment refund for this cancellation. "
            "Please contact support.",
        )

    order.payment_status = (
        Order.PaymentStatus.PARTIALLY_REFUNDED
    )


@transaction.atomic
def initiate_razorpay_checkout(
    user,
    address_id,
):

    if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:

        raise ValidationError(
            "Online payment is not configured.",
        )

    validation = validate_cart_for_checkout(
        user,
    )

    if not validation["valid"]:

        raise ValidationError(
            validation.get(
                "message",
                "Cart cannot be checked out.",
            ),
        )

    try:

        address = Address.objects.get(
            pk=address_id,
            user=user,
            is_deleted=False,
        )

    except Address.DoesNotExist:

        raise ValidationError(
            "Shipping address not found.",
        )

    pricing = compute_checkout_grand_total(
        user,
    )

    grand_total = pricing[
        "grand_total"
    ]

    amount_paise = int(
        grand_total * 100,
    )

    if amount_paise < 100:

        raise ValidationError(
            "Order total must be at least ₹1.",
        )

    _expire_stale_pending_intents(
        user,
    )

    _mark_pending_intents_expired(
        user,
    )

    client = get_razorpay_client()

    receipt = f"fc-{uuid.uuid4().hex[:20]}"

    try:

        rz_order = client.order.create(
            {
                "amount": amount_paise,
                "currency": "INR",
                "receipt": receipt,
                "notes": {
                    "user_id": str(
                        user.pk,
                    ),
                    "address_id": str(
                        address_id,
                    ),
                },
            },
        )

    except Exception as exc:

        logger.exception(
            "Razorpay order creation failed",
        )

        raise ValidationError(
            "Could not start payment. Please try again.",
        ) from exc

    PaymentIntent.objects.create(
        user=user,
        shipping_address=address,
        razorpay_order_id=rz_order[
            "id"
        ],
        amount_paise=amount_paise,
        grand_total=grand_total,
        applied_coupon_id=pricing[
            "applied_coupon_id"
        ],
        status=PaymentIntent.Status.PENDING,
        expires_at=timezone.now()
        + _intent_lifetime(),
    )

    return {
        "razorpay_order_id": rz_order[
            "id"
        ],
        "key_id": settings.RAZORPAY_KEY_ID,
        "amount_paise": amount_paise,
        "currency": "INR",
        "prefill": _user_prefill(
            user,
        ),
    }


def _validation_message(
    exc,
):

    detail = getattr(
        exc,
        "detail",
        exc,
    )

    if isinstance(
        detail,
        dict,
    ):

        if "detail" in detail:

            return str(
                detail[
                    "detail"
                ],
            )

        parts = []

        for key, val in detail.items():

            if isinstance(
                val,
                (
                    list,
                    tuple,
                ),
            ) and val:

                parts.append(
                    f"{key}: {val[0]}",
                )

            else:

                parts.append(
                    f"{key}: {val}",
                )

        if parts:

            return "; ".join(
                parts,
            )

    if isinstance(
        detail,
        (
            list,
            tuple,
        ),
    ) and detail:

        return str(
            detail[0],
        )

    return str(
        detail,
    )


def _fail_intent_with_refund(
    intent,
    payment_id,
    *,
    message,
):

    try:

        refund_razorpay_payment(
            payment_id,
            intent.amount_paise,
            notes={
                "payment_intent_id": str(
                    intent.pk,
                ),
                "reason": "checkout_failed",
            },
        )

    except Exception:

        logger.exception(
            "Razorpay refund failed for payment %s",
            payment_id,
        )

        raise ValidationError(
            "Payment was received but the order could not be placed. "
            "Please contact support with your payment reference.",
        )

    intent.status = PaymentIntent.Status.FAILED

    intent.gateway_payment_id = payment_id

    intent.save(
        update_fields=[
            "status",
            "gateway_payment_id",
        ],
    )

    raise ValidationError(
        message,
    )


def _complete_intent_from_payment(
    intent,
    payment_id,
):

    if intent.status == PaymentIntent.Status.COMPLETED:

        if intent.order_id:

            return intent.order

        raise ValidationError(
            "Payment was already processed but the order is missing. "
            "Please contact support.",
        )

    if intent.expires_at < timezone.now():

        _fail_intent_with_refund(
            intent,
            payment_id,
            message=(
                "Checkout session expired. Your payment has been refunded."
            ),
        )

    current_pricing = compute_checkout_grand_total(
        intent.user,
    )

    if current_pricing[
        "grand_total"
    ] != intent.grand_total:

        _fail_intent_with_refund(
            intent,
            payment_id,
            message=(
                "Your cart or pricing changed during checkout. "
                "Your payment has been refunded — please try again."
            ),
        )

    try:

        order = create_order_from_cart(
            intent.user,
            intent.shipping_address_id,
            payment_method=Order.PaymentMethod.RAZORPAY,
            razorpay_order_id=intent.razorpay_order_id,
            razorpay_payment_id=payment_id,
        )

    except ValidationError as exc:

        _fail_intent_with_refund(
            intent,
            payment_id,
            message=_validation_message(
                exc,
            ),
        )

    intent.status = PaymentIntent.Status.COMPLETED

    intent.gateway_payment_id = payment_id

    intent.order = order

    intent.save(
        update_fields=[
            "status",
            "gateway_payment_id",
            "order",
        ],
    )

    return order


@transaction.atomic
def verify_razorpay_payment(
    user,
    *,
    razorpay_order_id,
    razorpay_payment_id,
    razorpay_signature,
):

    client = get_razorpay_client()

    try:

        client.utility.verify_payment_signature(
            {
                "razorpay_order_id": razorpay_order_id,
                "razorpay_payment_id": razorpay_payment_id,
                "razorpay_signature": razorpay_signature,
            },
        )

    except razorpay.errors.SignatureVerificationError as exc:

        raise ValidationError(
            "Payment verification failed.",
        ) from exc

    try:

        intent = (
            PaymentIntent.objects.select_for_update().get(
                razorpay_order_id=razorpay_order_id,
                user=user,
            )
        )

    except PaymentIntent.DoesNotExist:

        raise ValidationError(
            "Payment session not found.",
        )

    if intent.status == PaymentIntent.Status.COMPLETED:

        if intent.order_id:

            return intent.order

        raise ValidationError(
            "Payment was already processed but the order is missing. "
            "Please contact support.",
        )

    if intent.status not in (
        PaymentIntent.Status.PENDING,
    ):

        raise ValidationError(
            "This payment session is no longer valid.",
        )

    return _complete_intent_from_payment(
        intent,
        razorpay_payment_id,
    )


def handle_razorpay_webhook(
    payload,
    signature,
):

    webhook_secret = getattr(
        settings,
        "RAZORPAY_WEBHOOK_SECRET",
        "",
    )

    if not webhook_secret:

        logger.warning(
            "Razorpay webhook received but RAZORPAY_WEBHOOK_SECRET is unset",
        )

        return None

    if isinstance(
        payload,
        bytes,
    ):

        payload = payload.decode(
            "utf-8",
        )

    client = get_razorpay_client()

    try:

        client.utility.verify_webhook_signature(
            payload,
            signature,
            webhook_secret,
        )

    except razorpay.errors.SignatureVerificationError:

        logger.warning(
            "Invalid Razorpay webhook signature",
        )

        return None

    import json

    event = json.loads(
        payload,
    )

    event_type = event.get(
        "event",
    )

    if event_type not in (
        "payment.captured",
        "order.paid",
    ):

        return None

    payment_entity = (
        event.get(
            "payload",
            {},
        )
        .get(
            "payment",
            {},
        )
        .get(
            "entity",
            {},
        )
    )

    order_entity = (
        event.get(
            "payload",
            {},
        )
        .get(
            "order",
            {},
        )
        .get(
            "entity",
            {},
        )
    )

    razorpay_order_id = (
        payment_entity.get(
            "order_id",
        )
        or order_entity.get(
            "id",
        )
    )

    payment_id = payment_entity.get(
        "id",
    )

    if not razorpay_order_id or not payment_id:

        return None

    with transaction.atomic():

        try:

            intent = (
                PaymentIntent.objects.select_for_update().get(
                    razorpay_order_id=razorpay_order_id,
                )
            )

        except PaymentIntent.DoesNotExist:

            logger.info(
                "Webhook for unknown Razorpay order %s",
                razorpay_order_id,
            )

            return None

        if intent.status == PaymentIntent.Status.COMPLETED:

            return intent.order

        if intent.status != PaymentIntent.Status.PENDING:

            return None

        try:

            return _complete_intent_from_payment(
                intent,
                payment_id,
            )

        except ValidationError:

            logger.exception(
                "Webhook could not complete payment intent %s",
                intent.pk,
            )

            return None


def serialize_order_response(
    order,
):

    return OrderDetailSerializer(
        order,
    ).data
