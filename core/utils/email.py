from django.conf import settings
from django.core.mail import send_mail


OTP_EXPIRY_MINUTES = 5

PURPOSE_COPY = {
    "signup": {
        "subject_action": "Verify your FurniCart account",
        "headline": "Welcome to FurniCart",
        "intro": (
            "Thank you for joining FurniCart — your destination for curated "
            "furniture and home décor. Use the code below to verify your email "
            "and complete your registration."
        ),
    },
    "forgot_password": {
        "subject_action": "Reset your FurniCart password",
        "headline": "Password reset request",
        "intro": (
            "We received a request to reset the password for your FurniCart "
            "account. Enter the code below to choose a new password and get "
            "back to shopping."
        ),
    },
    "email_change": {
        "subject_action": "Confirm your new FurniCart email",
        "headline": "Confirm email change",
        "intro": (
            "You asked to update the email on your FurniCart account. "
            "Enter the code below to confirm this new address."
        ),
    },
}

DEFAULT_PURPOSE_COPY = {
    "subject_action": "Your FurniCart verification code",
    "headline": "Verification code",
    "intro": (
        "Use the code below to continue on FurniCart, your online furniture "
        "and home shopping store."
    ),
}


def _purpose_key(purpose):
    return str(purpose or "signup").strip().lower()


def build_otp_email_content(otp, purpose="signup"):
    copy = PURPOSE_COPY.get(
        _purpose_key(purpose),
        DEFAULT_PURPOSE_COPY,
    )

    subject = f"FurniCart — {copy['subject_action']}"

    message = f"""{copy['headline']}
{'=' * len(copy['headline'])}

{copy['intro']}

Your one-time password (OTP):

    {otp}

This code expires in {OTP_EXPIRY_MINUTES} minutes.

If you did not request this email, you can safely ignore it. Your FurniCart
account will not be changed unless you enter this code.

Need help? Contact our support team through your account profile after signing in.

—
FurniCart
Curated furniture for calm, considered spaces.
Your online furniture & home décor store.
"""

    return subject, message


def send_otp_email(email, otp, purpose="signup"):
    subject, message = build_otp_email_content(
        otp,
        purpose=purpose,
    )

    send_mail(
        subject,
        message,
        settings.EMAIL_HOST_USER,
        [email],
        fail_silently=False,
    )
