from django.db.models import Q

from catalog.models import Category


def get_filtered_categories(params):

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

def get_all_child_categories(category):

    categories = [category]

    for child in category.children.all():

        categories.extend(
            get_all_child_categories(child)
        )

    return categories