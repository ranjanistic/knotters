from django.utils import timezone
from django.db.models.signals import post_save, post_delete
from allauth.account.signals import user_signed_up, user_logged_in, password_changed, password_reset, email_changed, email_confirmed, email_added, email_removed
from django.dispatch import receiver
from allauth.socialaccount.signals import social_account_added, social_account_updated, social_account_removed, pre_social_login
from allauth.socialaccount.models import SocialAccount
from allauth.socialaccount.providers.github.provider import GitHubProvider
from main.methods import addUserToMailingServer, removeUserFromMailingServer
from .models import ProfileSetting, User, Profile, defaultImagePath
from .mailers import accountDeleteAlert, emailAddAlert, emailRemoveAlert, passordChangeAlert, emailUpdateAlert
from .methods import getProfileImageBySocialAccount, isPictureDeletable, isPictureSocialImage, getUsernameFromGHSocial


@receiver(post_save, sender=User)
def on_user_create(sender, instance, created, **kwargs):
    """
    Creates Profile 121 after new User creation.
    Adds user to mailing server.
    """
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=Profile)
def on_profile_create(sender, instance, created, **kwargs):
    """
    Creates Setting 121 after new Profile creation.
    Adds user to mailing server.
    """
    if created:
        ProfileSetting.objects.create(profile=instance)
        addUserToMailingServer(
            instance.user.email, instance.user.first_name, instance.user.last_name)


@receiver(post_delete, sender=User)
def on_user_delete(sender, instance, **kwargs):
    """
    User cleanup.
    """
    try:
        Profile.objects.filter(id=instance.profile.id).update(
            is_zombie=True, githubID=None, is_moderator=False, is_active=False, zombied_on=timezone.now(), picture=defaultImagePath())
        if isPictureDeletable(instance.profile.picture):
            instance.profile.picture.delete(save=False)
    except Exception as e:
        print(e)
        pass
    try:
        removeUserFromMailingServer(instance.email)
    except Exception as e:
        print(e)
        pass
    accountDeleteAlert(instance)


@receiver(post_delete, sender=Profile)
def on_profile_delete(sender, instance, **kwargs):
    """
    Profile cleanup.
    """
    try:
        if isPictureDeletable(instance.picture):
            instance.picture.delete(save=False)
    except:
        pass


@receiver(user_logged_in)
def on_user_login(sender, user, request, **kwargs):
    pass


@receiver(user_signed_up)
def on_user_signup(request, user, **kwargs):
    try:
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


@receiver(password_changed)
def user_password_changed(request, user, **kwargs):
    passordChangeAlert(user)


@receiver(password_reset)
def user_password_reset(request, user, **kwargs):
    passordChangeAlert(user)


@receiver(email_changed)
def user_email_changed(request, user, from_email_address, to_email_address, **kwargs):
    emailUpdateAlert(user, from_email_address, to_email_address)


@receiver(email_added)
def user_email_added(request, user, email_address, **kwargs):
    emailAddAlert(user, email_address)


@receiver(email_removed)
def user_email_removed(request, user, email_address, **kwargs):
    emailRemoveAlert(user, email_address)


@receiver(social_account_removed)
def social_removed(request, socialaccount, **kwargs):
    try:
        profile = Profile.objects.get(user=socialaccount.user)
        if socialaccount.provider == GitHubProvider.id:
            profile.githubID = None
        provider = isPictureSocialImage(profile.picture)
        if provider and provider == socialaccount.provider:
            profile.picture = defaultImagePath()
        profile.save()
    except:
        pass


@receiver(social_account_added)
def social_added(request, sociallogin, **kwargs):
    try:
        profile = Profile.objects.get(user=sociallogin.user)
        if sociallogin.account.provider == GitHubProvider.id:
            data = SocialAccount.objects.get(
                user=sociallogin.user, provider=GitHubProvider.id)
            if data:
                profile.githubID = getUsernameFromGHSocial(data)
        if str(profile.picture) == defaultImagePath():
            profile.picture = getProfileImageBySocialAccount(
                sociallogin.account)
        profile.save()
    except:
        pass


@receiver(social_account_updated)
def social_updated(request, sociallogin, **kwargs):
    try:
        profile = Profile.objects.get(user=sociallogin.account.user)
        if sociallogin.account.provider == GitHubProvider.id:
            data = SocialAccount.objects.get(
                user=sociallogin.account.user, provider=GitHubProvider.id)
            profile.githubID = getUsernameFromGHSocial(data)
        if str(profile.picture) == defaultImagePath():
            profile.picture = getProfileImageBySocialAccount(
                sociallogin.account)
        profile.save()
    except:
        pass


@receiver(pre_social_login)
def before_social_login(request, sociallogin, **kwargs):
    """
    To connect existing account with unconnected social account, if user directly logs in with an unconnected social account.
    """
    if sociallogin.is_existing:
        return
    try:
        user = User.objects.get(email=sociallogin.user)
        sociallogin.connect(request, user)
    except:
        pass