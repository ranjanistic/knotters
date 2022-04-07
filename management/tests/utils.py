from main.strings import MANAGEMENT as APPNAME
from main.strings import url


def root(path='/', appendslash=False):
    return f"{url.getRoot(APPNAME, not appendslash)}{path}"
