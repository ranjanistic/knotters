from github import Github as GHub
from .env import GITHUBBOTTOKEN, PUBNAME, ISPRODUCTION

if ISPRODUCTION:
    Github = GHub(GITHUBBOTTOKEN)
    GithubKnotters = Github.get_organization(PUBNAME)
else:
    Github = None
    GithubKnotters = None
