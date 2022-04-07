from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .mailers import managementInvitationSent, newContactRequestAlert
from .models import (ContactRequest, ManagementInvitation, ManagementPerson,
                     ThirdPartyAccount, ThirdPartyLicense)


@receiver(post_save, sender=ManagementInvitation)
def on_people_mgminvite_create(sender, instance, created, **kwargs):
    """
    Management invitaion created.
    """
    if created:
        managementInvitationSent(instance)


@receiver(post_save, sender=ContactRequest)
def on_contactrequest_create(sender, instance: ContactRequest, created, **kwargs):
    """
    Contact request created
    """
    if created:
        newContactRequestAlert(instance)


@receiver(post_delete, sender=ManagementPerson)
def on_people_mgm_delete(sender, instance, **kwargs):
    """
    Management person deleted
    """
    ManagementInvitation.objects.filter(
        receiver=instance.person, management=instance.management).delete()


@receiver(post_delete, sender=ThirdPartyAccount)
def on_tpa_delete(sender, instance: ThirdPartyAccount, **kwargs):
    """
    Platform Third party account deleted
    """
    instance.reset_all_cache()


@receiver(post_delete, sender=ThirdPartyLicense)
def on_tpl_delete(sender, instance: ThirdPartyLicense, **kwargs):
    """
    Platform tpl deleted
    """
    instance.reset_all_cache()
