from users.models import User, OTP
from core.utils.email import send_otp_email
from django.utils import timezone
from datetime import timedelta
import random

def send_email_change_otp(user, new_email):

    otp_code = OTP.generate_otp()
    expiry = timezone.now() + timedelta(minutes=5)

    OTP.objects.filter(
        user=user,
        purpose="email_change"
    ).delete()

    OTP.objects.create(
        user=user,
        purpose="email_change",
        otp=otp_code,
        expires_at=expiry,
        extra_data={"new_email": new_email}
    )

    send_otp_email(new_email, otp_code)

    return otp_code

def verify_email_change(user, new_email, otp_input):

    otp_obj = OTP.objects.filter(
        user=user,
        purpose="email_change"
    ).order_by("-created_at").first()

    if not otp_obj:
        return False, "OTP not found"

    if otp_obj.is_expired():
        return False, "OTP expired"

    if otp_obj.otp != otp_input:
        return False, "Invalid OTP"

    stored_email = (otp_obj.extra_data or {}).get("new_email")

    if stored_email != new_email:
        return False, "Email mismatch"

    if User.objects.filter(email=new_email).exists():
        return False, "Email already in use"

    user.email = new_email
    user.save()

    otp_obj.delete()

    return True, None