from django.db.models import Q

from catalog.models import RoomType


# =====================================================
# USER ROOM TYPES
# =====================================================

def get_user_filtered_room_types(params):

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


# =====================================================
# ADMIN ROOM TYPES
# =====================================================

def get_admin_filtered_room_types(
    params
):

    search = params.get(
        "search",
        ""
    )

    is_active = params.get(
        "is_active"
    )

    sort = params.get(
        "sort"
    )

    room_types = RoomType.objects.all()

 

    if search:

        room_types = room_types.filter(
            Q(name__icontains=search)
        )

    # ==========================================
    # STATUS FILTER
    # ==========================================

    if is_active == "true":

        room_types = room_types.filter(
            is_active=True
        )

    elif is_active == "false":

        room_types = room_types.filter(
            is_active=False
        )
    # ==========================================
    # SORTING
    # ==========================================

    if sort == "a_z":

        room_types = room_types.order_by(
            "name"
        )

    elif sort == "z_a":

        room_types = room_types.order_by(
            "-name"
        )

    elif sort == "oldest":

        room_types = room_types.order_by(
            "created_at"
        )

    else:

        room_types = room_types.order_by(
            "-created_at"
        )

        

    return room_types