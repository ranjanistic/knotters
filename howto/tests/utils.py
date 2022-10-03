from uuid import uuid4
from main.strings import url
from howto.apps import APPNAME
from projects.models import Tag


def root(path='/', appendslash=False):
    return f"{url.getRoot(APPNAME, not appendslash)}{path}"


def getArticleHeading():
    return f'Article {uuid4().hex}'


def getArticleSubHeading():
    return f"{uuid4().hex} {uuid4().hex} {uuid4().hex}"


def getTestSubhHeading():
    return f'Test {uuid4().hex}'


def getTestParagraph():
    return f'Test {uuid4().hex} {uuid4().hex} {uuid4().hex}'


def getTestImage():
    return f"test_{uuid4().hex}.png"


def getTestVideo():
    return f"test_{uuid4().hex}.mp4"


def getTag():
    return f'test_{uuid4().hex}'


def getTestTags(count=1, start=0):
    tags = []
    for i in range(count):
        tags.append(f"test_{uuid4().hex}{i+start}")
    return tags


def getTestTagsInst(count=1, start=0):
    tags = []
    for name in getTestTags(count, start):
        tags.append(Tag(name=name))
    return tags
