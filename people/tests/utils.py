from uuid import uuid4

from auth2.tests.utils import getTestEmails, getTestNames, getTestPasswords
from django.contrib.auth.hashers import make_password
from main.strings import url
from people.apps import APPNAME
from people.models import Topic, User


def root(path='/', appendslash=False):
    return f"{url.getRoot(APPNAME, not appendslash)}{path}"


def getTestUsersInst(count=1):
    testemails = getTestEmails(count)
    testnames = getTestNames(count)
    testpswds = getTestPasswords(count)
    users = []
    for i in range(len(testemails)):
        users.append(User(email=testemails[i], first_name=testnames[i], password=make_password(
            testpswds[i], None, 'md5'), is_active=True))
    return users


def getTestTopic():
    return uuid4().hex


def getTestTopics(count=1):
    topics = []
    for _ in range(count):
        topics.append(getTestTopic())
    return topics


def getTestTopicsInst(count=1):
    topics = []
    for name in getTestTopics(count):
        topics.append(Topic(name=name))
    return topics


def getTestDP():
    return f'{uuid4().hex}.png'


def getTestBio():
    return f"{uuid4().hex} {uuid4().hex} {uuid4().hex}"
