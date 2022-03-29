from os import remove as os_remove, path as os_path
from django.dispatch import receiver
from django.db.models.signals import post_delete
from django.conf import settings
from .models import ParticipantCertificate,AppreciationCertificate

@receiver(post_delete, sender=ParticipantCertificate)
def on_cert_delete(sender, instance, **kwargs):
    try:
        if instance.certificate:
            os_remove(os_path.join(settings.MEDIA_ROOT, instance.certificate))
        if instance.certficateImage:
            os_remove(os_path.join(settings.MEDIA_ROOT, instance.certficateImage))
    except:
        pass

@receiver(post_delete, sender=AppreciationCertificate)
def on_appcert_delete(sender, instance, **kwargs):
    try:
        if instance.certificate:
            os_remove(os_path.join(settings.MEDIA_ROOT, instance.certificate))
        if instance.certficateImage:
            os_remove(os_path.join(settings.MEDIA_ROOT, instance.certficateImage))
    except:
        pass
