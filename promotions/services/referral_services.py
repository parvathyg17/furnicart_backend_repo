import secrets
import string

from datetime import timedelta
from decimal import Decimal

from django.db import IntegrityError, transaction
from django.utils import timezone

from orders.models import Order
from promotions.models import (
    Coupon,
    ReferralAttribution,
    ReferralCode,
    ReferralProgram,
)


def get_active_referral_program():

    return (
        ReferralProgram.objects.filter(
            is_active=True,
        )
        .order_by(
            "-id",
        )
        .first()
    )


def _generate_referral_code_value(
    length=8,
):

    alphabet = (
        string.ascii_uppercase
        + string.digits
    )

    return "".join(
        secrets.choice(
            alphabet,
        )
        for _ in range(
            length,
        )
    )


def _generate_unique_token():

    return secrets.token_urlsafe(
        16,
    )


def _generate_unique_coupon_code(
    prefix="WELCOME",
):

    for _ in range(
        30,
    ):

        code = (
            f"{prefix}"
            f"{secrets.token_hex(3).upper()}"
        )

        if not Coupon.objects.filter(
            code=code,
        ).exists():

            return code

    raise RuntimeError(
        "Could not generate unique coupon code.",
    )


@transaction.atomic
def get_or_create_referral_code(
    user,
):

    existing = (
        ReferralCode.objects.filter(
            user=user,
        ).first()
    )

    if existing is not None:

        return existing

    for _ in range(
        30,
    ):

        code = _generate_referral_code_value()

        token = _generate_unique_token()

        try:

            return ReferralCode.objects.create(
                user=user,
                code=code,
                token=token,
            )

        except IntegrityError:

            continue

    raise RuntimeError(
        "Could not generate referral code.",
    )


def resolve_referrer_from_input(
    *,
    referral_token=None,
    referral_code=None,
):

    token = (
        str(
            referral_token or "",
        )
        .strip()
    )

    code = (
        str(
            referral_code or "",
        )
        .strip()
        .upper()
    )

    if token:

        referral = (
            ReferralCode.objects.select_related(
                "user",
            )
            .filter(
                token=token,
            )
            .first()
        )

        if referral is not None:

            return referral.user

    if code:

        referral = (
            ReferralCode.objects.select_related(
                "user",
            )
            .filter(
                code=code,
            )
            .first()
        )

        if referral is not None:

            return referral.user

    return None


def _create_referee_coupon(
    referee,
    program,
):

    valid_until = None

    if program.referee_coupon_valid_days:

        valid_until = (
            timezone.now()
            + timedelta(
                days=program.referee_coupon_valid_days,
            )
        )

    return Coupon.objects.create(
        code=_generate_unique_coupon_code(),
        description="Referral welcome offer",
        discount_type=program.referee_discount_type,
        discount_value=program.referee_discount_value,
        max_discount_amount=program.referee_max_discount_amount,
        valid_until=valid_until,
        max_redemptions_total=1,
        max_redemptions_per_user=1,
        assigned_user=referee,
        is_active=True,
    )


@transaction.atomic
def try_attach_referral_on_signup(
    referee,
    *,
    referral_token=None,
    referral_code=None,
):

    if ReferralAttribution.objects.filter(
        referee=referee,
    ).exists():

        return None

    program = get_active_referral_program()

    if program is None:

        return None

    referrer = resolve_referrer_from_input(
        referral_token=referral_token,
        referral_code=referral_code,
    )

    if referrer is None:

        return None

    if referrer.pk == referee.pk:

        return None

    referral_code_row = get_or_create_referral_code(
        referrer,
    )

    coupon = _create_referee_coupon(
        referee,
        program,
    )

    attribution = ReferralAttribution.objects.create(
        referee=referee,
        referrer=referrer,
        referral_code=referral_code_row,
        referee_coupon=coupon,
    )

    return attribution


def referee_welcome_coupon_payload(
    user,
):

    attribution = (
        ReferralAttribution.objects.select_related(
            "referee_coupon",
        )
        .filter(
            referee=user,
        )
        .first()
    )

    if attribution is None:

        return None

    coupon = attribution.referee_coupon

    if coupon is None:

        return None

    from promotions.services.coupon_validation import (
        count_user_coupon_redemptions,
    )

    uses = count_user_coupon_redemptions(
        user,
        coupon,
    )

    return {
        "code": coupon.code,
        "description": coupon.description,
        "discount_type": coupon.discount_type,
        "discount_value": str(
            coupon.discount_value.quantize(
                Decimal(
                    "0.01",
                ),
            ),
        ),
        "is_used": uses > 0,
        "is_active": coupon.is_active,
    }


def referral_program_summary(
    program,
):

    if program is None:

        return None

    if (
        program.referee_discount_type
        == Coupon.DiscountType.PERCENT
    ):

        benefit = (
            f"{program.referee_discount_value.quantize(Decimal('0.01'))}% off"
        )

        if program.referee_max_discount_amount is not None:

            benefit += (
                f" (up to ₹{program.referee_max_discount_amount.quantize(Decimal('0.01'))})"
            )

    else:

        benefit = (
            f"₹{program.referee_discount_value.quantize(Decimal('0.01'))} off"
        )

    return {
        "referee_benefit": benefit,
        "referrer_reward_amount": str(
            program.referrer_reward_amount.quantize(
                Decimal(
                    "0.01",
                ),
            ),
        ),
    }


@transaction.atomic
def process_referral_referrer_reward(
    order,
):

    if order.payment_status != Order.PaymentStatus.PAID:

        return False

    if order.status == Order.Status.CANCELLED:

        return False

    referee = order.user

    attribution = (
        ReferralAttribution.objects.select_related(
            "referrer",
        )
        .filter(
            referee=referee,
            referrer_rewarded=False,
        )
        .first()
    )

    if attribution is None:

        return False

    paid_orders = (
        Order.objects.filter(
            user=referee,
            payment_status=Order.PaymentStatus.PAID,
        )
        .exclude(
            status=Order.Status.CANCELLED,
        )
        .count()
    )

    if paid_orders != 1:

        return False

    program = get_active_referral_program()

    if program is None:

        return False

    amount = program.referrer_reward_amount

    if amount <= Decimal(
        "0.00",
    ):

        return False

    from accounts.models.wallet import WalletTransaction
    from accounts.services.wallet_services import credit_wallet

    credit_wallet(
        attribution.referrer,
        amount,
        reason=WalletTransaction.Reason.REFERRAL_REWARD,
        order=order,
        reference_note=(
            f"Referral reward for order {order.order_number}"
        ),
    )

    attribution.referrer_rewarded = True

    attribution.referrer_reward_order = order

    attribution.save(
        update_fields=[
            "referrer_rewarded",
            "referrer_reward_order",
        ],
    )

    return True
