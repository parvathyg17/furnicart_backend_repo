from django.db import transaction
from django.db.models import F

from rest_framework.exceptions import ValidationError

from cart.models import Cart
from cart.services import (
    get_cart_payload,
    get_or_create_cart,
)
from promotions.models import Coupon
from promotions.services.coupon_validation import (
    validate_coupon_for_checkout,
)


@transaction.atomic
def apply_coupon_to_cart(
    user,
    code,
):
    cart = (
        Cart.objects.select_for_update()
        .get(
            pk=get_or_create_cart(
                user,
            ).pk,
        )
    )

    if cart.applied_coupon_id:

        raise ValidationError(
            {
                "code": (
                    "A coupon is already applied. "
                    "Remove it before applying another."
                ),
            },
        )

    clean = (
        str(
            code or "",
        )
        .strip()
        .upper()
    )

    if not clean:

        raise ValidationError(
            {
                "code": "Coupon code is required.",
            },
        )

    try:

        coupon = Coupon.objects.get(
            code=clean,
        )

    except Coupon.DoesNotExist:

        raise ValidationError(
            {
                "code": "Invalid coupon code.",
            },
        )

    _, _, subtotal, _, _ = get_cart_payload(
        user,
    )

    if subtotal <= 0:

        raise ValidationError(
            {
                "code": "Your cart is empty.",
            },
        )

    validate_coupon_for_checkout(
        user,
        coupon,
        subtotal,
    )

    cart.applied_coupon = coupon

    cart.save(
        update_fields=[
            "applied_coupon",
            "updated_at",
        ],
    )

    return cart


@transaction.atomic
def remove_coupon_from_cart(
    user,
):
    cart = (
        Cart.objects.select_for_update()
        .get(
            pk=get_or_create_cart(
                user,
            ).pk,
        )
    )

    if not cart.applied_coupon_id:

        raise ValidationError(
            {
                "code": "No coupon is applied to your cart.",
            },
        )

    cart.applied_coupon = None

    cart.save(
        update_fields=[
            "applied_coupon",
            "updated_at",
        ],
    )

    return cart


def resolve_applied_coupon_for_cart(
    cart,
    user,
    subtotal,
):
    """
    Return the cart's coupon if still valid; otherwise clear it.
    """

    coupon = cart.applied_coupon

    if coupon is None:

        return None

    try:

        validate_coupon_for_checkout(
            user,
            coupon,
            subtotal,
        )

    except ValidationError:

        cart.applied_coupon = None

        cart.save(
            update_fields=[
                "applied_coupon",
                "updated_at",
            ],
        )

        return None

    return coupon


@transaction.atomic
def record_coupon_redemption(
    coupon,
):
    Coupon.objects.filter(
        pk=coupon.pk,
    ).update(
        times_used=F(
            "times_used",
        )
        + 1,
    )
