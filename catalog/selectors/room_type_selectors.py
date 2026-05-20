from django.db.models import Q

from catalog.models import RoomType


def get_filtered_room_types(params):

    search = params.get(
        "search",
        ""
    )

    room_types = RoomType.objects.filter(
        is_active=True
    ).order_by(
        "name"
    )

    if search:

        room_types = room_types.filter(
            Q(name__icontains=search)
        )

    return room_types