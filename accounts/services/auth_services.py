from django.contrib.auth import authenticate
from accounts.models.users import User
from accounts.models.otp import OTP
from django.utils import timezone
from datetime import timedelta
from core.utils.email import send_otp_email


def user_login_service(
    email,
    password
):

    try:

        user = User.objects.get(
            email=email
        )

    except User.DoesNotExist:

        return (
            None,
            "Invalid email or password"
        )

    # ==========================
    # BLOCK ADMIN LOGIN
    # ==========================

    if (
        user.is_staff or
        user.is_superuser
    ):

        return (
            None,
            "Admins must login through admin panel"
        )

    # ==========================
    # EMAIL NOT VERIFIED
    # ==========================

    if not user.is_verified:

        return (
            None,
            "Email not verified"
        )

    # ==========================
    # BLOCKED USER
    # ==========================

    if not user.is_active:

        return (
            None,
            "User is blocked"
        )

    # ==========================
    # AUTHENTICATE
    # ==========================

    user = authenticate(
        email=email,
        password=password
    )

    if user is None:

        return (
            None,
            "Invalid email or password"
        )

    return user, None



def create_and_send_otp(user, purpose):
    purpose = purpose.strip().lower()

    otp_code = OTP.generate_otp()
    expiry_time = timezone.now() + timedelta(minutes=5)

    
    OTP.objects.filter(
        user=user,
        purpose=purpose
    ).delete()

    OTP.objects.create(
        user=user,
        purpose=purpose,
        otp=otp_code,
        expires_at=expiry_time
    )

    send_otp_email(user.email, otp_code)

    return otp_code


def verify_otp_service(user, otp_input, purpose):

    purpose = purpose.strip().lower()

    try:
        otp_obj = OTP.objects.get(
            user=user,
            purpose=purpose
        )

    except OTP.DoesNotExist:
        return False, "OTP not found"

    if otp_obj.is_expired():
        otp_obj.delete()
        return False, "OTP expired"

    if otp_obj.otp != otp_input:
        return False, "Invalid OTP"

    # =========================
    # SIGNUP VERIFY
    # =========================

    if purpose == "signup":

        user.is_verified = True
        # user.is_active = True
        user.save()

        # delete signup OTP after verification
        otp_obj.delete()

    return True, None



def resend_otp_service(
    user,
    purpose="signup"
):

    purpose = (
        purpose
        .strip()
        .lower()
    )

    latest_otp = (
        OTP.objects.filter(
            user=user,
            purpose=purpose
        )
        .order_by("-created_at")
        .first()
    )

    # =========================
    # COOLDOWN CHECK
    # =========================

    if latest_otp:

        seconds_passed = (
            timezone.now() -
            latest_otp.created_at
        ).seconds

        cooldown_seconds = 60

        if seconds_passed < cooldown_seconds:

            remaining = (
                cooldown_seconds -
                seconds_passed
            )

            return (
                False,
                f"Please wait {remaining}s before requesting another OTP."
            )

    # =========================
    # CREATE NEW OTP
    # =========================

    create_and_send_otp(
        user,
        purpose
    )

    return (
        True,
        None
    )


def forgot_password_service(email):


    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return None, "User not found"

    if not user.is_active:
        return None, "User is blocked"

    create_and_send_otp(user,"forgot_password")

    return user, None


def reset_password_service(email, otp_input, new_password):

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return False, "User not found"

    try:
        otp_obj = OTP.objects.get(
            user=user,
            purpose="forgot_password"
        )
    except OTP.DoesNotExist:
        return False, "OTP not found"

    if otp_obj.is_expired():
        return False, "OTP expired"

    if otp_obj.otp != otp_input:
        return False, "Invalid OTP"

    user.set_password(new_password)
    user.save()

    otp_obj.delete()

    return True, None


