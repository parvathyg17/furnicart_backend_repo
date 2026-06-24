from django.db.models import Q

from promotions.models import Offer


def get_admin_filtered_offers(
    query_params,
):

    qs = (
        Offer.objects.select_related(
            "product",
            "category",
        )
    )

    search = (
        query_params.get(
            "search",
            "",
        )
        or ""
    ).strip()

    if search:

        qs = qs.filter(
            Q(
                title__icontains=search,
            )
            | Q(
                description__icontains=search,
            )
            | Q(
                product__name__icontains=search,
            )
            | Q(
                category__name__icontains=search,
            ),
        )

    active = (
        query_params.get(
            "is_active",
            "",
        )
        or ""
    ).strip()

    if active.lower() in (
        "true",
        "1",
        "yes",
    ):

        qs = qs.filter(
            is_active=True,
        )

    elif active.lower() in (
        "false",
        "0",
        "no",
    ):

        qs = qs.filter(
            is_active=False,
        )

    offer_type = (
        query_params.get(
            "offer_type",
            "",
        )
        or ""
    ).strip()

    if offer_type in (
        Offer.OfferType.PRODUCT,
        Offer.OfferType.CATEGORY,
    ):

        qs = qs.filter(
            offer_type=offer_type,
        )

    return qs.order_by(
        "-created_at",
    )
