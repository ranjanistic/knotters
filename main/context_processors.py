from .methods import renderData
from .env import PUBNAME, MAILUSER, SITE, VERSION
from .strings import DIVISIONS

def Global(request):
    data = {}
    data['APPNAME'] = PUBNAME
    data['CONTACTMAIL'] = MAILUSER
    data['DESCRIPTION'] = "Solving problems together."
    data['SITE'] = SITE
    data['VERSION'] = VERSION
    data['SUBAPPS'] = {}
    for div in DIVISIONS:
        data['SUBAPPS'][div] = div
    return renderData(data=data)