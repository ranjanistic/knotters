from django.dispatch import receiver
from django.db.models.signals import post_delete, post_save
from main.methods import addMethodToAsyncQueue
from .mailers import managementInvitationSent, managementPersonRemoved
from .models import ManagementInvitation, ManagementPerson
from .apps import APPNAME


@receiver(post_save, sender=ManagementInvitation)
def on_people_mgminvite_create(sender, instance, created, **kwargs):
    """
    Management invitaion created.
    """
    if created:
        addMethodToAsyncQueue(f"{APPNAME}.mailers.{managementInvitationSent.__name__}",instance)

@receiver(post_delete, sender=ManagementPerson)
def on_people_mgm_delete(sender, instance, **kwargs):
    """
    Management person deleted
    """
    ManagementInvitation.objects.filter(receiver=instance.person,management=instance.management).delete()
    
