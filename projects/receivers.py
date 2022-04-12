from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .mailers import freeProjectCreated, freeProjectDeleted
from .models import (Asset, BaseProject, BaseProjectCoCreator,
                     BaseProjectCoCreatorInvitation, Category, CoreProject,
                     FreeProject, LegalDoc, Project, Snapshot,
                     defaultImagePath)


@receiver(post_delete, sender=Category)
def on_category_delete(sender, instance: Category, **kwargs):
    """
    Project submitted.
    """
    try:
        instance.reset_all_cache()
    except Exception as e:
        pass


@receiver(post_save, sender=Category)
def on_category_create(sender, instance: Category, created, **kwargs):
    """
    Project submitted.
    """
    if created:
        instance.reset_all_cache()


@receiver(post_save, sender=Project)
def on_project_create(sender, instance: Project, created, **kwargs):
    """
    Project submitted.
    """
    if created:
        instance.creator.increaseXP(
            by=2, reason="Submitted a verified project")


@receiver(post_save, sender=FreeProject)
def on_freeproject_create(sender, instance: FreeProject, created, **kwargs):
    """
    Quick Project submitted.
    """
    if created:
        instance.creator.increaseXP(by=2, reason="Created a Quick project")
        freeProjectCreated(instance)


@receiver(post_delete, sender=Project)
def on_project_delete(sender, instance: Project, **kwargs):
    """
    Verified Project cleanup.
    """
    try:
        if instance.image != defaultImagePath() and not BaseProject.objects.filter(image=instance.image).exists():
            instance.image.delete(save=False)
    except Exception as e:
        pass


@receiver(post_delete, sender=FreeProject)
def on_freeproject_delete(sender, instance: FreeProject, **kwargs):
    """
    Project cleanup.
    """

    try:
        if instance.image != defaultImagePath() and not BaseProject.objects.filter(image=instance.image).exists():
            instance.image.delete(save=False)
    except Exception as e:
        pass
    freeProjectDeleted(instance)


@receiver(post_delete, sender=CoreProject)
def on_coreproject_delete(sender, instance: CoreProject, **kwargs):
    """
    Project cleanup.
    """

    try:
        if instance.image != defaultImagePath() and not BaseProject.objects.filter(image=instance.image).exists():
            instance.image.delete(save=False)
    except Exception as e:
        pass


@receiver(post_delete, sender=Asset)
def on_asset_delete(sender, instance: Asset, **kwargs):
    """
    Asset cleanup.
    """
    try:
        instance.file.delete(save=False)
    except Exception as e:
        pass


@receiver(post_delete, sender=Snapshot)
def on_snap_delete(sender, instance: Snapshot, **kwargs):
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


@receiver(post_delete, sender=LegalDoc)
def on_legaldoc_delete(sender, instance: LegalDoc, **kwargs):
    """
    Legaldoc cache reset.
    """
    try:
        instance.reset_all_cache()
    except Exception as e:
        pass


@receiver(post_delete, sender=BaseProjectCoCreator)
def on_projectcocreator_delete(sender, instance: BaseProjectCoCreator, **kwargs):
    """
    On Base project cocreator relation delete.
    """
    BaseProjectCoCreatorInvitation.objects.filter(
        receiver=instance.co_creator, base_project=instance.base_project).delete()
