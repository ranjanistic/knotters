from .models import Project, defaultImagePath
from django.dispatch import receiver
from django.db.models.signals import post_delete

@receiver(post_delete, sender=Project)
def on_project_delete(sender, instance, **kwargs):
    """
    Project cleanup.
    """
    try:
        if instance.image != defaultImagePath():
            instance.image.delete(save=False)
    except Exception as e:
        pass
