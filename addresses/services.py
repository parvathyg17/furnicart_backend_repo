from django.db import transaction
from .models import Address


@transaction.atomic
def set_default_address(user, selected_address):

    
    Address.objects.select_for_update().filter(
        user=user,
        is_default=True
    ).exclude(
        id=selected_address.id
    ).update(is_default=False)

    
    selected_address.is_default = True
    selected_address.save()