from django.db.models import Q

from promotions.models import Coupon


def get_admin_filtered_coupons(
    query_params,
):

    qs = Coupon.objects.all()

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
                code__icontains=search,
            )
            | Q(
                description__icontains=search,
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

    return qs.order_by(
        "-created_at",
    )
