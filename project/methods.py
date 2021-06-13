from .models import *
from main.env import GITHUBBOTTOKEN, PUBNAME
from github import Github, BranchProtection, Organization
from main.methods import renderView
from .apps import APPNAME


def renderer(request, file, data={}):
    data['root'] = f"/{APPNAME}"
    data['subappname'] = APPNAME
    return renderView(request, f"{APPNAME}/{file}", data)


def projectImagePath(instance, filename):
    return f'{APPNAME}/{instance.id}/{filename}'


def defaultImagePath():
    return f'/{APPNAME}/default.png'


def createProject(name, reponame, description, tags, user):
    """
    Creates project on knotters under moderation.
    """
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
    """
    Checks for unique repository name among existing projects
    """
    try:
        Project.objects.get(reponame=reponame)
    except:
        return True
    return False


def uniqueTag(tagname):
    """
    Checks for unique tag name among existing tags
    """
    try:
        Tag.objects.get(name=tagname)
    except:
        return True
    return False


def setupNewProject(project, moderator) -> bool:
    """
    Setup project which has been approved from moderation. (project status should be: LIVE)

    Creates github org repository and setup restrictions & allowances.

    Creates discord chat channel.
    """
    try:
        if project.status != code.LIVE:
            return False

        created = setupOrgGihtubRepository(
            project.reponame, project.creator, moderator, project.description)
        if not created:
            return False

        created = setupProjectDiscordChannel(
            project.reponame, project.creator, moderator)
        if not created:
            return False

        return True
    except:
        return False


def setupOrgGihtubRepository(reponame, creator, moderator, description):
    """
    Creates github org repository and setup restrictions & allowances for corresponding project.

    Invites creator to organization & created repository
    """
    try:
        if creator.profile.githubID == None:
            return False

        gh = Github(GITHUBBOTTOKEN)

        ghUser = gh.get_user(creator.profile.githubID)

        ghOrg = gh.get_organization(PUBNAME)
        ghOrgRepo = ghOrg.get_repo(name=reponame)
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

        ghBranch = ghOrgRepo.getBranch("main")
        ghBranch.edit_protection(
            strict=True,
            enforce_admins=False,
            dismiss_stale_reviews=True,
            required_approving_review_count=1,
            user_push_restrictions=[moderator.profile.githubID],
        )

        invited = inviteMemberToGithubOrg(ghOrg,ghUser)
        if not invited:
            return False

        ghOrgRepo.add_to_collaborators(
            collaborator=moderator.profile.githubID, permission="maintain")
        ghOrgRepo.add_to_collaborators(
            collaborator=creator.profile.githubID, permission="push")

        return True
    except:
        return False


def inviteMemberToGithubOrg(ghOrg,ghUser):
    try:
        already = ghOrg.has_in_members(ghUser)
        if not already:
            ghOrg.invite_user(user=ghUser, role="direct_member")
        return True
    except:
        return False


def setupProjectDiscordChannel(reponame, creator, moderator):
    """
    Creates discord chat channel for corresponding project.
    """
    return True

