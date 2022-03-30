from django.db.models.signals import post_save, post_delete
from allauth.account.signals import user_signed_up, user_logged_in
from django.dispatch import receiver
from allauth.socialaccount.signals import social_account_added, social_account_updated, social_account_removed, pre_social_login
from allauth.socialaccount.models import SocialAccount
from allauth.socialaccount.providers.github.provider import GitHubProvider
from main.bots import Sender
from main.methods import errorLog, addMethodToAsyncQueue
from .models import ProfileSetting, User, Profile, defaultImagePath, isPictureDeletable, Framework, Frame
from .mailers import welcomeAlert
from .methods import getProfileImageBySocialAccount, isPictureSocialImage, getUsernameFromGHSocial
from .apps import APPNAME

@receiver(post_save, sender=User)
def on_user_create(sender, instance:User, created, **kwargs):
    """
    Creates Profile 121 after new User creation.
    Adds user to mailing server.
    """
    if created:
        Profile.objects.create(user=instance)
        addMethodToAsyncQueue(f"{APPNAME}.mailers.{welcomeAlert.__name__}",instance)


@receiver(post_save, sender=Profile)
def on_profile_create(sender, instance:Profile, created, **kwargs):
    """
    Creates Setting 121 after new Profile creation.
    Adds user to mailing server.
    """
    if created:
        ProfileSetting.objects.create(profile=instance)
        Sender.addUserToMailingServer(instance.user.email, instance.user.first_name, instance.user.last_name)



@receiver(post_delete, sender=Profile)
def on_profile_delete(sender, instance, **kwargs):
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



@receiver(social_account_removed)
def social_removed(request, socialaccount, **kwargs):
    try:
        profile = Profile.objects.get(user=socialaccount.user)
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
def social_added(request, sociallogin, **kwargs):
    try:
        changed = False
        profile = Profile.objects.get(user=sociallogin.user)
        if sociallogin.account.provider == GitHubProvider.id:
            try:
                data = SocialAccount.objects.get(
                    user=sociallogin.user, provider=GitHubProvider.id)
                if data:
                    profile.update_githubID(getUsernameFromGHSocial(data))
                    changed = True
            except: pass
        if str(profile.picture) == defaultImagePath():
            profile.picture = getProfileImageBySocialAccount(
                sociallogin.account)
            changed = True
        if changed:
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


@receiver(post_delete, sender=Framework)
def on_framework_delete(sender, instance, **kwargs):
    """
    Framework cleanup.
    """
    try:
        if instance.banner:
            instance.banner.delete(save=False)
    except Exception as e:
        pass
    
@receiver(post_delete, sender=Frame)
def on_frame_delete(sender, instance, **kwargs):
    """
    Frame cleanup.
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
