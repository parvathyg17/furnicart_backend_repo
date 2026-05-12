from django.db import models
from django.db.models import Q
from django.core.validators import RegexValidator

from users.models import User


class Address(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="addresses"
    )

    name = models.CharField(max_length=100)

    phone = models.CharField(
        max_length=15,
        validators=[
            RegexValidator(
                regex=r'^\+?\d{10,15}$',
                message="Enter a valid phone number"
            )
        ]
    )

    address_line = models.TextField()

    city = models.CharField(max_length=100)

    state = models.CharField(max_length=100)

    pincode = models.CharField(
        max_length=10,
        validators=[
            RegexValidator(
                regex=r'^\d{6}$',
                message="Enter a valid pincode"
            )
        ]
    )

    is_default = models.BooleanField(default=False)

    is_deleted = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:

        ordering = ["-is_default", "-id"]

        constraints = [
            models.UniqueConstraint(
                fields=["user"],
                condition=Q(is_default=True),
                name="unique_default_address_per_user"
            )
        ]

    def __str__(self):
        return f"{self.user.email} - {self.name}"