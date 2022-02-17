from django.core.cache import cache
from django.dispatch import receiver
from django.db.models.signals import post_delete, post_save
from main.methods import addMethodToAsyncQueue
from .mailers import managementInvitationSent, managementPersonRemoved, newContactRequestAlert
from .models import ContactRequest, ManagementInvitation, ManagementPerson, ThirdPartyAccount
from .apps import APPNAME


@receiver(post_save, sender=ManagementInvitation)
def on_people_mgminvite_create(sender, instance, created, **kwargs):
    """
    Management invitaion created.
    """
    if created:
        addMethodToAsyncQueue(f"{APPNAME}.mailers.{managementInvitationSent.__name__}",instance)

@receiver(post_save, sender=ContactRequest)
def on_people_mgminvite_create(sender, instance, created, **kwargs):
    """
    Management invitaion created.
    """
    if created:
        addMethodToAsyncQueue(f"{APPNAME}.mailers.{newContactRequestAlert.__name__}",instance)

@receiver(post_delete, sender=ManagementPerson)
def on_people_mgm_delete(sender, instance, **kwargs):
    """
    Management person deleted
    """
    ManagementInvitation.objects.filter(receiver=instance.person,management=instance.management).delete()
    

@receiver(post_delete, sender=ThirdPartyAccount)
def on_tpa_delete(sender, instance, **kwargs):
    """
    Management person deleted
    """
    cache.delete(ThirdPartyAccount.cachekey)
    
