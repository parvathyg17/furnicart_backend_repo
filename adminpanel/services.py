from django.contrib.auth import authenticate


def admin_login_service(email, password):

    user = authenticate(email=email, password=password)

    if user is None:
        return None, "Invalid credentials"

    if not user.is_staff:
        return None, "Not authorized as admin"

    return user, None