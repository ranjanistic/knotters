let currentStep = isNaN("{{request.GET.step}}")?0:Number("{{request.GET.step}}");
{% if not request.user.profile.has_ghID %}
    connectWithGithub(URLS.CREATE_MOD,_=>{window.location.replace(URLS.CREATE)})
{% endif %}
