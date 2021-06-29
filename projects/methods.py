from people.models import Profile
from django.db.models.signals import post_delete
from django.dispatch import receiver
from .models import Category, Project, Tag
from main.env import GITHUBBOTTOKEN, PUBNAME
from github import Github, Branch, Organization, NamedUser
from main.methods import renderView
from .apps import APPNAME
from main.strings import code



def renderer(request, file, data={}):
    return renderView(request, file, data, fromApp=APPNAME)


def createProject(name:str, category:str, reponame:str, description:str, tags:list, profile:Profile) -> Project or bool:
    """
    Creates project on knotters under moderation.
    """
    try:
        if not uniqueRepoName(reponame):
            return False
        categoryObj = addCategoryToDatabase(category)
        if not categoryObj: return False
        project = Project.objects.create(
            creator=profile, name=name, reponame=reponame, description=description,category=categoryObj)
        for tag in tags:
            tagobj = addTagToDatabase(tag)
            if tagobj:
                project.tags.add(tagobj)
                categoryObj.tags.add(tagobj)
        return project
    except Exception as e:
        print(e)
        return False

def addCategoryToDatabase(category:str) -> Category or bool:
    category = str(category).strip().replace('\n','')
    if not category: return False
    try:
        categoryObj = Category.objects.get(name=category)
    except:
        categoryObj = Category.objects.create(name=category)
    return categoryObj

def addTagToDatabase(tag:str) -> Tag or bool:
    tag = str(tag).strip().replace('\n','')
    if not tag: return False
    tag = tag.replace(" ", "_")
    if uniqueTag(tag):
        tagobj = Tag.objects.create(name=tag)
    else:
        tagobj = Tag.objects.get(name=tag)
    return tagobj

def uniqueRepoName(reponame:str)-> bool:
    """
    Checks for unique repository name among existing projects
    """
    try:
        Project.objects.get(reponame=str(reponame))
    except Exception as e:
        return True
    return False


def uniqueTag(tagname:str) -> bool:
    """
    Checks for unique tag name among existing tags
    """
    try:
        Tag.objects.get(name=tagname)
    except Exception as e:
        return True
    return False


def setupApprovedProject(project:Project, moderator:Profile) -> bool:
    """
    Setup project which has been approved from moderation. (project status should be: LIVE)

    Creates github org repository and setup restrictions & allowances.

    Creates discord chat channel.
    """
    try:
        if project.status != code.LIVE:
            return False

        created = setupOrgGihtubRepository(
            project.reponame, project.creator.profile, moderator, project.description)
        if not created:
            return False

        created = setupProjectDiscordChannel(
            project.reponame, project.creator, moderator)
        if not created:
            return False

        return True
    except Exception as e:
        print(e)
        return False


def setupOrgGihtubRepository(reponame:str, creator:Profile, moderator:Profile, description:str) -> bool:
    """
    Creates github org repository and setup restrictions & allowances for corresponding project.

    Invites creator to organization & created repository

    :reponame: The name of repository to be created
    """
    try:
        if creator.githubID == None:
            return False
        
        gh = Github(GITHUBBOTTOKEN)

        ghUser = gh.get_user(creator.githubID)
        

        ghOrg = gh.get_organization(PUBNAME)
        ghOrgRepo = ghOrgRepoExists(ghOrg,reponame)
    
        if not ghOrgRepo:
            ghOrgRepo = ghOrg.create_repo(
                name=reponame,
                allow_rebase_merge=False,
                auto_init=True,
                description=description,
                has_issues=True,
                has_projects=True,
                has_wiki=True,
                private=False,
            )

        ghBranch = ghOrgRepo.get_branch("main")
        
        ghBranch.edit_protection(
            strict=True,
            enforce_admins=False,
            dismiss_stale_reviews=True,
            required_approving_review_count=1,
            user_push_restrictions=[moderator.githubID],
        )
        
        invited = inviteMemberToGithubOrg(ghOrg, ghUser)
        if not invited:
            return False
        
        ghOrgRepo.add_to_collaborators(
            collaborator=moderator.githubID, permission="maintain")
        ghOrgRepo.add_to_collaborators(
            collaborator=creator.githubID, permission="push")
        
        return True
    except Exception as e:
        print(e)
        return False

def ghOrgRepoExists(ghOrg:Organization,reponame:str) -> Branch or bool:
    try:
        ghOrgRepo = ghOrg.get_repo(name=reponame)
        return ghOrgRepo
    except:
        return False

def inviteMemberToGithubOrg(ghOrg:Organization, ghUser:NamedUser) -> bool:
    try:
        already = ghOrg.has_in_members(ghUser)
        if not already:
            ghOrg.invite_user(user=ghUser, role="direct_member")
        return True
    except Exception as e:
        print(e)
        return False


def setupProjectDiscordChannel(reponame:str, creator:Profile, moderator:Profile) -> bool:
    """
    Creates discord chat channel for corresponding project.
    """
    return True

@receiver(post_delete, sender=Project)
def on_project_delete(sender, instance, **kwargs):
    """
    Project cleanup.
    """
    try:
        instance.image.delete(save=False)
    except Exception as e: pass
