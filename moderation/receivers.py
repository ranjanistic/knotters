from django.db.models import Q
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from main.exceptions import (DuplicateKeyError, IllegalModeration,
                             IllegalModerationState, IllegalModerationType,
                             IllegalModerator)
from main.strings import moderation

from .mailers import moderationAssignedAlert
from .methods import getModelByType
from .models import LocalStorage, Moderation


@receiver(pre_save, sender=LocalStorage)
def before_localstore_update(sender, instance: LocalStorage, raw, **kwargs):
    """Checks if the local storage record being updated has not a duplicate key."""
    if LocalStorage.objects.filter(~Q(id=instance.id), key=instance.key).count() > 0:
        raise DuplicateKeyError()


@receiver(pre_save, sender=Moderation)
def before_moderation_update(sender, instance: Moderation, raw, **kwargs):
    """Checks if the moderation record being updated has valid information."""
    if not (instance.moderator.is_moderator and instance.moderator.is_normal):
        raise IllegalModerator(instance.moderator)
    if instance.type not in moderation.TYPES:
        raise IllegalModerationType(instance.type)
    if instance.status not in moderation.MODSTATES:
        raise IllegalModerationState(instance.status)

    if not isinstance(instance.getModerateeFieldByType(), getModelByType(instance.type)):
        raise IllegalModeration(instance)


@receiver(post_save, sender=Moderation)
def on_moderation_update(sender, instance, created, **kwargs):
    """To alert the moderator when a moderation instance is created."""
    if created:
        moderationAssignedAlert(instance)
