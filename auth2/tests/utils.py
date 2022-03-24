from uuid import uuid4
from django.contrib.auth.hashers import make_password
from main.strings import url
from auth2.apps import APPNAME


def root(path='/', appendslash=False):
    return f"{url.getRoot(APPNAME, not appendslash)}{path}"


def getTestEmail():
    return f"test_{uuid4().hex}@knotters.org"


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

def getTestGHID():
    return uuid4().hex
