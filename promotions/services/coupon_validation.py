from decimal import Decimal, ROUND_HALF_UP

from django.db.models import Q
from django.utils import timezone

from rest_framework.exceptions import ValidationError

from orders.models import Order
from promotions.models import Coupon


def normalise_redemption_limit(
    value,
):
    """
    Blank, null, or zero means unlimited (no cap).
    """

    if value is None:

        return None

    try:

        parsed = int(
            value,
        )

    except (
        TypeError,
        ValueError,
    ):

        return None

    if parsed <= 0:

        return None

    return parsed


def count_user_coupon_redemptions(
    user,
    coupon,
):

    return (
        Order.objects.filter(
            user=user,
        )
        .exclude(
            status=Order.Status.CANCELLED,
        )
        .filter(
            Q(
                applied_coupon=coupon,
            )
            | Q(
                coupon_code__iexact=coupon.code,
            ),
        )
        .distinct()
        .count()
    )


def compute_coupon_discount_amount(
    coupon,
    subtotal,
):
    """
    Discount is applied to cart subtotal (before tax/shipping).
    """

    subtotal = (
        Decimal(
            subtotal,
        ).quantize(
            Decimal(
                "0.01",
            ),
        )
    )

    if subtotal <= Decimal(
        "0.00",
    ):

        return Decimal(
            "0.00",
        )

    if coupon.discount_type == Coupon.DiscountType.PERCENT:

        discount = (
            subtotal
            * coupon.discount_value
            / Decimal(
                "100",
            )
        ).quantize(
            Decimal(
                "0.01",
            ),
            rounding=ROUND_HALF_UP,
        )

        if coupon.max_discount_amount is not None:

            discount = min(
                discount,
                coupon.max_discount_amount,
            )

    else:

        discount = min(
            coupon.discount_value,
            subtotal,
        ).quantize(
            Decimal(
                "0.01",
            ),
            rounding=ROUND_HALF_UP,
        )

    if discount < Decimal(
        "0.00",
    ):

        return Decimal(
            "0.00",
        )

    return discount


def validate_coupon_for_checkout(
    user,
    coupon,
    subtotal,
):
    """
    Raise DRF ValidationError when the coupon cannot be used.
    """

    if coupon is None:

        raise ValidationError(
            {
                "code": "Invalid coupon code.",
            },
        )

    if not coupon.is_active:

        raise ValidationError(
            {
                "code": "This coupon is no longer active.",
            },
        )

    now = timezone.now()

    if coupon.valid_from and now < coupon.valid_from:

        raise ValidationError(
            {
                "code": "This coupon is not valid yet.",
            },
        )

    if coupon.valid_until and now > coupon.valid_until:

        raise ValidationError(
            {
                "code": "This coupon has expired.",
            },
        )

    subtotal = (
        Decimal(
            subtotal,
        ).quantize(
            Decimal(
                "0.01",
            ),
        )
    )

    if subtotal < coupon.min_order_subtotal:

        raise ValidationError(
            {
                "code": (
                    "Minimum order subtotal of "
                    f"{coupon.min_order_subtotal} required for this coupon."
                ),
            },
        )

    max_total = normalise_redemption_limit(
        coupon.max_redemptions_total,
    )

    if (
        max_total is not None
        and coupon.times_used >= max_total
    ):

        raise ValidationError(
            {
                "code": "This coupon has reached its usage limit.",
            },
        )

    max_per_user = normalise_redemption_limit(
        coupon.max_redemptions_per_user,
    )

    if max_per_user is not None:

        user_uses = count_user_coupon_redemptions(
            user,
            coupon,
        )

        if user_uses >= max_per_user:

            raise ValidationError(
                {
                    "code": "You have already used this coupon.",
                },
            )

    return coupon


def coupon_summary_dict(
    coupon,
):
    if coupon is None:

        return None

    return {
        "id": coupon.id,
        "code": coupon.code,
        "description": coupon.description,
        "discount_type": coupon.discount_type,
        "discount_value": str(
            coupon.discount_value.quantize(
                Decimal(
                    "0.01",
                ),
            ),
        ),
    }
