from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

from accounts.models import UserProfile
from accounts.services.wallet_services import ensure_wallet

User = get_user_model()


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):

    if created:
        UserProfile.objects.create(user=instance)
        ensure_wallet(instance)