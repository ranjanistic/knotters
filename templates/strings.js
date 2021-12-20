{% load i18n %}
{% load l10n %}

const STRING = {
    static_cache_name: 'static-cache-{{VERSION}}',
    dynamic_cache_name: 'dynamic-cache-{{VERSION}}',
    re_introduction: '{% trans "Press Alt+R for re-introduction, or visit The Landing Page" %}',
    update_available:'{% trans "Update available" %}',
    default_error_message: '{% trans "Something went wrong." %}',
    network_error_message: '{% trans "Network error, check your connection." %}',
}

Object.freeze(STRING);