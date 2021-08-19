from uuid import uuid4
from main.strings import url, COMPETE as APPNAME

def getCompTitle():
    return f'Test competition {uuid4().hex}'

def getCompPerks():
    return f'perk {uuid4().hex};perk {uuid4().hex};perk {uuid4().hex}'

def getCompBanner():
    return f'{uuid4().hex}.png'

def getSubmissionRepos(count=1, start=0):
    repos = []
    for i in range(count):
        repos.append(
            f"https://testing.knotters.org/submission{uuid4().hex}{i+start}")
    return repos

def root(path='/',appendslash=False):
    return f"{url.getRoot(APPNAME, not appendslash)}{path}"
