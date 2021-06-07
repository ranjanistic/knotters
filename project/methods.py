from .models import *
from main.env import GITHUBBOTTOKEN, PUBNAME
from github import Github

# Creates project on knotters & then repository in github/Knotters using knottersbot
def createProject(name, reponame, description, tags, user):
    try:
        project = Project.objects.create(
            creator=user, name=name, reponame=reponame, description=description)
        for tag in tags:
            tag = str(tag).strip().replace(" ", "_")
            if uniqueTag(tag):
                tagobj = Tag.objects.create(name=tag)
            else:
                tagobj = Tag.objects.get(name=tag)
            project.tags.add(tagobj)
        return project
    except:
        return False

def uniqueRepoName(reponame):
    try:
        Project.objects.get(reponame=reponame)
    except:
        return True
    return False


def uniqueTag(tagname):
    try:
        Tag.objects.get(name=tagname)
    except:
        return True
    return False


def createRepository(reponame, description):
    return False
    g = Github(GITHUBBOTTOKEN)
    org = g.get_organization(PUBNAME)
    repo = org.create_repo(name=reponame, private=False,
                           description=description, auto_init=True)
    return repo


def protectBranchMain():
    return None
