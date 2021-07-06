from .env import GITHUBBOTTOKEN, PUBNAME, ISPRODUCTION
from github import Github as GHub

if ISPRODUCTION:
    Github = GHub(GITHUBBOTTOKEN)
    GithubKnotters = Github.get_organization(PUBNAME)
else:
    Github = 0
    GithubKnotters = 0
