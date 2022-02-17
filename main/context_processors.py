from django.core.cache import cache
from django.conf import settings
from people.models import Profile
from management.models import ThirdPartyAccount
from .methods import renderData
from .env import PUBNAME, BOTMAIL, RECAPTCHA_KEY, SITE, VERSION
from .strings import DIVISIONS, URL, Browse

GlobalContextData = dict(
    APPNAME=PUBNAME,
    CONTACTMAIL=BOTMAIL,
    DESCRIPTION="Solving problems together. Be a part of Knotters community and explore what everyone's involved into.",
    SITE=SITE,
    VERSION=VERSION,
    ICON=f"{settings.STATIC_URL}graphics/self/icon.svg",
    ICON_DARK=f"{settings.STATIC_URL}graphics/self/icon-dark.svg",
    ICON_SHADOW=f"{settings.STATIC_URL}graphics/self/icon-shadow.svg",
    ICON_PNG=f"{settings.STATIC_URL}graphics/self/1024/icon.png",
    ICON_DARK_PNG=f"{settings.STATIC_URL}graphics/self/1024/icon-dark.png",
    ICON_SHADOW_PNG=f"{settings.STATIC_URL}graphics/self/1024/icon-shadow.png",
    BANNER=f"{settings.STATIC_URL}graphics/self/banner.svg",
    BANNER_PNG=f"{settings.STATIC_URL}graphics/self/2500x1000/banner-bg.png",
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
    VAPID_KEY=settings.VAPID_PUBLIC_KEY,
)


def Global(request):
    data = dict(**GlobalContextData,alerts=[],knotbot=Profile.KNOTBOT(),BROWSE=Browse.getAllKeys(),SUBAPPS=dict(),SUBAPPSLIST=[])
    SOCIALS = cache.get(ThirdPartyAccount.cachekey, None)
    if not SOCIALS:
        SOCIALS = ThirdPartyAccount.objects.all()
        cache.set(ThirdPartyAccount.cachekey, SOCIALS, settings.CACHE_MAX)

    data['SOCIALS'] = SOCIALS

    for div in DIVISIONS:
        data['SUBAPPS'][div] = div
        data['SUBAPPSLIST'].append(div)
    return renderData(data)
