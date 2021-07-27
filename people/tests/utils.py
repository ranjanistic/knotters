from people.models import User, Topic
from uuid import uuid4
from django.contrib.auth.hashers import make_password

TEST_FNAME = uuid4().hex
TEST_LNAME = uuid4().hex
TEST_NAME = f'Testing {uuid4().hex}'
TEST_EMAIL = f'{uuid4().hex}@knotters.org'
TEST_PASSWORD = uuid4().hex
TEST_TOPIC = uuid4().hex
TEST_GHID = uuid4().hex
TEST_DP = f'{uuid4().hex}.png'
TEST_BIO = f"{uuid4().hex} {uuid4().hex} {uuid4().hex}"

def getTestEmails(count=1):
    emails = []
    for _ in range(count):
        emails.append(f"{uuid4().hex}@knotters.org")
    return emails


def getTestNames(count=1):
    names = []
    for _ in range(count):
        names.append(f"Testing {uuid4().hex}")
    return names


def getTestPasswords(count=1):
    passwords = []
    for _ in range(count):
        passwords.append(uuid4().hex)
    return passwords


def getTestPasswordsHash(count=1):
    hashes = []
    for _ in range(count):
        hashes.append(make_password(
            uuid4().hex, None, 'md5'))
    return hashes


def getTestUsersInst(count=1, start=0):
    testemails = getTestEmails(count)
    testnames = getTestNames(count)
    testpswds = getTestPasswords(count)
    users = []
    for i in range(len(testemails)):
        users.append(User(email=testemails[i], first_name=testnames[i], password=make_password(
            testpswds[i], None, 'md5'), is_active=True))
    return users


def getTestTopics(count=1):
    topics = []
    for _ in range(count):
        topics.append(uuid4().hex)
    return topics


def getTestTopicsInst(count=1, start=0):
    topics = []
    for name in getTestTopics(count):
        topics.append(Topic(name=name))
    return topics
