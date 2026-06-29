from collections import defaultdict
from decimal import Decimal

from django.db.models import Q
from django.utils import timezone

from promotions.models import Offer
from promotions.services.offer_pricing import (
    compute_offer_discount_amount,
    offer_is_currently_valid,
)


def _min_active_variant_price(
    product,
):

    in_stock_prices = []
    active_prices = []

    for variant in product.variants.all():

        if (
            variant.is_active
            and variant.price is not None
        ):

            active_prices.append(
                variant.price,
            )

            if variant.stock > 0:

                in_stock_prices.append(
                    variant.price,
                )

    prices = (
        in_stock_prices
        or active_prices
    )

    if not prices:

        return Decimal(
            "0.00",
        )

    return min(
        prices,
    )


def format_offer_badge_label(
    offer,
):

    if offer.discount_type == Offer.DiscountType.PERCENT:

        value = offer.discount_value

        if value == value.to_integral_value():

            return f"{int(value)}% OFF"

        return f"{value}% OFF"

    amount = offer.discount_value.quantize(
        Decimal(
            "0.01",
        ),
    )

    if amount == amount.to_integral_value():

        return f"₹{int(amount)} OFF"

    return f"₹{amount} OFF"


def offer_to_badge_dict(
    offer,
):

    return {
        "label": format_offer_badge_label(
            offer,
        ),
        "discount_type": offer.discount_type,
        "discount_value": str(
            offer.discount_value.quantize(
                Decimal(
                    "0.01",
                ),
            ),
        ),
        "offer_type": offer.offer_type,
        "title": offer.title or "",
    }


def _load_active_offer_maps(
    product_ids,
    category_ids,
    *,
    now=None,
):

    product_map = defaultdict(
        list,
    )

    category_map = defaultdict(
        list,
    )

    if not product_ids and not category_ids:

        return product_map, category_map

    if now is None:

        now = timezone.now()

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
    )

    for offer in qs:

        if not offer_is_currently_valid(
            offer,
            now=now,
        ):

            continue

        if (
            offer.offer_type == Offer.OfferType.PRODUCT
            and offer.product_id
        ):

            product_map[
                offer.product_id
            ].append(
                offer,
            )

        elif (
            offer.offer_type == Offer.OfferType.CATEGORY
            and offer.category_id
        ):

            category_map[
                offer.category_id
            ].append(
                offer,
            )

    return product_map, category_map


def best_offer_discount_for_product_price(
    product,
    line_subtotal,
    product_map,
    category_map,
):

    line_subtotal = Decimal(
        line_subtotal,
    ).quantize(
        Decimal(
            "0.01",
        ),
    )

    if line_subtotal <= Decimal(
        "0.00",
    ):

        return Decimal(
            "0.00",
        )

    best_discount = Decimal(
        "0.00",
    )

    for offer in product_map.get(
        product.id,
        [],
    ):

        best_discount = max(
            best_discount,
            compute_offer_discount_amount(
                offer,
                line_subtotal,
            ),
        )

    for offer in category_map.get(
        product.category_id,
        [],
    ):

        best_discount = max(
            best_discount,
            compute_offer_discount_amount(
                offer,
                line_subtotal,
            ),
        )

    return best_discount


def discounted_unit_price(
    product,
    gross_price,
    product_map,
    category_map,
):

    gross = Decimal(
        gross_price,
    ).quantize(
        Decimal(
            "0.01",
        ),
    )

    discount = best_offer_discount_for_product_price(
        product,
        gross,
        product_map,
        category_map,
    )

    return (
        gross - discount
    ).quantize(
        Decimal(
            "0.01",
        ),
    )


def build_offer_pricing_context(
    products,
    *,
    now=None,
):

    products = list(
        products,
    )

    product_ids = {
        product.id
        for product in products
    }

    category_ids = {
        product.category_id
        for product in products
    }

    product_map, category_map = _load_active_offer_maps(
        product_ids,
        category_ids,
        now=now,
    )

    badges = {}

    for product in products:

        badge = best_offer_badge_for_product(
            product,
            product_map,
            category_map,
        )

        if badge is not None:

            badges[
                product.id
            ] = badge

    return {
        "product_map": product_map,
        "category_map": category_map,
        "badges": badges,
    }


def extend_serializer_context_with_offers(
    context,
    products,
    *,
    now=None,
):

    pricing = build_offer_pricing_context(
        products,
        now=now,
    )

    return {
        **context,
        "product_offer_badges": pricing[
            "badges"
        ],
        "offer_product_map": pricing[
            "product_map"
        ],
        "offer_category_map": pricing[
            "category_map"
        ],
    }


def best_offer_badge_for_product(
    product,
    product_map,
    category_map,
):

    ref_price = _min_active_variant_price(
        product,
    )

    if ref_price <= Decimal(
        "0.00",
    ):

        return None

    best_offer = None

    best_discount = Decimal(
        "0.00",
    )

    for offer in product_map.get(
        product.id,
        [],
    ):

        discount = compute_offer_discount_amount(
            offer,
            ref_price,
        )

        if discount > best_discount:

            best_discount = discount
            best_offer = offer

    for offer in category_map.get(
        product.category_id,
        [],
    ):

        discount = compute_offer_discount_amount(
            offer,
            ref_price,
        )

        if discount > best_discount:

            best_discount = discount
            best_offer = offer

    if (
        best_offer is None
        or best_discount <= Decimal(
            "0.00",
        )
    ):

        return None

    return offer_to_badge_dict(
        best_offer,
    )


def build_offer_badges_for_products(
    products,
    *,
    now=None,
):

    products = list(
        products,
    )

    if not products:

        return {}

    product_ids = {
        product.id
        for product in products
    }

    category_ids = {
        product.category_id
        for product in products
    }

    product_map, category_map = _load_active_offer_maps(
        product_ids,
        category_ids,
        now=now,
    )

    badges = {}

    for product in products:

        badge = best_offer_badge_for_product(
            product,
            product_map,
            category_map,
        )

        if badge is not None:

            badges[
                product.id
            ] = badge

    return badges
