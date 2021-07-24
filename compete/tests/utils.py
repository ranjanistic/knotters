TEST_COMP_TITLE = 'Test competition'
TEST_COMP_PERKS = '12000;10000;9000'

def getSubmissionRepos(count=1,start=0):
    repos = []
    for i in range(count):
        repos.append(f"https://testing.knotters.org/submission{i+start}")
    return repos