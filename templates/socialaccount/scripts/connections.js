{% load static %}
{% load i18n %}
{% load l10n %}
{% load tz %}
{% load cache %}
{% load socialaccount %}

const socialaccounts = getElements("base-account-provider").map((ele)=>ele.getAttribute("data-provider"));

const allproviders = getElements("oauth-providers");

allproviders.forEach((provider)=>{
    visibleElement(provider.id,!socialaccounts.includes(provider.id));
})

if(socialaccounts.length===allproviders.length){
    hide(getElement('account-linking'));
}
{% if form.non_field_errors %}
    error("{{ form.non_field_errors }}");
{% endif %}
