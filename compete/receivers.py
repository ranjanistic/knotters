import os
from django.dispatch import receiver
from django.db.models.signals import post_delete
from django.conf import settings
from .models import ParticipantCertificate

@receiver(post_delete, sender=ParticipantCertificate)
def on_cert_delete(sender, instance, **kwargs):
    try:
        if instance.certificate:
            os.remove(os.path.join(settings.MEDIA_ROOT, instance.certificate))
        if instance.certficateImage:
            os.remove(os.path.join(settings.MEDIA_ROOT, instance.certficateImage))
    except:
        pass
