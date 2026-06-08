from decimal import Decimal

from django.db import IntegrityError, transaction
from django.db.models import Prefetch, Sum
from django.utils import timezone

from rest_framework.exceptions import ValidationError

from accounts.models.address import Address
from catalog.models import ProductVariant, VariantImage

from cart.models import CartItem
from cart.services import (
    cart_line_subtotal,
    validate_cart_for_checkout,
    get_or_create_cart,
)

from orders.models import DailyOrderCounter, Order, OrderLine
from orders.services.checkout_pricing import compute_checkout_totals
from orders.services.order_status import persist_derived_order_status


def _allocate_order_number():

    today = timezone.now().date()
    date_str = today.strftime("%Y%m%d")

    for _ in range(8):

        try:

            with transaction.atomic():

                counter, _ = (
                    DailyOrderCounter.objects.select_for_update().get_or_create(
                        date=today,
                        defaults={
                            "last_number": 0,
                        },
                    )
                )

                counter.last_number += 1

                counter.save(
                    update_fields=[
                        "last_number",
                    ],
                )

                return f"FC-{date_str}-{counter.last_number:06d}"

        except IntegrityError:

            continue

    raise ValidationError(
        "Could not allocate an order number. Please try again.",
    )


def _primary_variant_image_url(variant):

    for img in variant.images.all():

        if img.image:

            return img.image.url

    return ""


@transaction.atomic
def create_order_from_cart(
    user,
    address_id,
    *,
    payment_method=None,
):

    

    if payment_method is None:

        payment_method = Order.PaymentMethod.COD

    if payment_method != Order.PaymentMethod.COD:

        raise ValidationError(
            "Only cash on delivery is available at this time.",
        )

    validation = validate_cart_for_checkout(
        user,
    )

    if not validation["valid"]:

        raise ValidationError(
            validation.get(
                "message",
                "Cart cannot be checked out.",
            ),
        )

    try:

        address = Address.objects.get(
            pk=address_id,
            user=user,
            is_deleted=False,
        )

    except Address.DoesNotExist:

        raise ValidationError(
            "Shipping address not found.",
        )

    cart = get_or_create_cart(
        user,
    )

    items = list(
        CartItem.objects.filter(
            cart=cart,
        ).select_related(
            "variant",
            "variant__product",
            "variant__product__category",
        ),
    )

    if not items:

        raise ValidationError(
            "Your cart is empty.",
        )

    variant_ids = sorted(
        {
            item.variant_id
            for item in items
        },
    )

    locked_variants = {
        v.pk: v
        for v in ProductVariant.objects.select_for_update().filter(
            pk__in=variant_ids,
        ).select_related(
            "product",
            "product__category",
        ).prefetch_related(
            Prefetch(
                "images",
                queryset=VariantImage.objects.order_by(
                    "-is_primary",
                    "display_order",
                    "-created_at",
                ),
            ),
        )
    }

    subtotal = Decimal("0.00")

    line_specs = []

    for item in items:

        variant = locked_variants.get(
            item.variant_id,
        )

        if variant is None:

            raise ValidationError(
                "One or more products are no longer available.",
            )

        if not variant.product.is_active:

            raise ValidationError(
                f"{variant.product.name} is unavailable.",
            )

        if not variant.product.category.is_active:

            raise ValidationError(
                f"{variant.product.name} is unavailable.",
            )

        if not variant.is_active:

            raise ValidationError(
                f"{variant.product.name} ({variant.variant_name}) is unavailable.",
            )

        if variant.stock < item.quantity:

            raise ValidationError(
                (
                    f"Not enough stock for {variant.product.name} "
                    f"({variant.variant_name})."
                ),
            )

        line_sub = cart_line_subtotal(
            item,
        )

        subtotal += line_sub

        line_specs.append(
            {
                "item": item,
                "variant": variant,
                "line_subtotal": line_sub,
            },
        )

    pricing = compute_checkout_totals(
        subtotal,
    )

    tax_total = pricing["tax_total"]

    discount_total = pricing["discount_total"]

    shipping_total = pricing["shipping_total"]

    grand_total = pricing["grand_total"]

    order_number = _allocate_order_number()

    order = Order.objects.create(
        user=user,
        order_number=order_number,
        status=Order.Status.PENDING,
        payment_method=payment_method,
        payment_status=Order.PaymentStatus.PENDING,
        subtotal=subtotal.quantize(
            Decimal("0.01"),
        ),
        tax_total=tax_total.quantize(
            Decimal("0.01"),
        ),
        discount_total=discount_total.quantize(
            Decimal("0.01"),
        ),
        shipping_total=shipping_total.quantize(
            Decimal("0.01"),
        ),
        grand_total=grand_total,
        shipping_address=address,
        shipping_name=address.name,
        shipping_phone=address.phone,
        shipping_address_line=address.address_line,
        shipping_city=address.city,
        shipping_state=address.state,
        shipping_pincode=address.pincode,
    )

    for spec in line_specs:

        variant = spec["variant"]

        qty = spec["item"].quantity

        variant.stock -= qty

        variant.save(
            update_fields=[
                "stock",
                "updated_at",
            ],
        )

        line_sub = spec["line_subtotal"].quantize(
            Decimal("0.01"),
        )

        OrderLine.objects.create(
            order=order,
            variant=variant,
            product_name=variant.product.name,
            variant_name=variant.variant_name,
            sku=variant.sku,
            unit_price=variant.price,
            quantity=qty,
            tax_amount=Decimal("0.00"),
            discount_amount=Decimal("0.00"),
            line_total=line_sub,
            image_url=_primary_variant_image_url(
                variant,
            )[:512],
            fulfillment_status=OrderLine.FulfillmentStatus.PENDING,
        )

    CartItem.objects.filter(
        cart=cart,
    ).delete()

    return order


