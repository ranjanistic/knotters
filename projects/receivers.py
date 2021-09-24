from django.dispatch import receiver
from django.db.models.signals import post_delete, post_save
from .models import Project, BaseProject, defaultImagePath


@receiver(post_save, sender=BaseProject)
def on_project_create(sender, instance:Project, created, **kwargs):
    """
    Project submitted.
    """
    
    if created:
        instance.creator.increaseXP(by=2)


@receiver(post_delete, sender=BaseProject)
def on_project_delete(sender, instance, **kwargs):
    """
    Project cleanup.
    """
    try:
        if instance.image != defaultImagePath():
            instance.image.delete(save=False)
    except Exception as e:
        pass
