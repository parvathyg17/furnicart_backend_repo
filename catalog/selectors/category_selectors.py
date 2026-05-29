
from django.db.models import Q

from catalog.models import Category


# =====================================================
# USER CATEGORY
# =====================================================

def get_user_filtered_categories(params):

    search = params.get(
        "search",
        ""
    )

    categories = Category.objects.select_related(
        "parent"
    ).prefetch_related(
        "children"
    ).filter(
        is_active=True
    ).order_by(
        "-created_at"
    )

    if search:

        categories = categories.filter(
            Q(name__icontains=search)
        )

    return categories


# =====================================================
# ADMIN CATEGORY
# =====================================================

def get_admin_filtered_categories(params):

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

    # =========================================
    # BASE QUERYSET
    # =========================================

    categories = Category.objects.select_related(
        "parent"
    ).prefetch_related(
        "children"
    )

    # =========================================
    # SEARCH
    # =========================================

    if search:

        categories = categories.filter(
            Q(name__icontains=search)
        )

    # =========================================
    # STATUS FILTER
    # =========================================

    if is_active == "true":

        categories = categories.filter(
            is_active=True
        ).exclude(
            parent__is_active=False
        )

    elif is_active == "false":

        categories = categories.filter(
            is_active=False
        )

    # =========================================
    # SORTING
    # =========================================

    if sort == "a_z":

        categories = categories.order_by(
            "name"
        )

    elif sort == "z_a":

        categories = categories.order_by(
            "-name"
        )

    elif sort == "oldest":

        categories = categories.order_by(
            "created_at"
        )

    else:

        categories = categories.order_by(
            "-created_at"
        )

    return categories


# =====================================================
# CHILD CATEGORY
# =====================================================

def get_all_child_categories(category):

    categories = [category]

    for child in category.children.all():

        categories.extend(
            get_all_child_categories(child)
        )

    return categories

