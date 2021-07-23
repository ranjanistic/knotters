
TEST_NAME = 'Testing'
TEST_EMAIL = 'testing@knotters.org'
TEST_PASSWORD = '12345@abcde'
TEST_TOPIC = 'Test Topic'
TEST_GHID = 'testing'
TEST_DP = 'testing.png'

def getTestEmails(count=1):
    emails = []
    for i in range(count):
        emails.append(f"testing{i}@knotters.org")
    return emails

def getTestNames(count=1):
    names = []
    for i in range(count):
        names.append(f"Testing {i}")
    return names

def getTestPasswords(count=1):
    passwords = []
    for i in range(count):
        passwords.append(f"12345@abcde{i}")
    return passwords

def getTestTopics(count=1):
    topics = []
    for i in range(count):
        topics.append(f"Test Topic {i}")
    return topics