# import discord
from .env import GITHUBBOTTOKEN, PUBNAME
from github import Github as GHub
Github = GHub(GITHUBBOTTOKEN)
GithubKnotters = Github.get_organization(PUBNAME)
# Github = 1
# GithubKnotters = 2
