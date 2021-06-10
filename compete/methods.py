from main.methods import renderView
from .apps import APPNAME


def renderer(request, file, data={}):
    data['root'] = f"/{APPNAME}"
    data['subappname'] = APPNAME
    return renderView(request, f"{APPNAME}/{file}", data)

def competeBannerPath(instance, filename):
    return f"{APPNAME}/{instance.id}/{filename}"
