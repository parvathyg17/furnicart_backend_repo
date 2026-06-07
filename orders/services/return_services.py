from django.db import transaction
from django.utils import timezone

from rest_framework.exceptions import ValidationError

from catalog.models import ProductVariant

from orders.models import Order, OrderLine, ReturnRequest
from orders.services.order_status import persist_derived_order_status


def _normalize_return_reason(
    reason,
):

    if reason is None:

        raise ValidationError(
            {
                "reason": "A return reason is required.",
            },
        )

    clean = str(
        reason,
    ).strip()

    if not clean:

        raise ValidationError(
            {
                "reason": "A return reason is required.",
            },
        )

    return clean[
        :2000
    ]


@transaction.atomic
def create_return_request_for_user(
    user,
    order_number,
    line_id,
    *,
    reason,
):

    reason_clean = _normalize_return_reason(
        reason,
    )

    order = Order.objects.select_for_update().get(
        user=user,
        order_number=order_number,
    )

    line = (
        OrderLine.objects.select_for_update()
        .select_related(
            "variant",
        )
        .get(
            pk=line_id,
            order=order,
        )
    )

    if line.status != OrderLine.LineStatus.ACTIVE:

        raise ValidationError(
            "This line cannot be returned.",
        )

    if line.fulfillment_status != OrderLine.FulfillmentStatus.DELIVERED:

        raise ValidationError(
            "Returns are only available after delivery.",
        )

    if ReturnRequest.objects.filter(
        order_line=line,
    ).exists():

        raise ValidationError(
            "A return has already been requested for this item.",
        )

    req = ReturnRequest.objects.create(
        order_line=line,
        user=user,
        reason=reason_clean,
        status=ReturnRequest.Status.PENDING,
    )

    return req


@transaction.atomic
def admin_set_return_request_status(
    *,
    return_id,
    new_status,
    admin_note="",
):

    note_clean = str(
        admin_note or "",
    ).strip()[
        :2000
    ]

    req = (
        ReturnRequest.objects.select_for_update()
        .select_related(
            "order_line",
            "order_line__order",
            "order_line__variant",
        )
        .get(
            pk=return_id,
        )
    )

    if new_status not in dict(
        ReturnRequest.Status.choices,
    ):

        raise ValidationError(
            "Invalid return status.",
        )

    if req.status == ReturnRequest.Status.COMPLETED:

        raise ValidationError(
            "This return is already completed.",
        )

    if new_status == ReturnRequest.Status.REJECTED:

        if req.status != ReturnRequest.Status.PENDING:

            raise ValidationError(
                "Only pending returns can be rejected.",
            )

        req.status = ReturnRequest.Status.REJECTED

        req.admin_note = note_clean

        req.resolved_at = timezone.now()

        req.save(
            update_fields=[
                "status",
                "admin_note",
                "resolved_at",
            ],
        )

        return req

    if new_status == ReturnRequest.Status.APPROVED:

        if req.status != ReturnRequest.Status.PENDING:

            raise ValidationError(
                "Only pending returns can be approved.",
            )

        req.status = ReturnRequest.Status.APPROVED

        req.admin_note = note_clean

        req.save(
            update_fields=[
                "status",
                "admin_note",
            ],
        )

        return req

    if new_status == ReturnRequest.Status.COMPLETED:

        if req.status != ReturnRequest.Status.APPROVED:

            raise ValidationError(
                "Approve the return before completing it.",
            )

        line = req.order_line

        variant = ProductVariant.objects.select_for_update().get(
            pk=line.variant_id,
        )

        variant.stock += line.quantity

        variant.save(
            update_fields=[
                "stock",
                "updated_at",
            ],
        )

        line.fulfillment_status = OrderLine.FulfillmentStatus.RETURNED

        line.save(
            update_fields=[
                "fulfillment_status",
            ],
        )

        req.status = ReturnRequest.Status.COMPLETED

        req.admin_note = note_clean or req.admin_note

        req.resolved_at = timezone.now()

        req.save(
            update_fields=[
                "status",
                "admin_note",
                "resolved_at",
            ],
        )

        persist_derived_order_status(
            line.order_id,
        )

        return req

    raise ValidationError(
        "Unsupported status transition.",
    )
