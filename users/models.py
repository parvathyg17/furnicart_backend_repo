import random
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):

    email = models.EmailField(unique=True)

    phone_number = models.CharField(max_length=15, blank=True, null=True)

    # 🔐 control fields
    is_verified = models.BooleanField(default=False)
    is_blocked = models.BooleanField(default=False)

    # timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.email
    







class OTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def is_expired(self):
        return timezone.now() > self.expires_at

    @staticmethod
    def generate_otp():
        return str(random.randint(100000, 999999))