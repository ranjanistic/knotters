from django.db.models.signals import post_save, pre_save
from django.db.models import Q
from django.dispatch import receiver
from main.exceptions import IllegalModeration, IllegalModerator, IllegalModerationType, IllegalModerationState, DuplicateKeyError
from main.methods import addMethodToAsyncQueue
from main.strings import moderation
from .models import LocalStorage, Moderation
from .mailers import moderationAssignedAlert
from .methods import getModelByType
from .apps import APPNAME


@receiver(pre_save, sender=LocalStorage)
def before_localstore_update(sender, instance:LocalStorage, raw, **kwargs):
    if LocalStorage.objects.filter(~Q(id=instance.id),key=instance.key).count() > 0:
        raise DuplicateKeyError()

@receiver(pre_save, sender=Moderation)
def before_moderation_update(sender, instance:Moderation, raw, **kwargs):
    if not instance.moderator.is_moderator:
        raise IllegalModerator()
    if instance.type not in moderation.TYPES:
        raise IllegalModerationType()
    if instance.status not in moderation.MODSTATES:
        raise IllegalModerationState()

    if not isinstance(instance.getModerateeFieldByType(),getModelByType(instance.type)):
        raise IllegalModeration()


@receiver(post_save, sender=Moderation)
def on_moderation_update(sender, instance, created, **kwargs):
    if created:
        addMethodToAsyncQueue(f"{APPNAME}.mailers.{moderationAssignedAlert.__name__}",instance)
