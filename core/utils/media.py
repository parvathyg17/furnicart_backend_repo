from PIL import Image


def resolve_media_url(file_field, request=None):
    if not file_field:
        return None

    url = file_field.url

    if url.startswith(("http://", "https://")):
        return url

    if request:
        return request.build_absolute_uri(url)

    return url


def get_image_dimensions(image_field):
    if not image_field:
        return None, None

    try:
        image_field.seek(0)
    except (AttributeError, OSError, ValueError):
        pass

    try:
        with Image.open(image_field) as img:
            img.load()
            return img.width, img.height
    except Exception:
        pass

    try:
        with image_field.open("rb") as file_obj:
            with Image.open(file_obj) as img:
                img.load()
                return img.width, img.height
    except Exception:
        return None, None
    finally:
        try:
            image_field.seek(0)
        except (AttributeError, OSError, ValueError):
            pass


def get_file_size(image_field):
    if not image_field:
        return None

    try:
        size = image_field.size
        if size is not None:
            return size
    except Exception:
        pass

    try:
        with image_field.open("rb") as file_obj:
            file_obj.seek(0, 2)
            return file_obj.tell()
    except Exception:
        return None
