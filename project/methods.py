from .models import *
from main.env import GITHUBBOTTOKEN, PUBNAME
from github import Github
from main.methods import renderView
from .apps import APPNAME


def renderer(request, file, data={}):
    data['root'] = f"/{APPNAME}"
    data['subappname'] = APPNAME
    return renderView(request, f"{APPNAME}/{file}", data)

def projectImagePath(instance,filename):
    return f'{APPNAME}/{instance.id}/{filename}'

def defaultImagePath():
    return f'/{APPNAME}/default.png'

# Creates project on knotters
def createProject(name, reponame, description, tags, user):
    try:
        if not uniqueRepoName(reponame):
            return False
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

