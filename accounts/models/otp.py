import random

from django.db import models
from django.utils import timezone

from .users import User


class OTP(models.Model):

    PURPOSE_CHOICES = (
        ("signup", "Signup"),
        ("forgot_password", "Forgot Password"),
        ("email_change", "Email Change"),
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    purpose = models.CharField(
        max_length=30,
        choices=PURPOSE_CHOICES
    )

    otp = models.CharField(max_length=6)

    extra_data = models.JSONField(
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    expires_at = models.DateTimeField()

    def is_expired(self):
        return timezone.now() > self.expires_at

    @staticmethod
    def generate_otp():
        return str(random.randint(100000, 999999))