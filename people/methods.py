import re

from django.http.response import HttpResponse
from main.methods import renderView
from .apps import APPNAME
from .models import User, Profile, defaultImagePath
from allauth.account.signals import user_signed_up
from allauth.socialaccount.signals import social_account_added, social_account_updated, social_account_removed, pre_social_login
from allauth.socialaccount.models import SocialAccount
from django.db.models.signals import post_save
from django.dispatch import receiver
from allauth.socialaccount.providers.github.provider import GitHubProvider
from allauth.socialaccount.providers.google.provider import GoogleProvider
from allauth.socialaccount.providers.discord.provider import DiscordProvider
from projects.models import Project
from .apps import APPNAME
from main.strings import code, profile
from django.template.loader import render_to_string
import requests

def renderer(request, file, data={}):
    return renderView(request, file, data, fromApp=APPNAME)


@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    """
    Creates Profile 121 after new User creation.
    """
    if created:
        return Profile.objects.create(user=instance)


def getProfileImageBySocialAccount(socialaccount):
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


def getUsernameFromGHSocial(ghSocial):
    url = ghSocial.get_profile_url()
    try:
        urlparts = str(url).split('/')
        return urlparts[len(urlparts)-1]
    except:
        return None


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


def convertToFLname(string):
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

def filterBio(string):
    bio = str(string)
    if len(bio) > 120:
        bio = bio[:(120-len(bio))]
        return filterBio(bio)
    return bio

PROFILE_SECTIONS = [profile.OVERVIEW, profile.PROJECTS,
                    profile.CONTRIBUTION, profile.ACTIVITY, profile.MODERATION]

SETTING_SECTIONS = [profile.setting.ACCOUNT, profile.setting.PREFERENCE]


def getProfileSectionData(section, user, request):
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


def getProfileSectionHTML(user, section, request):
    if not PROFILE_SECTIONS.__contains__(section):
        return False
    data = {}
    for sec in PROFILE_SECTIONS:
        if sec == section:
            data = getProfileSectionData(sec, user, request)
            break
    return render_to_string(f'{APPNAME}/profile/{section}.html',  data, request=request)


def getSettingSectionData(section, user, request):
    data = {}
    if section == profile.setting.ACCOUNT:
        pass
    if section == profile.setting.PREFERENCE:
        pass
    return data


def getSettingSectionHTML(user, section, request):
    if not SETTING_SECTIONS.__contains__(section) or request.user != user:
        return False
    data = {}
    for sec in SETTING_SECTIONS:
        if sec == section:
            data = getSettingSectionData(sec, user, request)
            break
    return render_to_string(f'{APPNAME}/setting/{section}.html',  data, request=request)


def sendWelcomeMail(email, first_name, last_name):
    token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJhdWQiOiIxIiwianRpIjoiYzg0NjFlNGU1NzU2NDdkNGE2ZjA2ZDEyYzUwNmQ4NDYzYTNjM2U5ODcyNDZkN2EyYmQ2MWRhNTY2OGQ5NWQ4YmFjMWNhZmM4MjdiODMxOWMiLCJpYXQiOiIxNjI0MDE1NTQ0LjU2MzQ3MSIsIm5iZiI6IjE2MjQwMTU1NDQuNTYzNDc5IiwiZXhwIjoiMTYyNDYyMDM0NC41NTk3OTEiLCJzdWIiOiI5Nzg0NSIsInNjb3BlcyI6W119.U9889llhKwGqvJyGrk3jo5rlMT5GuMk3CP1TvA28MAgpLQ_LK_XBe4NkXJ-Tvnq6EKYlmP7JjJzso62R1ol92w"
    url = "https://api.sender.net/v2/subscribers"
    headers = {
        "Authorization": "Bearer " + token,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    payload = {
    "email": email,
    "firstname": first_name,
    "lastname": last_name,
    "groups": ["dL8pBD"],
    }

    response = requests.request('POST', url, headers=headers,json=payload)

