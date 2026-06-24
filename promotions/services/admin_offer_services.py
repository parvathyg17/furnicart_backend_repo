from django.db import transaction

from promotions.models import Offer


@transaction.atomic
def create_offer(
    validated_data,
):

    instance = Offer(
        **validated_data,
    )
    instance.full_clean()
    instance.save()

    return instance


@transaction.atomic
def update_offer(
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
def delete_offer(
    instance,
):

    pk = instance.pk
    instance.delete()

    return pk