def get_order_for_user(
    user,
    order_number,
):

    return (
        Order.objects.prefetch_related(
            Prefetch(
                "lines",
                queryset=OrderLine.objects.select_related(
                    "variant",
                    "variant__product",
                ).order_by(
                    "id",
                ),
            ),
        ).get(
            user=user,
            order_number=order_number,
        )
    )


def _normalize_cancel_reason(
    reason,
):

    if reason is None:

        return ""

    return str(
        reason,
    ).strip()[
        :500
    ]


def _set_order_financials_zero(
    order,
):

    z = Decimal(
        "0.00",
    )

    order.subtotal = z

    order.tax_total = z

    order.discount_total = z

    order.shipping_total = z

    order.grand_total = z


def _recalculate_order_financials_from_active_lines(
    order,
):

    agg = order.lines.filter(
        status=OrderLine.LineStatus.ACTIVE,
    ).aggregate(
        s=Sum(
            "line_total",
        ),
    )

    raw = agg.get(
        "s",
    )

    subtotal = (
        Decimal(
            str(
                raw or "0.00",
            ),
        ).quantize(
            Decimal(
                "0.01",
            ),
        )
    )

    pricing = compute_checkout_totals(
        subtotal,
    )

    order.subtotal = subtotal

    order.tax_total = pricing[
        "tax_total"
    ].quantize(
        Decimal(
            "0.01",
        ),
    )

    order.discount_total = pricing[
        "discount_total"
    ].quantize(
        Decimal(
            "0.01",
        ),
    )

    order.shipping_total = pricing[
        "shipping_total"
    ].quantize(
        Decimal(
            "0.01",
        ),
    )

    order.grand_total = pricing[
        "grand_total"
    ]


@transaction.atomic
def cancel_entire_order_for_user(
    user,
    order_number,
    *,
    reason=None,
):

    reason_clean = _normalize_cancel_reason(
        reason,
    )

    order = (
        Order.objects.select_for_update().prefetch_related(
            "lines",
        ).get(
            user=user,
            order_number=order_number,
        )
    )

    if order.status == Order.Status.CANCELLED:

        raise ValidationError(
            "This order is already cancelled.",
        )

    lines = list(
        order.lines.select_related(
            "variant",
        ).all(),
    )

    active = [
        ln
        for ln in lines
        if ln.status == OrderLine.LineStatus.ACTIVE
    ]

    if not active:

        raise ValidationError(
            "This order has no active items to cancel.",
        )

    for ln in active:

        if ln.fulfillment_status != OrderLine.FulfillmentStatus.PENDING:

            raise ValidationError(
                "The order can no longer be cancelled because one or more "
                "items have already shipped.",
            )

    for line in active:

        variant = (
            ProductVariant.objects.select_for_update().get(
                pk=line.variant_id,
            )
        )

        variant.stock += line.quantity

        variant.save(
            update_fields=[
                "stock",
                "updated_at",
            ],
        )

        line.status = OrderLine.LineStatus.CANCELLED

        line.save(
            update_fields=[
                "status",
            ],
        )

    order.cancelled_at = timezone.now()

    order.cancellation_reason = reason_clean

    _set_order_financials_zero(
        order,
    )

    order.save(
        update_fields=[
            "cancelled_at",
            "cancellation_reason",
            "subtotal",
            "tax_total",
            "discount_total",
            "shipping_total",
            "grand_total",
            "updated_at",
        ],
    )

    persist_derived_order_status(
        order.id,
    )

    order.refresh_from_db()

    return order


