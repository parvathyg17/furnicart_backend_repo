from catalog.models import VariantImage


def get_image_by_id(image_id):
    try:
        return VariantImage.objects.get(id=image_id)
    except VariantImage.DoesNotExist:
        return None


def delete_image(image):
    image.delete()
    return True