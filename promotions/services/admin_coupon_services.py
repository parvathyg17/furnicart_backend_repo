from django.db import transaction

from promotions.models import Coupon


@transaction.atomic
def create_coupon(
    validated_data,
):
    """
    Persist a new coupon after serializer validation.
    """

    instance = Coupon(
        **validated_data,
    )
    instance.full_clean()
    instance.save()

    return instance


@transaction.atomic
def update_coupon(
    instance,
    validated_data,
):
    """
    Apply partial/full updates after serializer validation.
    """

    for key, value in validated_data.items():

        setattr(
            instance,
            key,
            value,
        )

    instance.full_clean()
    instance.save()

    return instance


@transaction.atomic
def delete_coupon(
    instance,
):
    """
    Remove a coupon row (admin only).
    """

    pk = instance.pk
    instance.delete()

    return pk
