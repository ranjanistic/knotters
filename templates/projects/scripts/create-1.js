let currentStep = isNaN("{{request.GET.step}}")?0:Number("{{request.GET.step}}");
{% if not request.user.profile.has_ghID %}
    connectWithGithub(URLS.CREATE_MOD,_=>{window.location.replace(URLS.CREATE)})
{% endif %}
getElement('prevBtn').onclick=()=>{
    nextPrev(-1)
}
getElement('nextBtn').onclick=()=>{
    nextPrev(1)
}
getElement('stale_days').onblur=(e)=>{
    e.target.value=((15-Number(e.target.value))>=0?Number(e.target.value)>0?Number(e.target.value):1:15)||3
}