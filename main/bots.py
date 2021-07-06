from .env import GITHUBBOTTOKEN, PUBNAME, ISPRODUCTION
from github import Github as GHub

if ISPRODUCTION:
    Github = GHub(GITHUBBOTTOKEN)
    GithubKnotters = Github.get_organization(PUBNAME)
else:
    Github = None
    GithubKnotters = None
