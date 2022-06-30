import string
import random
from uuid import uuid4

from auth2.apps import APPNAME
from django.contrib.auth.hashers import make_password
from main.strings import url


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


def getTestPassword(length: int = 20):
    characters = list(string.ascii_letters + string.digits + "!@#$%^&*()")
    random.shuffle(characters)
    password = []
    for i in range(length):
        password.append(random.choice(characters))
    random.shuffle(password)
    return "".join(password)


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
