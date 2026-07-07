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

    html_message = f"""
    <div style="font-family: 'Helvetica Neue', Arial, sans-serif; max-width: 600px; margin: 0 auto; color: #333; line-height: 1.6; border: 1px solid #eaeaea; border-radius: 8px;">
        <div style="text-align: center; padding: 20px 0; border-bottom: 1px solid #eaeaea; background-color: #fafafa; border-top-left-radius: 8px; border-top-right-radius: 8px;">
            <h2 style="margin: 0; color: #2c3e50; font-size: 24px; letter-spacing: 1px;">FurniCart</h2>
        </div>
        <div style="padding: 30px 20px;">
            <h3 style="color: #2c3e50; font-size: 20px; margin-top: 0;">{copy['headline']}</h3>
            <p style="font-size: 16px; color: #555;">
                {copy['intro']}
            </p>
            <div style="margin: 30px 0; padding: 25px; background-color: #f8f9fa; border-radius: 8px; text-align: center; border: 1px dashed #ced4da;">
                <p style="margin: 0 0 10px 0; font-size: 14px; text-transform: uppercase; color: #6c757d; font-weight: bold;">Your one-time password (OTP)</p>
                <div style="font-size: 36px; letter-spacing: 8px; color: #000; font-weight: bold; margin: 10px 0;">{otp}</div>
            </div>
            <p style="font-size: 14px; color: #6c757d;">
                This code expires in <strong>{OTP_EXPIRY_MINUTES} minutes</strong>.
            </p>
            <p style="font-size: 14px; color: #6c757d; margin-top: 30px; border-top: 1px solid #eaeaea; padding-top: 20px;">
                If you did not request this email, you can safely ignore it. Your FurniCart
                account will not be changed unless you enter this code.<br><br>
                Need help? Contact our support team through your account profile after signing in.
            </p>
        </div>
        <div style="background-color: #f8f9fa; padding: 20px; text-align: center; font-size: 12px; color: #999; border-bottom-left-radius: 8px; border-bottom-right-radius: 8px;">
            <strong style="color: #555;">FurniCart</strong><br>
            Curated furniture for calm, considered spaces.<br>
            Your online furniture &amp; home décor store.
        </div>
    </div>
    """

    return subject, message, html_message


def send_otp_email(email, otp, purpose="signup"):
    subject, message, html_message = build_otp_email_content(
        otp,
        purpose=purpose,
    )

    send_mail(
        subject,
        message,
        settings.EMAIL_HOST_USER,
        [email],
        fail_silently=False,
        html_message=html_message,
    )
