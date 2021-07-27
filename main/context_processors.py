from main.methods import renderData
from .env import PUBNAME, MAILUSER, SITE, VERSION
from .strings import DIVISIONS, URL
from .settings import STATIC_URL


def Global(request):
    data = dict(
        APPNAME=PUBNAME,
        CONTACTMAIL=MAILUSER,
        DESCRIPTION="Solving problems together.",
        SITE=SITE,
        VERSION=VERSION,
        SUBAPPS=dict(),
        SUBAPPSLIST=[],
        ICON=f"{STATIC_URL}graphics/self/icon.svg",
        SERVICE_WORKER=f"/{URL.SERVICE_WORKER}",
        MANIFESTURL=f"/{URL.MANIFEST}",
    )

    for div in DIVISIONS:
        data['SUBAPPS'][div] = div
        data['SUBAPPSLIST'].append(div)

    return renderData(data)
