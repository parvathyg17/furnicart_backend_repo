from django.db.models import (
    Q,
)

from catalog.models import Product


def get_related_products(product):

    base = Product.objects.select_related(
        "category",
    ).prefetch_related(
        "variants__images",
        "room_types",
    ).filter(
        is_active=True,
        category__is_active=True,
    ).exclude(
        pk=product.pk,
    )

    room_ids = list(
        product.room_types.values_list(
            "id",
            flat=True,
        )
    )

    q = Q(
        category_id=product.category_id,
    )

    if room_ids:

        q |= Q(
            room_types__id__in=room_ids,
        )

    return base.filter(q).distinct().order_by(
        "-created_at",
    )[:8]
