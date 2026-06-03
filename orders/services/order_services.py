from decimal import Decimal

from django.db import IntegrityError, transaction
from django.db.models import Prefetch
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
    tax_total=None,
    discount_total=None,
    shipping_total=None,
):

    """
    Validate cart and address, reserve stock, persist order + lines,
    and clear the cart. All-or-nothing inside one database transaction.
    """

    if tax_total is None:

        tax_total = Decimal("0.00")

    if discount_total is None:

        discount_total = Decimal("0.00")

    if shipping_total is None:

        shipping_total = Decimal("0.00")

    for label, value in (
        ("tax_total", tax_total),
        ("discount_total", discount_total),
        ("shipping_total", shipping_total),
    ):

        if value < 0:

            raise ValidationError(
                f"{label} cannot be negative.",
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

    if subtotal + tax_total + shipping_total < discount_total:

        raise ValidationError(
            "Discount cannot exceed subtotal plus tax and shipping.",
        )

    grand_total = (
        subtotal
        + tax_total
        + shipping_total
        - discount_total
    ).quantize(
        Decimal("0.01"),
    )

    if grand_total < Decimal("0.00"):

        grand_total = Decimal("0.00")

    order_number = _allocate_order_number()

    order = Order.objects.create(
        user=user,
        order_number=order_number,
        status=Order.Status.PENDING,
        payment_method=Order.PaymentMethod.COD,
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
            "lines",
        ).get(
            user=user,
            order_number=order_number,
        )
    )
