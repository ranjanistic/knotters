from people.models import User, Topic
from random import randint
from uuid import uuid4
from django.contrib.auth.hashers import make_password

TEST_NAME = 'Testing'
TEST_EMAIL = 'testing@knotters.org'
TEST_PASSWORD = '12345@abcde'
TEST_TOPIC = 'Test Topic'
TEST_GHID = 'testing'
TEST_DP = 'testing.png'


def getTestEmails(count=1,start=0):
    emails = []
    for i in range(count):
        emails.append(f"testing{i+start}.{uuid4().hex}@knotters.org")
    return emails


def getTestNames(count=1,start=0):
    names = []
    for i in range(count):
        names.append(f"Testing {i+start}{randint(0,count)}")
    return names


def getTestPasswords(count=1,start=0):
    passwords = []
    for i in range(count):
        passwords.append(f"12345@abcde{i+start}{randint(0,count)}")
    return passwords

def getTestPasswordsHash(count=1,start=0):
    hashes = []
    for i in range(count):
        hashes.append(make_password(f"12345@abcde{i+start}{randint(0,count)}", None, 'md5'))
    return hashes


def getTestUsersInst(count=1, start=0):
    testemails = getTestEmails(count,start)
    testnames = getTestNames(count,start)
    testpswds = getTestPasswords(count,start)
    users = []
    for i in range(len(testemails)):
        users.append(User(email=testemails[i], first_name=testnames[i], password=make_password(
            testpswds[i], None, 'md5'), is_active=True))
    return users

def getTestTopics(count=1,start=0):
    topics = []
    for i in range(count):
        topics.append(f"Test Topic {i+start}{uuid4().hex}")
    return topics

def getTestTopicsInst(count=1,start=0):
    topics = []
    for name in getTestTopics(count,start):
        topics.append(Topic(name=name))
    return topics