from django.contrib.auth import authenticate
from .models import OTP
from django.utils import timezone
from datetime import timedelta
from core.utils.email import send_otp_email



def user_login_service(email, password):

    user = authenticate(email=email, password=password)

    if user is None:
        return None, "Invalid email or password"

    if user.is_blocked:
        return None, "User is blocked"

    if not user.is_verified:
        return None, "Email not verified"

    return user, None




def create_and_send_otp(user):
    otp_code = OTP.generate_otp()
    expiry_time = timezone.now() + timedelta(minutes=5)

    # delete old OTPs
    OTP.objects.filter(user=user).delete()

    otp_obj = OTP.objects.create(
        user=user,
        otp=otp_code,
        expires_at=expiry_time
    )

    send_otp_email(user.email, otp_code)

    return otp_obj


def verify_otp_service(user, otp_input):

    try:
        otp_obj = OTP.objects.get(user=user)
    except OTP.DoesNotExist:
        return False, "OTP not found"

    if otp_obj.is_expired():
        return False, "OTP expired"

    if otp_obj.otp != otp_input:
        return False, "Invalid OTP"

    user.is_verified = True
    user.save()

    otp_obj.delete()

    return True, None


def resend_otp_service(user):
    return create_and_send_otp(user)


def forgot_password_service(email):
    from .models import User
    from .services import create_and_send_otp

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return None, "User not found"

    if user.is_blocked:
        return None, "User is blocked"

    create_and_send_otp(user)

    return user, None


def reset_password_service(email, otp_input, new_password):
    from .models import User, OTP

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return False, "User not found"

    try:
        otp_obj = OTP.objects.get(user=user)
    except OTP.DoesNotExist:
        return False, "OTP not found"

    if otp_obj.is_expired():
        return False, "OTP expired"

    if otp_obj.otp != otp_input:
        return False, "Invalid OTP"

    # 🔐 HASHED PASSWORD SET
    user.set_password(new_password)
    user.save()

    otp_obj.delete()

    return True, None