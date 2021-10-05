from django.core.cache import cache
from django.conf import settings
from people.models import Profile
from .methods import renderData
from .env import PUBNAME, BOTMAIL, RECAPTCHA_KEY, SITE, VERSION
from .strings import DIVISIONS, URL


def Global(request):
    # id = uuid4()
    # cache.set(f"global_alerts_{id}",{'message':'haha this the alert', 'url':'/compete/shit', 'id':id}, settings.CACHE_MICRO)
    # alerts = cache.get(f"global_alerts_{id}") or []
    knotbot = cache.get('profile_knottersbot')
    if not knotbot:
        knotbot = Profile.objects.get(user__email=BOTMAIL)
        cache.set('profile_knottersbot', knotbot, settings.CACHE_MAX)

    data = dict(
        APPNAME=PUBNAME,
        CONTACTMAIL=BOTMAIL,
        DESCRIPTION="Solving problems together.",
        SITE=SITE,
        VERSION=VERSION,
        SUBAPPS=dict(),
        SUBAPPSLIST=[],
        ICON=f"{settings.STATIC_URL}graphics/self/icon.svg",
        SERVICE_WORKER=f"/{URL.SERVICE_WORKER}",
        MANIFESTURL=f"/{URL.MANIFEST}",
        RECAPTCHA_KEY=RECAPTCHA_KEY,
        CACHE_MICRO=settings.CACHE_MICRO,
        CACHE_MIN=settings.CACHE_MIN,
        CACHE_SHORT=settings.CACHE_SHORT,
        CACHE_LONG=settings.CACHE_LONG,
        CACHE_LONGER=settings.CACHE_LONGER,
        CACHE_MAX=settings.CACHE_MAX,
        CACHE_ETERNAL=settings.CACHE_ETERNAL,
        alerts=[],
        knotbot=knotbot
    )

    for div in DIVISIONS:
        data['SUBAPPS'][div] = div
        data['SUBAPPSLIST'].append(div)
    return renderData(data)
