from uuid import uuid4
from django.contrib.auth.hashers import make_password
from main.strings import url
from people.models import User, Topic
from people.apps import APPNAME


def root(path='/', appendslash=False):
    return f"{url.getRoot(APPNAME, not appendslash)}{path}"


def getTestEmail():
    return f"{uuid4().hex}@knotters.org"


def getTestEmails(count=1):
    emails = []
    for _ in range(count):
        emails.append(getTestEmail())
    return emails


def getTestFName():
    return uuid4().hex


def getTestLName():
    return uuid4().hex


def getTestName():
    return f"Testing {uuid4().hex}"


def getTestNames(count=1):
    names = []
    for _ in range(count):
        names.append(getTestName())
    return names


def getTestPassword():
    return uuid4().hex


def getTestPasswords(count=1):
    passwords = []
    for _ in range(count):
        passwords.append(getTestPassword())
    return passwords


def getTestPasswordHash():
    return make_password(uuid4().hex, None, 'md5')


def getTestPasswordsHash(count=1):
    hashes = []
    for _ in range(count):
        hashes.append(make_password(
            uuid4().hex, None, 'md5'))
    return hashes


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
        topics.append(uuid4().hex)
    return topics


def getTestTopicsInst(count=1):
    topics = []
    for name in getTestTopics(count):
        topics.append(Topic(name=name))
    return topics


def getTestGHID():
    return uuid4().hex


def getTestDP():
    return f'{uuid4().hex}.png'


def getTestBio():
    return f"{uuid4().hex} {uuid4().hex} {uuid4().hex}"
