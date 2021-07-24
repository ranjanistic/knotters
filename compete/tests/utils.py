from uuid import uuid4

TEST_COMP_TITLE = 'Test competition'
TEST_COMP_PERKS = '12000;10000;9000'
TEST_BANNER = 'testingbanner.png'

def getSubmissionRepos(count=1,start=0):
    repos = []
    for i in range(count):
        repos.append(f"https://testing.knotters.org/submission{uuid4().hex}")
    return repos