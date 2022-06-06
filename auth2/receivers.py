from allauth.account.signals import (email_added, email_changed, email_removed,
                                     password_changed, password_reset)
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.utils import timezone
from main.bots import Sender
from main.methods import errorLog
from people.models import Profile, User, defaultImagePath, isPictureDeletable

from .mailers import (accountDeleteAlert, emailAddAlert, emailRemoveAlert,
                      emailUpdateAlert, passwordChangeAlert)
from .models import DeviceNotification, EmailNotification, Notification


@receiver(post_save, sender=Notification)
def on_notification_create(sender, instance: Notification, created, **kwargs):
    if created:
        if not EmailNotification.objects.filter(notification=instance).exists():
            EmailNotification.objects.create(notification=instance)
        if not DeviceNotification.objects.filter(notification=instance).exists():
            DeviceNotification.objects.create(notification=instance)


@receiver(post_delete, sender=User)
def on_user_delete(sender, instance: User, **kwargs):
    """
    User cleanup.
    """
    try:
        instprofile: Profile = instance.profile
        if isPictureDeletable(instprofile.picture):
            instprofile.picture.delete(save=False)
        Profile.objects.filter(id=instprofile.id).update(
            to_be_zombie=True,
            is_zombie=True,
            githubID=None,
            is_moderator=False,
            is_active=False,
            zombied_on=timezone.now(),
            picture=defaultImagePath()
        )
    except Exception as e:
        errorLog(e)
        pass
    try:
        Sender.removeUserFromMailingServer(instance.email)
    except Exception as e:
        errorLog(e)
        pass
    accountDeleteAlert(instance)


@receiver(password_changed)
def user_password_changed(request, user: User, **kwargs):
    passwordChangeAlert(user)


@receiver(password_reset)
def user_password_reset(request, user: User, **kwargs):
    passwordChangeAlert(user)


@receiver(email_changed)
def user_email_changed(request, user: User, from_email_address: str, to_email_address: str, **kwargs):
    if from_email_address != to_email_address:
        emailUpdateAlert(user, from_email_address, to_email_address)


@receiver(email_added)
def user_email_added(request, user: User, email_address: str, **kwargs):
    emailAddAlert(user, email_address)


@receiver(email_removed)
def user_email_removed(request, user: User, email_address: str, **kwargs):
    emailRemoveAlert(user, email_address)
