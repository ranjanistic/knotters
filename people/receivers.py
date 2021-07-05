from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from allauth.account.signals import user_signed_up
from allauth.socialaccount.signals import social_account_added, social_account_updated, social_account_removed, pre_social_login
from allauth.socialaccount.models import SocialAccount
from allauth.socialaccount.providers.github.provider import GitHubProvider
from allauth.socialaccount.providers.google.provider import GoogleProvider
from allauth.socialaccount.providers.discord.provider import DiscordProvider
from main.methods import addUserToMailingServer, removeUserFromMailingServer
from .models import ProfileSetting, User, Profile, defaultImagePath


def getProfileImageBySocialAccount(socialaccount: SocialAccount) -> str:
    """
    Returns user profile image url by social account.
    """
    if socialaccount.provider == GitHubProvider.id:
        return socialaccount.extra_data['avatar_url']
    if socialaccount.provider == GoogleProvider.id:
        link = str(socialaccount.extra_data['picture'])
        linkpart = link.split("=")[0]
        sizesplit = link.split("=")[1].split("-")
        sizesplit.remove(sizesplit[0])
        return "=".join([linkpart, "-".join(["s512", "-".join(sizesplit)])])
    if socialaccount.provider == DiscordProvider.id:
        return f"https://cdn.discordapp.com/avatars/{socialaccount.uid}/{socialaccount.extra_data['avatar']}.png?size=1024"
    return defaultImagePath()


def getUsernameFromGHSocial(ghSocial: SocialAccount) -> str or None:
    """
    Extracts github ID of user from their github profile url.
    """
    url = ghSocial.get_profile_url()
    try:
        urlparts = str(url).split('/')
        return urlparts[len(urlparts)-1]
    except:
        return None


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
    removeUserFromMailingServer(instance.email)


@receiver(post_delete, sender=Profile)
def on_profile_delete(sender, instance, **kwargs):
    """
    Profile cleanup.
    """
    try:
        if instance.picture != defaultImagePath() and not str(instance.picture).startswith('http'):
            instance.picture.delete(save=False)
    except:
        pass


@receiver(user_signed_up)
def on_user_signup(request, user, **kwargs):
    try:
        accs = SocialAccount.objects.filter(user=user)
        picture = getProfileImageBySocialAccount(accs.first())
        githubID = ''
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
        if socialaccount.provider == GitHubProvider.id:
            Profile.objects.filter(
                user=socialaccount.user).update(githubID=None)
    except:
        pass


@receiver(social_account_added)
def social_added(request, sociallogin, **kwargs):
    try:
        if sociallogin.account.provider == GitHubProvider.id:
            data = SocialAccount.objects.get(
                user=sociallogin.user, provider=GitHubProvider.id)
            if data:
                Profile.objects.filter(user=sociallogin.user).update(
                    githubID=getUsernameFromGHSocial(data))
    except:
        pass


@receiver(social_account_updated)
def social_updated(request, sociallogin, **kwargs):
    try:
        if sociallogin.account.provider == GitHubProvider.id:
            data = SocialAccount.objects.get(
                user=sociallogin.account.user, provider=GitHubProvider.id)
            Profile.objects.filter(user=sociallogin.account.user).update(
                githubID=getUsernameFromGHSocial(data))
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
