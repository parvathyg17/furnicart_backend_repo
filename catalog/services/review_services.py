from django.db import transaction

from rest_framework.exceptions import ValidationError

from catalog.models import ProductReview
from catalog.selectors.review_selectors import (
    get_delivered_order_line_for_product,
    get_user_product_by_ref,
    get_user_review_for_product,
    user_has_delivered_purchase,
)


def _normalize_rating(
    rating,
):

    if rating is None:

        raise ValidationError(
            {
                "rating": "Rating is required.",
            },
        )

    try:

        value = int(rating)

    except (
        TypeError,
        ValueError,
    ):

        raise ValidationError(
            {
                "rating": "Rating must be a number between 1 and 5.",
            },
        )

    if value < 1 or value > 5:

        raise ValidationError(
            {
                "rating": "Rating must be between 1 and 5.",
            },
        )

    return value


def _normalize_title(
    title,
):

    return str(
        title or "",
    ).strip()[
        :120
    ]


def _normalize_body(
    body,
):

    clean = str(
        body or "",
    ).strip()

    if not clean:

        raise ValidationError(
            {
                "body": "Review text is required.",
            },
        )

    return clean[
        :2000
    ]


def _get_product_or_error(
    product_ref,
):

    product = get_user_product_by_ref(
        product_ref,
    )

    if not product:

        raise ValidationError(
            {
                "product": "Product not found.",
            },
        )

    return product


@transaction.atomic
def create_review_for_user(
    user,
    product_ref,
    *,
    rating,
    title="",
    body="",
):

    product = _get_product_or_error(
        product_ref,
    )

    if get_user_review_for_product(
        user,
        product,
    ):

        raise ValidationError(
            "You have already reviewed this product.",
        )

    if not user_has_delivered_purchase(
        user,
        product,
    ):

        raise ValidationError(
            "You can only review products after delivery.",
        )

    order_line = get_delivered_order_line_for_product(
        user,
        product,
    )

    review = ProductReview.objects.create(
        user=user,
        product=product,
        order_line=order_line,
        rating=_normalize_rating(
            rating,
        ),
        title=_normalize_title(
            title,
        ),
        body=_normalize_body(
            body,
        ),
        status=ProductReview.Status.APPROVED,
    )

    return review


@transaction.atomic
def update_review_for_user(
    user,
    review_id,
    *,
    rating=None,
    title=None,
    body=None,
):

    try:

        review = ProductReview.objects.select_for_update().get(
            pk=review_id,
            user=user,
        )

    except ProductReview.DoesNotExist:

        raise ValidationError(
            "Review not found.",
        )

    if review.status == ProductReview.Status.REJECTED:

        raise ValidationError(
            "This review can no longer be edited.",
        )

    if rating is not None:

        review.rating = _normalize_rating(
            rating,
        )

    if title is not None:

        review.title = _normalize_title(
            title,
        )

    if body is not None:

        review.body = _normalize_body(
            body,
        )

    review.save()

    return review


@transaction.atomic
def delete_review_for_user(
    user,
    review_id,
):

    try:

        review = ProductReview.objects.select_for_update().get(
            pk=review_id,
            user=user,
        )

    except ProductReview.DoesNotExist:

        raise ValidationError(
            "Review not found.",
        )

    review.delete()


@transaction.atomic
def moderate_review_for_admin(
    review_id,
    *,
    status,
):

    valid = {
        ProductReview.Status.APPROVED,
        ProductReview.Status.REJECTED,
        ProductReview.Status.PENDING,
    }

    if status not in valid:

        raise ValidationError(
            {
                "status": "Invalid review status.",
            },
        )

    try:

        review = ProductReview.objects.select_for_update().get(
            pk=review_id,
        )

    except ProductReview.DoesNotExist:

        raise ValidationError(
            "Review not found.",
        )

    review.status = status
    review.save(
        update_fields=[
            "status",
            "updated_at",
        ],
    )

    return review
