from decimal import Decimal, ROUND_HALF_UP

from django.conf import settings


def _d(
    name,
    default,
):

    raw = getattr(
        settings,
        name,
        default,
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


def compute_checkout_totals(
    subtotal,
    *,
    coupon=None,
):
    

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

        z = Decimal(
            "0.00",
        )

        return {
            "subtotal": z,
            "tax_total": z,
            "discount_total": z,
            "shipping_total": z,
            "grand_total": z,
            "gst_rate": _d(
                "CHECKOUT_GST_RATE",
                "0.18",
            ),
            "free_shipping_min_subtotal": _d(
                "CHECKOUT_FREE_SHIPPING_MIN_SUBTOTAL",
                "5000.00",
            ),
            "shipping_flat_amount": _d(
                "CHECKOUT_SHIPPING_FLAT_AMOUNT",
                "100.00",
            ),
            "shipping_tier": "none",
            "coupon": None,
        }

    gst_rate = _d(
        "CHECKOUT_GST_RATE",
        "0.18",
    )

    threshold = _d(
        "CHECKOUT_FREE_SHIPPING_MIN_SUBTOTAL",
        "5000.00",
    )

    flat_ship = _d(
        "CHECKOUT_SHIPPING_FLAT_AMOUNT",
        "100.00",
    )

    discount_total = Decimal(
        "0.00",
    )

    coupon_payload = None

    if coupon is not None:

        from promotions.services.coupon_validation import (
            compute_coupon_discount_amount,
            coupon_summary_dict,
        )

        discount_total = compute_coupon_discount_amount(
            coupon,
            subtotal,
        )

        coupon_payload = coupon_summary_dict(
            coupon,
        )

    tax_total = (
        subtotal * gst_rate
    ).quantize(
        Decimal(
            "0.01",
        ),
        rounding=ROUND_HALF_UP,
    )

    if subtotal >= threshold:

        shipping_total = Decimal(
            "0.00",
        )

        shipping_tier = "free_over_threshold"

    else:

        shipping_total = flat_ship.quantize(
            Decimal(
                "0.01",
            ),
        )

        shipping_tier = "flat"

    grand_total = (
        subtotal
        + tax_total
        + shipping_total
        - discount_total
    ).quantize(
        Decimal(
            "0.01",
        ),
    )

    if grand_total < Decimal(
        "0.00",
    ):

        grand_total = Decimal(
            "0.00",
        )

    return {
        "subtotal": subtotal,
        "tax_total": tax_total,
        "discount_total": discount_total,
        "shipping_total": shipping_total,
        "grand_total": grand_total,
        "gst_rate": gst_rate,
        "free_shipping_min_subtotal": threshold,
        "shipping_flat_amount": flat_ship,
        "shipping_tier": shipping_tier,
        "coupon": coupon_payload,
    }


def totals_as_response_dict(
    totals,
):
    """Serialize Decimals for JSON responses."""

    def s(
        key,
    ):

        return str(
            totals[key].quantize(
                Decimal(
                    "0.01",
                ),
            ),
        )

    return {
        "subtotal": s(
            "subtotal",
        ),
        "tax_total": s(
            "tax_total",
        ),
        "discount_total": s(
            "discount_total",
        ),
        "shipping_total": s(
            "shipping_total",
        ),
        "grand_total": s(
            "grand_total",
        ),
        "gst_rate": str(
            totals["gst_rate"],
        ),
        "free_shipping_min_subtotal": str(
            totals["free_shipping_min_subtotal"].quantize(
                Decimal(
                    "0.01",
                ),
            ),
        ),
        "shipping_flat_amount": str(
            totals["shipping_flat_amount"].quantize(
                Decimal(
                    "0.01",
                ),
            ),
        ),
        "shipping_tier": totals["shipping_tier"],
        "coupon": totals.get(
            "coupon",
        ),
    }
