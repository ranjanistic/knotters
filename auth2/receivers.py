from django.core.cache import cache
from django.utils import timezone
from django.db.models.signals import post_save, post_delete
from allauth.account.signals import user_signed_up, user_logged_in, password_changed, password_reset, email_changed, email_confirmed, email_added, email_removed
from django.dispatch import receiver
from allauth.socialaccount.signals import social_account_added, social_account_updated, social_account_removed, pre_social_login
from allauth.socialaccount.models import SocialAccount
from main.bots import Sender
from main.methods import errorLog, addMethodToAsyncQueue
from .models import Notification, EmailNotification, DeviceNotification
from .apps import APPNAME

@receiver(post_save, sender=Notification)
def on_notification_create(sender, instance:Notification, created, **kwargs):
    if created:
        if not EmailNotification.objects.filter(notification=instance).exists():
            EmailNotification.objects.create(notification=instance)
        if not DeviceNotification.objects.filter(notification=instance).exists():
            DeviceNotification.objects.create(notification=instance)
