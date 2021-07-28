from django.dispatch import receiver
from django.db.models.signals import post_delete, post_save
from .models import Project, defaultImagePath


@receiver(post_save, sender=Project)
def on_project_create(sender, instance, created, **kwargs):
    """
    Project submitted.
    """
    if created:
        if instance.creator.xp:
            instance.creator.xp = instance.creator.xp + 2
        else:
            instance.creator.xp = 2
        instance.creator.save()


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
