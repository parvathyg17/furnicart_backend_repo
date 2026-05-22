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

    room_types = RoomType.objects.all().order_by(
        "name"
    )

    # ==========================================
    # SEARCH
    # ==========================================

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

    return room_types