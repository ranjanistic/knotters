TEST_COMP_TITLE = 'Test competition'

def getSubmissionRepos(count=1,start=0):
    repos = []
    for i in range(count):
        repos.append(f"https://testing.knotters.org/submission{i+start}")
    return repos