
from uuid import uuid4
from django.contrib.auth.hashers import make_password
from main.strings import url
from projects.apps import APPNAME
from projects.models import Tag

def root(path='/', appendslash=False):
    return f"{url.getRoot(APPNAME, not appendslash)}{path}"


def getProjName():
    return f'Test {uuid4().hex}'

def getProjRepo():
    return f"test-{str(uuid4()).split('-')[0]}"

def getProjImage():
    return f"test_{uuid4().hex}.png"

def getProjDesc():
    return f"{uuid4().hex} {uuid4().hex} {uuid4().hex}"

def getProjCategory():
    return f'Test {uuid4().hex}'

def getLicName():
    return f"test_{uuid4().hex}"

def getLicDesc():
    return f"test_{uuid4().hex}"

def getTag():
    return f'test_{uuid4().hex}'

def getTestTags(count=1,start=0):
    tags = []
    for i in range(count):
        tags.append(f"test_{uuid4().hex}{i+start}")
    return tags

def getTestTagsInst(count=1,start=0):
    tags = []
    for name in getTestTags(count,start):
        tags.append(Tag(name=name))
    return tags
