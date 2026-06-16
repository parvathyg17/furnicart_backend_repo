from django.db.models import (
    Avg,
    Count,
    Q,
)

from catalog.models import (
    Product,
    ProductReview,
)
from orders.models import OrderLine


def approved_review_filter():

    return Q(
        reviews__status=ProductReview.Status.APPROVED,
    )


def annotate_product_ratings(
    queryset,
):

    filt = approved_review_filter()

    return queryset.annotate(
        average_rating=Avg(
            "reviews__rating",
            filter=filt,
        ),
        review_count=Count(
            "reviews",
            filter=filt,
        ),
    )


def get_user_product_by_ref(
    product_ref,
):

    ref = str(
        product_ref,
    ).strip()

    if not ref:

        return None

    qs = Product.objects.filter(
        is_active=True,
    )

    if ref.isdigit():

        return qs.filter(
            pk=int(ref),
        ).first()

    return qs.filter(
        slug=ref,
    ).first()


def get_approved_reviews_for_product(
    product,
):

    return ProductReview.objects.filter(
        product=product,
        status=ProductReview.Status.APPROVED,
    ).select_related(
        "user",
        "order_line",
    )


def get_user_review_for_product(
    user,
    product,
):

    if not user or not user.is_authenticated:

        return None

    return ProductReview.objects.filter(
        user=user,
        product=product,
    ).select_related(
        "order_line",
    ).first()


def user_has_delivered_purchase(
    user,
    product,
):

    return OrderLine.objects.filter(
        order__user=user,
        variant__product=product,
        status=OrderLine.LineStatus.ACTIVE,
        fulfillment_status=OrderLine.FulfillmentStatus.DELIVERED,
    ).exists()


def get_delivered_order_line_for_product(
    user,
    product,
):

    return (
        OrderLine.objects.filter(
            order__user=user,
            variant__product=product,
            status=OrderLine.LineStatus.ACTIVE,
            fulfillment_status=OrderLine.FulfillmentStatus.DELIVERED,
        )
        .select_related(
            "variant",
        )
        .order_by(
            "-order__placed_at",
        )
        .first()
    )


def user_can_review_product(
    user,
    product,
):

    if not user or not user.is_authenticated:

        return False

    if get_user_review_for_product(
        user,
        product,
    ):

        return False

    return user_has_delivered_purchase(
        user,
        product,
    )


def get_eligible_products_for_user(
    user,
):

    reviewed_product_ids = ProductReview.objects.filter(
        user=user,
    ).values_list(
        "product_id",
        flat=True,
    )

    delivered_product_ids = (
        OrderLine.objects.filter(
            order__user=user,
            status=OrderLine.LineStatus.ACTIVE,
            fulfillment_status=OrderLine.FulfillmentStatus.DELIVERED,
        )
        .values_list(
            "variant__product_id",
            flat=True,
        )
        .distinct()
    )

    return Product.objects.filter(
        id__in=delivered_product_ids,
        is_active=True,
    ).exclude(
        id__in=reviewed_product_ids,
    ).select_related(
        "category",
    ).order_by(
        "-created_at",
    )


def get_admin_filtered_reviews(
    params,
):

    queryset = ProductReview.objects.select_related(
        "user",
        "product",
        "order_line",
    )

    status = (params.get("status") or "").strip()

    if status:

        queryset = queryset.filter(
            status=status,
        )

    search = (params.get("search") or "").strip()

    if search:

        queryset = queryset.filter(
            Q(
                product__name__icontains=search,
            )
            | Q(
                user__email__icontains=search,
            )
            | Q(
                title__icontains=search,
            )
            | Q(
                body__icontains=search,
            ),
        )

    return queryset.order_by(
        "-created_at",
    )
