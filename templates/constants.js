{% load static %}
{% load i18n %}
{% load l10n %}
{% load tz %}
{% load cache %}
{% load account %}
{% load socialaccount %}
{% load custom_tags %}

const SITE = "{{SITE}}", 
    STATIC_URL = "{% static '*' %}",
    csrfmiddlewaretoken = "{{csrf_token}}",
    authenticated = "{{request.user.is_authenticated}}" == 'True',
    activeuser = authenticated && "{{request.user.profile.is_active}}" == 'True', 
    ROOT = "{{ROOT}}", 
    APPNAME = "{{APPNAME}}",
    VERSION = "{{VERSION}}",
    _DEBUG = "{{DEBUG}}" == "True",
    SUBAPPSLIST = {{SUBAPPSLIST|or:'[]'|safe}},
    SUBAPPNAME = "{{SUBAPPNAME}}"||"{{request.GET.subappname}}",
    ICON = "{{ICON}}",
    ICON_DARK = "{{ICON_DARK}}",
    ICON_SHADOW = "{{ICON_SHADOW}}",
    RECAPTCHA_KEY = "{{RECAPTCHA_KEY}}",
    VAPID_KEY = "{{VAPID_KEY}}",
    BROWSE = Object.freeze({{BROWSE|or:'{}'|safe}}),
    URLS = Object.freeze({{URLS|or:'{}'|safe}});
