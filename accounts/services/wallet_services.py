from decimal import Decimal

from django.db import transaction

from rest_framework.exceptions import ValidationError

from accounts.models.wallet import Wallet, WalletTransaction


def _quantize_amount(
    amount,
):

    return (
        Decimal(
            str(
                amount,
            ),
        ).quantize(
            Decimal(
                "0.01",
            ),
        )
    )


def ensure_wallet(
    user,
):

    wallet, _ = Wallet.objects.get_or_create(
        user=user,
        defaults={
            "balance": Decimal(
                "0.00",
            ),
        },
    )

    return wallet


@transaction.atomic
def _locked_wallet(
    user,
):

    ensure_wallet(
        user,
    )

    return (
        Wallet.objects.select_for_update().get(
            user=user,
        )
    )


def get_wallet_balance(
    user,
):

    wallet = (
        Wallet.objects.filter(
            user=user,
        ).first()
    )

    if wallet is None:

        return Decimal(
            "0.00",
        )

    return wallet.balance


@transaction.atomic
def credit_wallet(
    user,
    amount,
    *,
    reason=WalletTransaction.Reason.OTHER,
    order=None,
    return_request=None,
    reference_note="",
):

    amount = _quantize_amount(
        amount,
    )

    if amount <= Decimal(
        "0.00",
    ):

        raise ValidationError(
            "Credit amount must be greater than zero.",
        )

    wallet = _locked_wallet(
        user,
    )

    wallet.balance = (
        wallet.balance + amount
    ).quantize(
        Decimal(
            "0.01",
        ),
    )

    wallet.save(
        update_fields=[
            "balance",
            "updated_at",
        ],
    )

    txn = WalletTransaction.objects.create(
        wallet=wallet,
        type=WalletTransaction.Type.CREDIT,
        amount=amount,
        reason=reason,
        order=order,
        return_request=return_request,
        reference_note=(
            reference_note or ""
        )[
            :255
        ],
        balance_after=wallet.balance,
    )

    return wallet, txn


@transaction.atomic
def debit_wallet(
    user,
    amount,
    *,
    reason=WalletTransaction.Reason.OTHER,
    order=None,
    reference_note="",
):

    amount = _quantize_amount(
        amount,
    )

    if amount <= Decimal(
        "0.00",
    ):

        raise ValidationError(
            "Debit amount must be greater than zero.",
        )

    wallet = _locked_wallet(
        user,
    )

    if wallet.balance < amount:

        raise ValidationError(
            "Insufficient wallet balance.",
        )

    wallet.balance = (
        wallet.balance - amount
    ).quantize(
        Decimal(
            "0.01",
        ),
    )

    wallet.save(
        update_fields=[
            "balance",
            "updated_at",
        ],
    )

    txn = WalletTransaction.objects.create(
        wallet=wallet,
        type=WalletTransaction.Type.DEBIT,
        amount=amount,
        reason=reason,
        order=order,
        reference_note=(
            reference_note or ""
        )[
            :255
        ],
        balance_after=wallet.balance,
    )

    return wallet, txn
