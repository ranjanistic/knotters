from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from main.methods import addMethodToAsyncQueue

from .apps import APPNAME
from .mailers import freeProjectCreated, freeProjectDeleted
from .models import (Asset, BaseProject, CoreProject, FreeProject, Project,
                     Snapshot, defaultImagePath)


@receiver(post_save, sender=Project)
def on_project_create(sender, instance: Project, created, **kwargs):
    """
    Project submitted.
    """
    if created:
        instance.creator.increaseXP(by=2)


@receiver(post_save, sender=FreeProject)
def on_freeproject_create(sender, instance: FreeProject, created, **kwargs):
    """
    Project submitted.
    """
    if created:
        instance.creator.increaseXP(by=2)
        addMethodToAsyncQueue(
            f"{APPNAME}.mailers.{freeProjectCreated.__name__}", instance)


@receiver(post_delete, sender=Project)
def on_project_delete(sender, instance, **kwargs):
    """
    Project cleanup.
    """
    try:
        if instance.image != defaultImagePath() and not BaseProject.objects.filter(image=instance.image).exists():
            instance.image.delete(save=False)
    except Exception as e:
        pass


@receiver(post_delete, sender=Asset)
def on_asset_delete(sender, instance, **kwargs):
    """
    Project cleanup.
    """
    try:
        instance.file.delete(save=False)
    except Exception as e:
        pass


@receiver(post_delete, sender=FreeProject)
def on_freeproject_delete(sender, instance, **kwargs):
    """
    Project cleanup.
    """

    try:
        if instance.image != defaultImagePath() and not BaseProject.objects.filter(image=instance.image).exists():
            instance.image.delete(save=False)
    except Exception as e:
        pass
    addMethodToAsyncQueue(
        f"{APPNAME}.mailers.{freeProjectDeleted.__name__}", instance)


@receiver(post_delete, sender=CoreProject)
def on_coreproject_delete(sender, instance, **kwargs):
    """
    Project cleanup.
    """

    try:
        if instance.image != defaultImagePath() and not BaseProject.objects.filter(image=instance.image).exists():
            instance.image.delete(save=False)
    except Exception as e:
        pass


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

# @receiver(post_save, sender=ProjectTransferInvitation)
# def on_transfer_invite_create(sender, instance, created, **kwargs):
#     """
#     Project invitaion created.
#     """
#     if created:
#         addMethodToAsyncQueue(f"{APPNAME}.mailers.{projectTransferInvitation.__name__}",instance)

# @receiver(post_save, sender=ProjectModerationTransferInvitation)
# def on_transfer_invite_create(sender, instance, created, **kwargs):
#     """
#     Verified Project invitaion created.
#     """
#     if created:
#         addMethodToAsyncQueue(f"{APPNAME}.mailers.{projectModTransferInvitation.__name__}",instance)

# @receiver(post_save, sender=CoreModerationTransferInvitation)
# def on_transfer_invite_create(sender, instance, created, **kwargs):
#     """
#     Core Project invitaion created.
#     """
#     if created:
#         addMethodToAsyncQueue(f"{APPNAME}.mailers.{coreProjectModTransferInvitation.__name__}",instance)
