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
    data['SUBAPPSLIST'] = []
    for div in DIVISIONS:
        data['SUBAPPS'][div] = div
        data['SUBAPPSLIST'].append(div)
    return renderData(data=data)