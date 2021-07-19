from people.models import Profile
from github import Organization, NamedUser, Repository
from main.bots import Github, GithubKnotters
from main.strings import Code, url
from main.methods import renderView, classAttrsToDict, replaceUrlParamsWithStr
from .models import Category, Project, Tag
from .apps import APPNAME
from .mailers import sendProjectApprovedNotification


def renderer(request, file, data={}):
    data['URLS'] = {}

    def cond(key, value):
        return str(key).isupper()

    urls = classAttrsToDict(url.Projects, cond)

    for key in urls:
        data['URLS'][key] = f"{url.getRoot(APPNAME)}{replaceUrlParamsWithStr(urls[key])}"

    return renderView(request, file, data, fromApp=APPNAME)


def createProject(name: str, category: str, reponame: str, description: str, tags: list, creator: Profile, url: str = '') -> Project or bool:
    """
    Creates project on knotters under moderation status.

    :name: Display name of project
    :category: The category of project
    :reponame: Repository name, a unique indetifier of project
    :description: Visible about (bio) of project
    :tags: List of tag strings
    :creator: The profile of project creator
    :url: A display link for project, optional
    """
    try:
        if not uniqueRepoName(reponame):
            return False
        categoryObj = addCategoryToDatabase(category)
        if not categoryObj:
            return False
        project = Project.objects.create(
            creator=creator, name=name, reponame=reponame, description=description, category=categoryObj, url=url)
        for tag in tags:
            tagobj = addTagToDatabase(tag)
            if tagobj:
                project.tags.add(tagobj)
                categoryObj.tags.add(tagobj)
        return project
    except Exception as e:
        print(e)
        return False


def addCategoryToDatabase(category: str) -> Category:
    category = str(category).strip().replace('\n', '')
    if not category:
        return False
    categoryObj = None
    try:
        categoryObj = Category.objects.filter(name__iexact=category).first()
        if not categoryObj:
            categoryObj = Category.objects.create(name=category)
    except:
        if not categoryObj:
            categoryObj = Category.objects.create(name=category)
    return categoryObj


def addTagToDatabase(tag: str) -> Tag:
    tag = str(tag).strip('#').strip().replace('\n', '').replace(" ", "_")
    if not tag:
        return False
    tagobj = uniqueTag(tag)
    if not tagobj:
        tagobj = Tag.objects.create(name=tag)
    return tagobj


def uniqueRepoName(reponame: str) -> bool:
    """
    Checks for unique repository name among existing projects
    """
    reponame = str(reponame).strip('-').strip().replace(' ', '-').lower()
    try:
        count = Project.objects.filter(reponame=str(reponame)).count()
        return count < 1
    except Exception as e:
        print(e)
        return True


def uniqueTag(tagname: str) -> bool:
    """
    Checks for unique tag name among existing tags
    """
    try:
        return Tag.objects.filter(name__iexact=tagname).first()
    except Exception as e:
        return True


def setupApprovedProject(project: Project, moderator: Profile) -> bool:
    """
    Setup project which has been approved by moderator. (project status should be: LIVE)

    Creates github org repository and setup restrictions & allowances.

    Creates discord chat channel.
    """
    try:
        if project.status != Code.APPROVED:
            return False

        sendProjectApprovedNotification(project)

        created = setupOrgGihtubRepository(
            project.reponame, project.creator, moderator, project.description)

        if not created:
            return False

        # created = setupProjectDiscordChannel(
        #     project.reponame, project.creator.profile, moderator)
        # if not created:
        #     return False

        return True
    except Exception as e:
        print(e)
        return False


def setupOrgGihtubRepository(reponame: str, creator: Profile, moderator: Profile, description: str) -> bool:
    """
    Creates github org repository and setup restrictions & allowances for corresponding project.

    Invites creator to organization & created repository

    :reponame: The name of repository to be created
    """
    try:
        if not creator.githubID or not moderator.githubID:
            return False

        ghUser = Github.get_user(creator.githubID)

        ghOrgRepo = getGhOrgRepo(GithubKnotters, reponame)

        if not ghOrgRepo:
            ghOrgRepo = GithubKnotters.create_repo(
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

        invited = inviteMemberToGithubOrg(GithubKnotters, ghUser)
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


def getGhOrgRepo(ghOrg: Organization, reponame: str) -> Repository:
    try:
        ghOrgRepo = ghOrg.get_repo(name=reponame)
        return ghOrgRepo
    except:
        return None


def inviteMemberToGithubOrg(ghOrg: Organization, ghUser: NamedUser) -> bool:
    try:
        already = ghOrg.has_in_members(ghUser)
        if not already:
            ghOrg.invite_user(user=ghUser, role="direct_member")
        return True
    except Exception as e:
        print(e)
        return False


def setupProjectDiscordChannel(reponame: str, creator: Profile, moderator: Profile) -> bool:
    """
    Creates discord chat channel for corresponding project.
    """
    return True

from .receivers import *