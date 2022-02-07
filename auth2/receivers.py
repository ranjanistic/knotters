from django.core.cache import cache
from django.utils import timezone
from django.db.models.signals import post_save, post_delete
from allauth.account.signals import user_signed_up, user_logged_in, password_changed, password_reset, email_changed, email_confirmed, email_added, email_removed
from django.dispatch import receiver
from allauth.socialaccount.signals import social_account_added, social_account_updated, social_account_removed, pre_social_login
from allauth.socialaccount.models import SocialAccount
from main.bots import Sender
from main.methods import errorLog, addMethodToAsyncQueue
from people.models import Profile, User, defaultImagePath, isPictureDeletable
from .mailers import accountDeleteAlert, emailAddAlert, emailRemoveAlert, passordChangeAlert, emailUpdateAlert
from .models import Notification, EmailNotification, DeviceNotification
from .apps import APPNAME

@receiver(post_save, sender=Notification)
def on_notification_create(sender, instance:Notification, created, **kwargs):
    if created:
        if not EmailNotification.objects.filter(notification=instance).exists():
            EmailNotification.objects.create(notification=instance)
        if not DeviceNotification.objects.filter(notification=instance).exists():
            DeviceNotification.objects.create(notification=instance)

@receiver(post_delete, sender=User)
def on_user_delete(sender, instance, **kwargs):
    """
    User cleanup.
    """
    try:
        Profile.objects.filter(id=instance.profile.id).update(
            to_be_zombie=True,
            is_zombie=True, 
            githubID=None, 
            is_moderator=False, 
            is_active=False,
            zombied_on=timezone.now(),
            picture=defaultImagePath()
        )
        if isPictureDeletable(instance.profile.picture):
            instance.profile.picture.delete(save=False)
    except Exception as e:
        errorLog(e)
        pass
    addMethodToAsyncQueue(f"{APPNAME}.mailers.{accountDeleteAlert.__name__}",instance)
    try:
        Sender.removeUserFromMailingServer(instance.email)
    except Exception as e:
        errorLog(e)
        pass


@receiver(password_changed)
def user_password_changed(request, user, **kwargs):
    addMethodToAsyncQueue(f"{APPNAME}.mailers.{passordChangeAlert.__name__}", user)


@receiver(password_reset)
def user_password_reset(request, user, **kwargs):
    addMethodToAsyncQueue(f"{APPNAME}.mailers.{passordChangeAlert.__name__}", user)


@receiver(email_changed)
def user_email_changed(request, user, from_email_address, to_email_address, **kwargs):
    if from_email_address != to_email_address:
        addMethodToAsyncQueue(f"{APPNAME}.mailers.{emailUpdateAlert.__name__}",user, from_email_address, to_email_address)


@receiver(email_added)
def user_email_added(request, user, email_address, **kwargs):
    addMethodToAsyncQueue(f"{APPNAME}.mailers.{emailAddAlert.__name__}", user, email_address)


@receiver(email_removed)
def user_email_removed(request, user, email_address, **kwargs):
    addMethodToAsyncQueue(f"{APPNAME}.mailers.{emailRemoveAlert.__name__}", user, email_address)

