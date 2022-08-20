from allauth.account.signals import user_logged_in, user_signed_up, email_confirmed
from allauth.socialaccount.models import SocialAccount, SocialLogin, EmailAddress
from allauth.socialaccount.providers.github.provider import GitHubProvider
from allauth.socialaccount.signals import (pre_social_login,
                                           social_account_added,
                                           social_account_removed,
                                           social_account_updated)
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from auth2.models import EmailNotification
from main.bots import Sender
from main.methods import errorLog

from .mailers import welcomeAlert
from .methods import (getProfileImageBySocialAccount, getUsernameFromGHSocial,
                      isPictureSocialImage)
from .models import (Frame, Framework, Profile, ProfileSetting, User,
                     defaultImagePath, isPictureDeletable)


@receiver(post_save, sender=User)
def on_user_create(sender, instance: User, created, **kwargs):
    """
    Creates Profile 121 after new User creation.
    Adds user to mailing server.
    """
    if created:
        Profile.objects.create(user=instance)
        welcomeAlert(instance)


@receiver(post_save, sender=Profile)
def on_profile_create(sender, instance: Profile, created, **kwargs):
    """
    Creates Setting 121 after new Profile creation.
    Adds user to mailing server.
    """
    if created:
        ProfileSetting.objects.create(profile=instance)
        Sender.addUserToMailingServer(
            instance.user.email, instance.user.first_name, instance.user.last_name)


@receiver(post_delete, sender=Profile)
def on_profile_delete(sender, instance: Profile, **kwargs):
    """
    Profile cleanup.
    """
    try:
        if isPictureDeletable(instance.picture):
            instance.picture.delete(save=False)
    except Exception as e:
        errorLog(e)
        pass


@receiver(user_logged_in)
def on_user_login(sender, user, request, **kwargs):
    pass


@receiver(user_signed_up)
def on_user_signup(request, user: User, **kwargs):
    """On user signup, to update relevant things."""
    try:
        email = user.get_emailaddresses(True)
        if len(email)>0:
            on_email_confirmation(request, email[0])
        accs = SocialAccount.objects.filter(user=user)
        picture = getProfileImageBySocialAccount(accs.first())
        githubID = None
        try:
            acc = accs.filter(provider=GitHubProvider.id).first()
            if acc:
                githubID = getUsernameFromGHSocial(acc)
        except:
            pass
        Profile.objects.filter(user=user).update(
            githubID=githubID, picture=picture)
    except:
        pass


@receiver(email_confirmed)
def on_email_confirmation(request, email_address: EmailAddress, **kwargs):
    """On email confirmation, email notifications are subscribed"""
    user = User.objects.get(email=email_address)
    if(email_address.primary):
        list(map(lambda e: e.subscribers.add(user),
            EmailNotification.objects.all()))


@receiver(social_account_removed)
def social_removed(request, socialaccount: SocialAccount, **kwargs):
    """On social account removal, to update relevant things."""
    try:
        profile: Profile = Profile.objects.get(user=socialaccount.user)
        if socialaccount.provider == GitHubProvider.id:
            profile.update_githubID(None)
            if profile.is_manager():
                profile.update_management(githubOrgID=None)
        provider = isPictureSocialImage(profile.picture)
        if provider and provider == socialaccount.provider:
            profile.picture = defaultImagePath()
        profile.save()
    except Exception as e:
        errorLog(e)
        pass


@receiver(social_account_added)
def social_added(request, sociallogin: SocialLogin, **kwargs):
    """On social account added, to update relevant things."""
    try:
        changed = False
        profile: Profile = Profile.objects.get(user=sociallogin.user)
        if sociallogin.account.provider == GitHubProvider.id:
            try:
                data = SocialAccount.objects.get(
                    user=sociallogin.user, provider=GitHubProvider.id)
                if data:
                    profile.update_githubID(getUsernameFromGHSocial(data))
                    changed = True
            except:
                pass
        if str(profile.picture) == defaultImagePath():
            profile.picture = getProfileImageBySocialAccount(
                sociallogin.account)
            changed = True
        if changed:
            profile.save()
    except:
        pass


@receiver(social_account_updated)
def social_updated(request, sociallogin: SocialLogin, **kwargs):
    """On social account updated, to update relevant things."""
    try:
        profile: Profile = Profile.objects.get(user=sociallogin.account.user)
        if sociallogin.account.provider == GitHubProvider.id:
            data = SocialAccount.objects.get(
                user=sociallogin.account.user, provider=GitHubProvider.id)
            profile.update_githubID(getUsernameFromGHSocial(data))
        if str(profile.picture) == defaultImagePath():
            profile.picture = getProfileImageBySocialAccount(
                sociallogin.account)
        profile.save()
    except:
        pass


@receiver(pre_social_login)
def before_social_login(request, sociallogin: SocialLogin, **kwargs):
    """
    To connect existing account with unconnected social account, if user directly logs in with an unconnected social account.
    """
    if sociallogin.is_existing:
        return
    try:
        user: User = User.objects.get(email=sociallogin.user)
        sociallogin.connect(request, user)
    except:
        pass


@receiver(post_delete, sender=Framework)
def on_framework_delete(sender, instance: Framework, **kwargs):
    """
    Framework cleanup.
    TODO
    """
    try:
        if instance.banner:
            instance.banner.delete(save=False)
    except Exception as e:
        pass


@receiver(post_delete, sender=Frame)
def on_frame_delete(sender, instance: Frame, **kwargs):
    """
    Frame cleanup.
    TODO
    """
    try:
        if instance.image:
            instance.image.delete(save=False)
        if instance.video:
            instance.video.delete(save=False)
        if instance.attachment:
            instance.attachment.delete(save=False)
    except Exception as e:
        pass
