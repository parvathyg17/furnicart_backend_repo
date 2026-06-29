from decimal import Decimal

from django.db.models import Q
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from promotions.models import Coupon
from promotions.services.coupon_validation import (
    normalise_redemption_limit,
    validate_coupon_for_checkout,
)

def _coupon_ineligible_message(
    exc,
):

    detail = exc.detail

    if isinstance(
        detail,
        dict,
    ):

        for value in detail.values():

            if isinstance(
                value,
                (
                    list,
                    tuple,
                ),
            ) and value:

                return str(
                    value[0],
                )

            if isinstance(
                value,
                str,
            ):

                return value

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

    if isinstance(
        detail,
        str,
    ):

        return detail

    return "This coupon cannot be used on your order."


def _coupon_public_dict(
    coupon,
    *,
    is_eligible,
    ineligible_reason="",
):

    return {
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
        "min_order_subtotal": str(
            coupon.min_order_subtotal.quantize(
                Decimal(
                    "0.01",
                ),
            ),
        ),
        "is_eligible": is_eligible,
        "ineligible_reason": ineligible_reason,
    }


def list_active_coupons_for_checkout(
    user,
    subtotal,
    *,
    exclude_code=None,
):
    """
    Active, date-valid coupons the customer may see at checkout.
    Includes eligibility for the current cart subtotal and per-user limits.
    """

    now = timezone.now()

    subtotal = (
        Decimal(
            subtotal,
        ).quantize(
            Decimal(
                "0.01",
            ),
        )
    )

    qs = (
        Coupon.objects.filter(
            is_active=True,
        )
        .filter(
            Q(
                assigned_user__isnull=True,
            )
            | Q(
                assigned_user=user,
            ),
        )
        .filter(
            Q(
                valid_from__isnull=True,
            )
            | Q(
                valid_from__lte=now,
            ),
        )
        .filter(
            Q(
                valid_until__isnull=True,
            )
            | Q(
                valid_until__gte=now,
            ),
        )
        .order_by(
            "code",
        )
    )

    if exclude_code:

        qs = qs.exclude(
            code=exclude_code,
        )

    rows = []

    for coupon in qs:

        max_total = normalise_redemption_limit(
            coupon.max_redemptions_total,
        )

        if (
            max_total is not None
            and coupon.times_used >= max_total
        ):

            continue

        try:

            validate_coupon_for_checkout(
                user,
                coupon,
                subtotal,
            )

            rows.append(
                _coupon_public_dict(
                    coupon,
                    is_eligible=True,
                ),
            )

        except ValidationError as exc:

            rows.append(
                _coupon_public_dict(
                    coupon,
                    is_eligible=False,
                    ineligible_reason=_coupon_ineligible_message(
                        exc,
                    ),
                ),
            )

    rows.sort(
        key=lambda row: (
            not row["is_eligible"],
            row["code"],
        ),
    )

    return rows
