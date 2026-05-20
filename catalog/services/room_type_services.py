from catalog.models import RoomType


def get_room_type_by_id(room_type_id):

    try:

        return RoomType.objects.get(
            id=room_type_id
        )

    except RoomType.DoesNotExist:

        return None


def soft_delete_room_type(room_type):

    room_type.is_active = False

    room_type.save()

    return room_type