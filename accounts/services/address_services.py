# from django.db import transaction
# from accounts.models.address import Address


# @transaction.atomic
# def set_default_address(user, selected_address):

    
#     Address.objects.select_for_update().filter(
#         user=user,
#         is_default=True
#     ).exclude(
#         id=selected_address.id
#     ).update(is_default=False)

    
#     selected_address.is_default = True
#     selected_address.save()
from django.db import transaction

from accounts.models.address import Address


@transaction.atomic
def set_default_address(
    user,
    selected_address
):

    

    selected = (
        Address.objects
        .select_for_update()
        .get(
            pk=selected_address.pk,
            user=user,
            is_deleted=False
        )
    )

    

    other_addresses = (
        Address.objects
        .select_for_update()
        .filter(
            user=user,
            is_default=True,
            is_deleted=False
        )
        .exclude(
            pk=selected.pk
        )
    )

    

    for address in other_addresses:

        address.is_default = False

        address.save(
            update_fields=["is_default"]
        )

   

    selected.is_default = True

    selected.save(
        update_fields=["is_default"]
    )