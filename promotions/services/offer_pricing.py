from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP

from django.db.models import Q
from django.utils import timezone

from promotions.models import Offer


def _quantize_money(
    value,
):

    return (
        Decimal(
            value,
        ).quantize(
            Decimal(
                "0.01",
            ),
            rounding=ROUND_HALF_UP,
        )
    )


def offer_is_currently_valid(
    offer,
    *,
    now=None,
):

    if not offer.is_active:

        return False

    if now is None:

        now = timezone.now()

    if offer.valid_from and now < offer.valid_from:

        return False

    if offer.valid_until and now > offer.valid_until:

        return False

    return True


def compute_offer_discount_amount(
    offer,
    line_subtotal,
):
    """
    Discount for a single cart line (variant price × quantity).
    """

    line_subtotal = _quantize_money(
        line_subtotal,
    )

    if line_subtotal <= Decimal(
        "0.00",
    ):

        return Decimal(
            "0.00",
        )

    if offer.discount_type == Offer.DiscountType.PERCENT:

        discount = (
            line_subtotal
            * offer.discount_value
            / Decimal(
                "100",
            )
        ).quantize(
            Decimal(
                "0.01",
            ),
            rounding=ROUND_HALF_UP,
        )

        if offer.max_discount_amount is not None:

            discount = min(
                discount,
                offer.max_discount_amount,
            )

    else:

        discount = min(
            offer.discount_value,
            line_subtotal,
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


def line_gross_subtotal(
    variant,
    quantity,
):

    return (
        variant.price
        * Decimal(
            quantity,
        )
    )


class OfferResolver:

    """
    Batch-load active offers for cart lines to avoid N+1 queries.
    """

    def __init__(
        self,
        *,
        now=None,
    ):

        self.now = now or timezone.now()
        self._product_offers = defaultdict(
            list,
        )
        self._category_offers = defaultdict(
            list,
        )
        self._loaded = False

    def preload(
        self,
        items,
    ):

        product_ids = set()
        category_ids = set()

        for item in items:

            product_ids.add(
                item.variant.product_id,
            )

            category_ids.add(
                item.variant.product.category_id,
            )

        if not product_ids and not category_ids:

            self._loaded = True

            return

        qs = (
            Offer.objects.filter(
                is_active=True,
            )
            .filter(
                Q(
                    offer_type=Offer.OfferType.PRODUCT,
                    product_id__in=product_ids,
                )
                | Q(
                    offer_type=Offer.OfferType.CATEGORY,
                    category_id__in=category_ids,
                ),
            )
            .select_related(
                "product",
                "category",
            )
        )

        for offer in qs:

            if not offer_is_currently_valid(
                offer,
                now=self.now,
            ):

                continue

            if (
                offer.offer_type == Offer.OfferType.PRODUCT
                and offer.product_id
            ):

                self._product_offers[
                    offer.product_id
                ].append(
                    offer,
                )

            elif (
                offer.offer_type == Offer.OfferType.CATEGORY
                and offer.category_id
            ):

                self._category_offers[
                    offer.category_id
                ].append(
                    offer,
                )

        self._loaded = True

    def line_offer_discount(
        self,
        variant,
        quantity,
    ):

        if not self._loaded:

            raise RuntimeError(
                "Call preload() before line_offer_discount().",
            )

        line_subtotal = line_gross_subtotal(
            variant,
            quantity,
        )

        product_discount = Decimal(
            "0.00",
        )

        for offer in self._product_offers.get(
            variant.product_id,
            [],
        ):

            product_discount = max(
                product_discount,
                compute_offer_discount_amount(
                    offer,
                    line_subtotal,
                ),
            )

        category_discount = Decimal(
            "0.00",
        )

        for offer in self._category_offers.get(
            variant.product.category_id,
            [],
        ):

            category_discount = max(
                category_discount,
                compute_offer_discount_amount(
                    offer,
                    line_subtotal,
                ),
            )

        return max(
            product_discount,
            category_discount,
        )

    def line_net_subtotal(
        self,
        variant,
        quantity,
    ):

        gross = line_gross_subtotal(
            variant,
            quantity,
        )

        discount = self.line_offer_discount(
            variant,
            quantity,
        )

        return _quantize_money(
            gross - discount,
        )


def cart_offer_totals(
    items,
    *,
    resolver=None,
):

    if resolver is None:

        resolver = OfferResolver()

        resolver.preload(
            items,
        )

    gross_subtotal = Decimal(
        "0.00",
    )

    offer_discount_total = Decimal(
        "0.00",
    )

    for item in items:

        gross = line_gross_subtotal(
            item.variant,
            item.quantity,
        )

        discount = resolver.line_offer_discount(
            item.variant,
            item.quantity,
        )

        gross_subtotal += gross
        offer_discount_total += discount

    net_subtotal = _quantize_money(
        gross_subtotal - offer_discount_total,
    )

    return {
        "gross_subtotal": _quantize_money(
            gross_subtotal,
        ),
        "offer_discount_total": _quantize_money(
            offer_discount_total,
        ),
        "subtotal": net_subtotal,
        "resolver": resolver,
    }