@transaction.atomic
def cancel_order_line_for_user(
    user,
    order_number,
    line_id,
    *,
    reason=None,
):

    reason_clean = _normalize_cancel_reason(
        reason,
    )

    order = Order.objects.select_for_update().get(
        user=user,
        order_number=order_number,
    )

    if order.status == Order.Status.CANCELLED:

        raise ValidationError(
            "This order is already cancelled.",
        )

    line = (
        OrderLine.objects.select_related(
            "variant",
        ).select_for_update().get(
            pk=line_id,
            order=order,
        )
    )

    if line.status != OrderLine.LineStatus.ACTIVE:

        raise ValidationError(
            "This line is already cancelled.",
        )

    if line.fulfillment_status != OrderLine.FulfillmentStatus.PENDING:

        raise ValidationError(
            "This line can no longer be cancelled because it has already "
            "entered fulfillment.",
        )

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

    line.status = OrderLine.LineStatus.CANCELLED

    update_line = [
        "status",
    ]

    if reason_clean:

        line.cancellation_reason = reason_clean

        update_line.append(
            "cancellation_reason",
        )

    line.save(
        update_fields=update_line,
    )

    remaining_active = order.lines.filter(
        status=OrderLine.LineStatus.ACTIVE,
    ).count()

    if remaining_active == 0:

        order.cancelled_at = timezone.now()

        order.cancellation_reason = reason_clean

        _set_order_financials_zero(
            order,
        )

        order.save(
            update_fields=[
                "cancelled_at",
                "cancellation_reason",
                "subtotal",
                "tax_total",
                "discount_total",
                "shipping_total",
                "grand_total",
                "updated_at",
            ],
        )

    else:

        _recalculate_order_financials_from_active_lines(
            order,
        )

        order.save(
            update_fields=[
                "subtotal",
                "tax_total",
                "discount_total",
                "shipping_total",
                "grand_total",
                "updated_at",
            ],
        )

    persist_derived_order_status(
        order.id,
    )

    order.refresh_from_db()

    return order


@transaction.atomic
def cancel_entire_order_for_admin(
    order_number,
    *,
    reason=None,
):

    """
    Cancel every active line on an order and restore stock.
    Same rules as customer cancel: only lines still in ``pending`` fulfillment.
    """

    reason_clean = _normalize_cancel_reason(
        reason,
    )

    order = (
        Order.objects.select_for_update().prefetch_related(
            "lines",
        ).get(
            order_number=order_number,
        )
    )

    if order.status == Order.Status.CANCELLED:

        raise ValidationError(
            "This order is already cancelled.",
        )

    lines = list(
        order.lines.select_related(
            "variant",
        ).all(),
    )

    active = [
        ln
        for ln in lines
        if ln.status == OrderLine.LineStatus.ACTIVE
    ]

    if not active:

        raise ValidationError(
            "This order has no active items to cancel.",
        )

    for ln in active:

        if ln.fulfillment_status != OrderLine.FulfillmentStatus.PENDING:

            raise ValidationError(
                "The order can no longer be cancelled because one or more "
                "items have already shipped.",
            )

    for line in active:

        variant = (
            ProductVariant.objects.select_for_update().get(
                pk=line.variant_id,
            )
        )

        variant.stock += line.quantity

        variant.save(
            update_fields=[
                "stock",
                "updated_at",
            ],
        )

        line.status = OrderLine.LineStatus.CANCELLED

        line.save(
            update_fields=[
                "status",
            ],
        )

    order.cancelled_at = timezone.now()

    order.cancellation_reason = reason_clean

    _set_order_financials_zero(
        order,
    )

    order.save(
        update_fields=[
            "cancelled_at",
            "cancellation_reason",
            "subtotal",
            "tax_total",
            "discount_total",
            "shipping_total",
            "grand_total",
            "updated_at",
        ],
    )

    persist_derived_order_status(
        order.id,
    )

    order.refresh_from_db()

    return order
