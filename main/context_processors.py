from django.conf import settings
from management.models import ThirdPartyAccount
from people.models import Profile

from .env import BOTMAIL, PUBNAME, SITE, VERSION
from .methods import renderData
from .strings import DIVISIONS, URL, Action, Browse, Code, Message, Template
from projects.models import LegalDoc

GlobalContextData = dict(
    APPNAME=PUBNAME,
    CONTACTMAIL=BOTMAIL,
    DESCRIPTION=Message.APP_DESCRIPTION,
    SITE=SITE,
    VERSION=VERSION,
    ICON=f"{settings.STATIC_URL}graphics/self/icon.svg",
    ICON_DARK=f"{settings.STATIC_URL}graphics/self/icon-dark.svg",
    ICON_SHADOW=f"{settings.STATIC_URL}graphics/self/icon-shadow.svg",
    ICON_PNG=f"{settings.STATIC_URL}graphics/self/1024/icon.webp",
    ICON_DARK_PNG=f"{settings.STATIC_URL}graphics/self/1024/icon-dark.webp",
    ICON_SHADOW_PNG=f"{settings.STATIC_URL}graphics/self/1024/icon-shadow.webp",
    ICON_CIRCLE=f"{settings.STATIC_URL}graphics/self/icon-circle.svg",
    ICON_CIRCLE_DARK=f"{settings.STATIC_URL}graphics/self/icon-circle-dark.svg",
    BANNER=f"{settings.STATIC_URL}graphics/self/banner.svg",
    BANNER_PNG=f"{settings.STATIC_URL}graphics/self/2500x1000/banner-bg.webp",
    SERVICE_WORKER=f"/{URL.SERVICE_WORKER}",
    MANIFESTURL=f"/{URL.MANIFEST}",
    RECAPTCHA_KEY=settings.GOOGLE_RECAPTCHA_KEY,
    VAPID_KEY=settings.VAPID_PUBLIC_KEY,
    CACHE_MICRO=settings.CACHE_MICRO,
    CACHE_MIN=settings.CACHE_MIN,
    CACHE_SHORT=settings.CACHE_SHORT,
    CACHE_LONG=settings.CACHE_LONG,
    CACHE_LONGER=settings.CACHE_LONGER,
    CACHE_MAX=settings.CACHE_MAX,
    CACHE_ETERNAL=settings.CACHE_ETERNAL,
)


def Global(request):
    data = dict(**GlobalContextData,
                alerts=[],
                KNOTBOT=Profile.KNOTBOT(),
                knotbot=Profile.KNOTBOT(),
                BROWSE=Browse.getAllKeys(),
                SCRIPTS=Template.Script.getAllKeys(),
                ACTIONS=Action.getAllKeys(),
                CODE=Code.getAllKeys(),
                SUBAPPS=dict(),
                SUBAPPSLIST=[],
                SOCIALS=ThirdPartyAccount.get_all(),
                LEGAL_DOCS=LegalDoc.get_all(),
                )

    for div in DIVISIONS:
        data['SUBAPPS'][div] = div
        data['SUBAPPSLIST'].append(div)

    return renderData(data)
