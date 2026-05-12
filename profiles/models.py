from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    phone = models.CharField(
        max_length=15,
        blank=True,
        null=True,
        unique=True
    )

    date_of_birth = models.DateField(
        blank=True,
        null=True
    )

    profile_image = models.ImageField(
        upload_to="profile_images/",
        blank=True,
        null=True
    )

    def __str__(self):
        return str(self.user)