from catalog.models import Category


def get_category_by_id(category_id):

    try:

        return Category.objects.select_related(
            "parent"
        ).get(
            id=category_id
        )

    except Category.DoesNotExist:

        return None


def soft_delete_category(category):

    category.is_active = False

    category.save()

    for child in category.children.all():

        soft_delete_category(child)

    return category