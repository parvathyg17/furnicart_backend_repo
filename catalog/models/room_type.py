from django.db import models
from django.utils.text import slugify


class RoomType(models.Model):

    name = models.CharField(
        max_length=100,
        unique=True
    )

    slug = models.SlugField(
        unique=True,
        blank=True
    )

    image = models.ImageField(
        upload_to="room-types/",
        blank=True,
        null=True
    )

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:

        ordering = ["name"]

    def save(self, *args, **kwargs):

        if not self.slug:

            base_slug = slugify(self.name)

            slug = base_slug

            counter = 1

            while RoomType.objects.filter(
                slug=slug
            ).exclude(id=self.id).exists():

                slug = f"{base_slug}-{counter}"

                counter += 1

            self.slug = slug

        super().save(*args, **kwargs)

    def __str__(self):

        return self.name