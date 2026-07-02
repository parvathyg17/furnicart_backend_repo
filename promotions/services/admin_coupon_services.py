from django.db import transaction

from promotions.models import Coupon


@transaction.atomic
def create_coupon(
    validated_data,
):

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

    pk = instance.pk
    instance.delete()

    return pk
