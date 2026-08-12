from django.db.models import Q

from catalog.models import Category


def get_user_filtered_categories(params):

    search = params.get("search", "")

    categories = (
        Category.objects.select_related("parent")
        .prefetch_related("children")
        .filter(is_active=True)
        .order_by("-created_at")
    )

    if search:

        categories = categories.filter(Q(name__icontains=search))

    return categories


def get_admin_filtered_categories(params):

    search = params.get("search", "")

    is_active = params.get("is_active")

    sort = params.get("sort")

    categories = Category.objects.select_related("parent").prefetch_related("children")

    if search:

        categories = categories.filter(Q(name__icontains=search))

    if is_active == "true":

        categories = categories.filter(is_active=True).exclude(parent__is_active=False)

    elif is_active == "false":

        categories = categories.filter(is_active=False)

    if sort == "a_z":

        categories = categories.order_by("name")

    elif sort == "z_a":

        categories = categories.order_by("-name")

    elif sort == "oldest":

        categories = categories.order_by("created_at")

    else:

        categories = categories.order_by("-created_at")

    return categories


def get_all_child_categories(category):

    categories = [category]

    for child in category.children.all():

        categories.extend(get_all_child_categories(child))

    return categories


def get_category_ancestor_ids_map():
    """
    Returns a dictionary mapping each active category ID to a list of its active ancestor category IDs (including itself).
    Example: {child_id: [child_id, parent_id, grandparent_id]}
    """
    all_cats = {
        c["id"]: c["parent_id"]
        for c in Category.objects.filter(is_active=True).values("id", "parent_id")
    }

    mapping = {}
    for cat_id in all_cats:
        ancestors = []
        curr = cat_id
        visited = set()
        while curr and curr not in visited:
            visited.add(curr)
            if curr in all_cats:
                ancestors.append(curr)
                curr = all_cats[curr]
            else:
                break
        mapping[cat_id] = ancestors

    return mapping

