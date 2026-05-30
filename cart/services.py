from decimal import Decimal

from django.db import transaction

from rest_framework.exceptions import (
    ValidationError,
)

from catalog.models import ProductVariant

from cart.models import (
    Cart,
    CartItem,
)

from wishlist.models import WishlistItem


MAX_CART_QTY = 10


def get_or_create_cart(user):

    cart, _ = Cart.objects.get_or_create(
        user=user,
    )

    return cart


def _get_variant_for_cart(variant_id):

    try:

        return ProductVariant.objects.select_related(
            "product",
            "product__category",
        ).get(
            pk=variant_id,
        )

    except ProductVariant.DoesNotExist:

        raise ValidationError(
            "Variant not found.",
        )


def _assert_variant_cartable(variant):

    if not variant.product.is_active:

        raise ValidationError(
            "Product unavailable.",
        )

    if not variant.product.category.is_active:

        raise ValidationError(
            "Product unavailable.",
        )

    if not variant.is_active:

        raise ValidationError(
            "Variant unavailable.",
        )


def _format_validation_detail(detail):

    if detail is None:

        return "Unavailable."

    if isinstance(detail, str):

        return detail

    if isinstance(detail, (list, tuple)) and detail:

        return str(detail[0])

    if isinstance(detail, dict):

        parts = []

        for key, val in detail.items():

            if isinstance(val, (list, tuple)) and val:

                parts.append(
                    f"{key}: {val[0]}",
                )

            elif isinstance(val, str):

                parts.append(
                    f"{key}: {val}",
                )

        if parts:

            return "; ".join(parts)

        return str(detail)

    return str(detail)


def get_cart_line_availability(item):

    variant = item.variant

    try:

        _assert_variant_cartable(variant)

    except ValidationError as exc:

        return {
            "status": "unavailable",
            "code": "unavailable",
            "message": _format_validation_detail(
                exc.detail,
            ),
        }

    if variant.stock < 1:

        return {
            "status": "out_of_stock",
            "code": "out_of_stock",
            "message": "This item is out of stock.",
        }

    if item.quantity > variant.stock:

        return {
            "status": "insufficient_stock",
            "code": "insufficient_stock",
            "message": (
                f"Only {variant.stock} left in stock; your cart has "
                f"{item.quantity}. Reduce the quantity to continue."
            ),
        }

    return {
        "status": "ok",
        "code": None,
        "message": None,
    }


def _remove_wishlist_for_variant(
    user,
    variant,
):

    WishlistItem.objects.filter(
        wishlist__user=user,
        variant=variant,
    ).delete()


@transaction.atomic
def add_to_cart(
    user,
    variant_id,
    quantity,
):

    if quantity < 1:

        raise ValidationError(
            "Quantity must be at least 1.",
        )

    variant = _get_variant_for_cart(variant_id)

    _assert_variant_cartable(variant)

    if variant.stock < 1:

        raise ValidationError(
            "This item is out of stock.",
        )

    if quantity > variant.stock:

        raise ValidationError(
            f"Only {variant.stock} available.",
        )

    cart = get_or_create_cart(user)

    item, created = CartItem.objects.get_or_create(
        cart=cart,
        variant=variant,
        defaults={
            "quantity": 0,
        },
    )

    new_qty = (
        quantity
        if created
        else item.quantity + quantity
    )

    if new_qty > variant.stock:

        if variant.stock < 1:

            raise ValidationError(
                "This item is out of stock.",
            )

        raise ValidationError(
            f"Only {variant.stock} available.",
        )

    if new_qty > MAX_CART_QTY:

        raise ValidationError(
            f"Maximum {MAX_CART_QTY} units allowed per item.",
        )

    item.quantity = new_qty

    item.save()

    _remove_wishlist_for_variant(
        user,
        variant,
    )

    return item


@transaction.atomic
def update_cart_item_quantity(
    user,
    item_id,
    quantity,
):

    if quantity < 1:

        raise ValidationError(
            "Quantity must be at least 1.",
        )

    try:

        item = CartItem.objects.select_related(
            "variant",
            "variant__product",
            "variant__product__category",
            "cart",
        ).get(
            pk=item_id,
            cart__user=user,
        )

    except CartItem.DoesNotExist:

        raise ValidationError(
            "Cart item not found.",
        )

    variant = item.variant

    if quantity == item.quantity:

        return item

    if quantity < item.quantity:

        item.quantity = quantity

        item.save()

        return item

    _assert_variant_cartable(variant)

    if variant.stock < 1:

        raise ValidationError(
            "This item is out of stock.",
        )

    if quantity > variant.stock:

        raise ValidationError(
            f"Only {variant.stock} available.",
        )

    if quantity > MAX_CART_QTY:

        raise ValidationError(
            f"Maximum {MAX_CART_QTY} units allowed per item.",
        )

    item.quantity = quantity

    item.save()

    return item


@transaction.atomic
def remove_cart_item(
    user,
    item_id,
):

    deleted_count, _ = CartItem.objects.filter(
        pk=item_id,
        cart__user=user,
    ).delete()

    if deleted_count == 0:

        raise ValidationError(
            "Cart item not found.",
        )


def cart_line_subtotal(item):

    return (
        item.variant.price
        * Decimal(item.quantity)
    )


def get_cart_payload(user):

    cart = get_or_create_cart(user)

    items = (
        CartItem.objects.filter(
            cart=cart,
        )
        .select_related(
            "variant",
            "variant__product",
            "variant__product__category",
        )
        .prefetch_related(
            "variant__images",
        )
        .order_by(
            "-created_at",
        )
    )

    subtotal = Decimal("0")

    count = 0

    can_checkout = True

    for item in items:

        subtotal += cart_line_subtotal(item)

        count += item.quantity

        info = get_cart_line_availability(item)

        if info["status"] != "ok":

            can_checkout = False

    return cart, items, subtotal, count, can_checkout


def validate_cart_for_checkout(user):

    _, items, _, count, _ = get_cart_payload(
        user,
    )

    if count < 1:

        return {
            "valid": False,
            "code": "empty_cart",
            "message": "Your cart is empty.",
            "line_issues": [],
        }

    line_issues = []

    for item in items:

        info = get_cart_line_availability(item)

        if info["status"] != "ok":

            line_issues.append(
                {
                    "item_id": item.id,
                    "product_name": item.variant.product.name,
                    "variant_name": item.variant.variant_name,
                    "quantity": item.quantity,
                    "stock": item.variant.stock,
                    **info,
                },
            )

    if line_issues:

        return {
            "valid": False,
            "code": "cart_not_valid",
            "message": (
                "Some items are sold out, unavailable, or exceed current "
                "stock. Update your cart to continue."
            ),
            "line_issues": line_issues,
        }

    return {
        "valid": True,
        "code": None,
        "message": None,
        "line_issues": [],
    }
