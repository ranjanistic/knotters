from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Moderation
from .mailers import moderationAssignedAlert

@receiver(post_save, sender=Moderation)
def on_moderation_create(sender, instance, created, **kwargs):
    if created:
        moderationAssignedAlert(instance)
    pass