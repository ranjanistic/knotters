from uuid import uuid4

TEST_COMP_TITLE = f'Test competition {uuid4().hex}'
TEST_COMP_PERKS = f'perk {uuid4().hex};perk {uuid4().hex};perk {uuid4().hex}'
TEST_BANNER = f'testingbanner{uuid4().hex}.png'


def getSubmissionRepos(count=1, start=0):
    repos = []
    for i in range(count):
        repos.append(
            f"https://testing.knotters.org/submission{i+start}{uuid4().hex}")
    return repos
