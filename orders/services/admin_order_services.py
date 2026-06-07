from django.db import transaction

from rest_framework.exceptions import ValidationError

from orders.models import Order, OrderLine
from orders.services.order_status import persist_derived_order_status


@transaction.atomic
def admin_set_order_line_fulfillment(
    *,
    order_number,
    line_id,
    fulfillment_status,
):

    line = (
        OrderLine.objects.select_for_update()
        .select_related(
            "order",
        )
        .get(
            pk=line_id,
            order__order_number=order_number,
        )
    )

    if line.status != OrderLine.LineStatus.ACTIVE:

        raise ValidationError(
            "Cannot change fulfillment for a cancelled line.",
        )

    valid = {
        c
        for c, _ in OrderLine.FulfillmentStatus.choices
    }

    if fulfillment_status not in valid:

        raise ValidationError(
            "Invalid fulfillment status.",
        )

    if fulfillment_status == OrderLine.FulfillmentStatus.RETURNED:

        raise ValidationError(
            "Returned status is set only after a completed return.",
        )

    if (
        line.fulfillment_status == OrderLine.FulfillmentStatus.DELIVERED
        and fulfillment_status != OrderLine.FulfillmentStatus.DELIVERED
    ):

        raise ValidationError(
            "Cannot change fulfillment after a line is marked delivered.",
        )

    line.fulfillment_status = fulfillment_status

    line.save(
        update_fields=[
            "fulfillment_status",
        ],
    )

    persist_derived_order_status(
        line.order_id,
    )

    return line.order
