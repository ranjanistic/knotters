from django.dispatch import receiver
from django.db.models.signals import post_delete, post_save
from main.methods import addMethodToAsyncQueue
from .mailers import freeProjectDeleted, freeProjectCreated
from .models import Project, FreeProject, Snapshot, defaultImagePath
from .apps import APPNAME

@receiver(post_save, sender=Project)
def on_project_create(sender, instance:Project, created, **kwargs):
    """
    Project submitted.
    """
    if created:
        instance.creator.increaseXP(by=2)

@receiver(post_save, sender=FreeProject)
def on_freeproject_create(sender, instance:FreeProject, created, **kwargs):
    """
    Project submitted.
    """
    if created:
        instance.creator.increaseXP(by=2)
        addMethodToAsyncQueue(f"{APPNAME}.mailers.{freeProjectCreated.__name__}",instance)


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

@receiver(post_delete, sender=FreeProject)
def on_freeproject_delete(sender, instance, **kwargs):
    """
    Project cleanup.
    """
    
    try:
        if instance.image != defaultImagePath():
            instance.image.delete(save=False)
    except Exception as e:
        pass
    addMethodToAsyncQueue(f"{APPNAME}.mailers.{freeProjectDeleted.__name__}", instance)

@receiver(post_delete, sender=Snapshot)
def on_snap_delete(sender, instance, **kwargs):
    """
    Project cleanup.
    """
    try:
        if instance.video:
            instance.video.delete(save=False)
        if instance.image:
            instance.image.delete(save=False)
    except Exception as e:
        pass