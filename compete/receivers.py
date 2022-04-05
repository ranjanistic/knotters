from os import path as os_path
from os import remove as os_remove

from django.conf import settings
from django.db.models.signals import post_delete
from django.dispatch import receiver

from .models import AppreciationCertificate, ParticipantCertificate


@receiver(post_delete, sender=ParticipantCertificate)
def on_cert_delete(sender, instance: ParticipantCertificate, **kwargs):
    """To remove certificate media on Participant Certificate instance deletion
    """
    try:
        if instance.certificate:
            os_remove(os_path.join(settings.MEDIA_ROOT, instance.certificate))
        if instance.certficateImage:
            os_remove(os_path.join(settings.MEDIA_ROOT,
                      instance.certficateImage))
    except:
        pass


@receiver(post_delete, sender=AppreciationCertificate)
def on_appcert_delete(sender, instance: AppreciationCertificate, **kwargs):
    """To remove certificate media on Appreciant Certificate instance deletion
    """
    try:
        if instance.certificate:
            os_remove(os_path.join(settings.MEDIA_ROOT, instance.certificate))
        if instance.certficateImage:
            os_remove(os_path.join(settings.MEDIA_ROOT,
                      instance.certficateImage))
    except:
        pass
