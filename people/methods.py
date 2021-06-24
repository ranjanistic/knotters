from django.http.request import HttpRequest
from allauth.account.signals import user_signed_up
from allauth.socialaccount.signals import social_account_added, social_account_updated, social_account_removed, pre_social_login
from allauth.socialaccount.models import SocialAccount
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from allauth.socialaccount.providers.github.provider import GitHubProvider
from allauth.socialaccount.providers.google.provider import GoogleProvider
from allauth.socialaccount.providers.discord.provider import DiscordProvider
from django.template.loader import render_to_string
from main.methods import renderView
from main.strings import code, profile
from main.methods import addUserToMailingServer, removeUserFromMailingServer
from projects.models import Project
from .models import User, Profile, defaultImagePath
from .apps import APPNAME


def renderer(request, file, data={}):
    return renderView(request, file, data, fromApp=APPNAME)


def getProfileImageBySocialAccount(socialaccount: SocialAccount) -> str:
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
    url = ghSocial.get_profile_url()
    try:
        urlparts = str(url).split('/')
        return urlparts[len(urlparts)-1]
    except:
        return None


def convertToFLname(string: str) -> str and str:
    """
    Converts the given string to first and last name format.

    :returns: firtsname, lastname
    """
    name = str(string)
    namesequence = name.split(" ")
    firstname = namesequence[0]
    del namesequence[0]
    if len(namesequence) > 0:
        lastname = " ".join(namesequence)
    else:
        lastname = ''
    fullname = f"{firstname} {lastname}"
    if len(fullname) > 70:
        fullname = fullname[:(70-len(fullname))]
        return convertToFLname(fullname)
    return firstname, lastname


def filterBio(string: str) -> str:
    bio = str(string)
    if len(bio) > 120:
        bio = bio[:(120-len(bio))]
        return filterBio(bio)
    return bio


PROFILE_SECTIONS = [profile.OVERVIEW, profile.PROJECTS,
                    profile.CONTRIBUTION, profile.ACTIVITY, profile.MODERATION]

SETTING_SECTIONS = [profile.setting.ACCOUNT, profile.setting.PREFERENCE]


def getProfileSectionData(section: str, user: User, request: HttpRequest) -> dict:
    data = {
        'self': request.user == user
    }
    if section == profile.OVERVIEW:
        pass
    if section == profile.PROJECTS:
        if request.user == user:
            projects = Project.objects.filter(creator=user)
        else:
            projects = Project.objects.filter(creator=user, status=code.LIVE)
        data[code.LIVE] = projects.filter(status=code.LIVE)
        data[code.MODERATION] = projects.filter(status=code.MODERATION)
        data[code.REJECTED] = projects.filter(status=code.REJECTED)
        pass
    if section == profile.CONTRIBUTION:
        pass
    if section == profile.ACTIVITY:
        pass
    if section == profile.MODERATION:
        pass
    return data


def getProfileSectionHTML(user: User, section: str, request: HttpRequest) -> str:
    if not PROFILE_SECTIONS.__contains__(section):
        return False
    data = {}
    for sec in PROFILE_SECTIONS:
        if sec == section:
            data = getProfileSectionData(sec, user, request)
            break
    return render_to_string(f'{APPNAME}/profile/{section}.html',  data, request=request)


def getSettingSectionData(section: str, user: User, request: HttpRequest) -> dict:
    data = {}
    if section == profile.setting.ACCOUNT:
        pass
    if section == profile.setting.PREFERENCE:
        pass
    return data


def getSettingSectionHTML(section: str, user: User, request: HttpRequest) -> dict:
    if not SETTING_SECTIONS.__contains__(section) or request.user != user:
        return False
    data = {}
    for sec in SETTING_SECTIONS:
        if sec == section:
            data = getSettingSectionData(sec, user, request)
            break
    return render_to_string(f'{APPNAME}/setting/{section}.html',  data, request=request)


@receiver(post_save, sender=User)
def on_user_create(sender, instance, created, **kwargs):
    """
    Creates Profile 121 after new User creation.
    Adds user to mailing server.
    """
    if created:
        Profile.objects.create(user=instance)
        addUserToMailingServer(
            instance.email, instance.first_name, instance.last_name)


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
        instance.picture.delete(save=False)
    except:
        pass


@receiver(user_signed_up)
def on_user_signup(request, user, **kwargs):
    try:
        profile = Profile.objects.get(user=user)
        accs = SocialAccount.objects.filter(user=user)
        for acc in accs:
            profile.picture = getProfileImageBySocialAccount(acc)
            if acc.provider == GitHubProvider.id:
                profile.githubID = getUsernameFromGHSocial(acc)
                break
        profile.save()
    except:
        pass


@receiver(social_account_removed)
def social_removed(request, socialaccount, **kwargs):
    if socialaccount.provider == GitHubProvider.id:
        profile = Profile.objects.get(user=socialaccount.user)
        profile.githubID = None
        profile.save()


@receiver(social_account_added)
def social_added(request, sociallogin, **kwargs):
    try:
        data = SocialAccount.objects.get(
            user=sociallogin.user, provider=GitHubProvider.id)
        if data:
            profile = Profile.objects.get(user=sociallogin.user)
            profile.githubID = getUsernameFromGHSocial(data)
            profile.save()
    except:
        pass


@receiver(social_account_updated)
def social_updated(request, sociallogin, **kwargs):
    if sociallogin.account.provider == GitHubProvider.id:
        profile = Profile.objects.get(user=sociallogin.account.user)
        data = SocialAccount.objects.get(
            user=sociallogin.account.user, provider=GitHubProvider.id)
        profile.githubID = getUsernameFromGHSocial(data)
        profile.save()


@receiver(pre_social_login)
def before_social_login(request, sociallogin, **kwargs):
    if sociallogin.is_existing:
        return
    try:
        user = User.objects.get(email=sociallogin.user)
        sociallogin.connect(request, user)
    except:
        pass
