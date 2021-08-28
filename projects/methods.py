from uuid import UUID
from django.core.handlers.wsgi import WSGIRequest
from django.http.response import HttpResponse
from people.models import Profile
from github import NamedUser, Repository
from main.bots import Github, GithubKnotters
from main.strings import Code, Event, url
from main.methods import errorLog, renderString, renderView
from django.conf import settings
from main.env import ISPRODUCTION, SITE
from .models import Category, License, Project, Tag
from .apps import APPNAME
from .mailers import sendProjectApprovedNotification


def renderer(request: WSGIRequest, file: str, data: dict = dict()) -> HttpResponse:
    return renderView(request, file, data, fromApp=APPNAME)


def rendererstr(request: WSGIRequest, file: str, data: dict = dict()) -> HttpResponse:
    return HttpResponse(renderString(request, file, data, fromApp=APPNAME))


def createProject(name: str, category: str, reponame: str, description: str, tags: list, creator: Profile, licenseID: UUID, url: str = str()) -> Project or bool:
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
        reponame = uniqueRepoName(reponame)
        if not reponame:
            return False
        license = License.objects.get(id=licenseID)
        categoryObj = addCategoryToDatabase(category)
        if not categoryObj:
            return False
        project = Project.objects.create(
            creator=creator, name=name, reponame=reponame, description=description, category=categoryObj, url=url, license=license)
        if tags:
            count = 0
            for tag in tags:
                if count == 5:
                    break
                tagobj = addTagToDatabase(tag)
                if tagobj:
                    project.tags.add(tagobj)
                    categoryObj.tags.add(tagobj)
                    count = count + 1
        return project
    except Exception as e:
        errorLog(e)
        return False


def addCategoryToDatabase(category: str) -> Category:
    category = str(category).strip().replace('\n', str())
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
    tag = str(tag).strip('#').strip().replace(
        '\n', str()).replace(" ", "_").strip()
    if not tag or tag == '':
        return False
    tagobj = uniqueTag(tag)
    if tagobj == True:
        tagobj = Tag.objects.create(name=tag)
    return tagobj


def uniqueRepoName(reponame: str) -> bool:
    """
    Checks for unique repository name among existing projects
    """
    if reponame.startswith('-') or reponame.endswith('-') or reponame.__contains__('--'):
        return False
    reponame = str(reponame).strip(
        '-').strip().replace(' ', '-').replace('--', '-').lower()
    if len(reponame) > 20 or len(reponame) < 3:
        return False
    project = Project.objects.filter(
        reponame=str(reponame), trashed=False).first()
    if project:
        if project.rejected() and project.canRetryModeration():
            return False
        if project.underModeration() or project.isApproved():
            return False

    return reponame if reponame and reponame != str() else False


def uniqueTag(tagname: str) -> Tag:
    """
    Checks for unique tag name among existing tags
    """
    try:
        return Tag.objects.get(name__iexact=tagname)
    except:
        return True


def setupApprovedProject(project: Project, moderator: Profile) -> bool:
    """
    Setup project which has been approved by moderator. (project status should be: LIVE)

    Creates github org repository and setup restrictions & allowances.

    Creates discord chat channel.
    """
    try:
        if not project.isApproved():
            return False

        created = setupOrgGihtubRepository(project, moderator)

        if not created and ISPRODUCTION:
            return False

        sendProjectApprovedNotification(project)

        # created = setupProjectDiscordChannel(
        #     project.reponame, project.creator.profile, moderator)
        # if not created:
        #     return False

        return True
    except Exception as e:
        errorLog(e)
        return False


def setupOrgGihtubRepository(project: Project, moderator: Profile) -> bool:
    """
    Creates github org repository and setup restrictions & allowances for corresponding project.

    Invites creator to organization & created repository

    :reponame: The name of repository to be created
    """
    try:
        if not project.isApproved():
            return False
        if not project.creator.githubID or not moderator.githubID:
            return False

        ghUser = Github.get_user(project.creator.githubID)
        ghMod = Github.get_user(moderator.githubID)

        ghOrgRepo = getGhOrgRepo(project.reponame)

        if not ghOrgRepo:
            if project.license.keyword:
                ghOrgRepo = GithubKnotters.create_repo(
                    name=project.reponame,
                    homepage=f"{SITE}{project.getLink()}",
                    description=project.description,
                    license_template=project.license.keyword,
                    auto_init=True,
                    has_issues=True,
                    has_projects=True,
                    has_wiki=True,
                    private=False,
                    has_downloads=True,
                    allow_squash_merge=False,
                    allow_merge_commit=True,
                    allow_rebase_merge=False,
                    delete_branch_on_merge=False
                )
            else:
                ghOrgRepo = GithubKnotters.create_repo(
                    name=project.reponame,
                    homepage=f"{SITE}{project.getLink()}",
                    description=project.description,
                    auto_init=True,
                    has_issues=True,
                    has_projects=True,
                    has_wiki=True,
                    private=False,
                    has_downloads=True,
                    allow_squash_merge=False,
                    allow_merge_commit=True,
                    allow_rebase_merge=False,
                    delete_branch_on_merge=False
                )

        ghBranch = ghOrgRepo.get_branch("main")

        ghBranch.edit_protection(
            strict=True,
            enforce_admins=False,
            dismiss_stale_reviews=True,
            required_approving_review_count=1,
            user_push_restrictions=[moderator.githubID],
        )

        invited = inviteMemberToGithubOrg(ghUser)
        if not invited:
            return False

        ghrepoteam = GithubKnotters.create_team(
            name=f"team-{project.reponame}",
            repo_names=[ghOrgRepo],
            permission="push",
            description=f"{project.name}'s team",
            privacy='closed'
        )

        if GithubKnotters.has_in_members(ghMod):
            ghrepoteam.add_membership(
                member=ghMod,
                role="maintainer"
            )

        if GithubKnotters.has_in_members(ghUser):
            ghrepoteam.add_membership(
                member=ghUser,
                role="member"
            )

        ghOrgRepo.add_to_collaborators(
            collaborator=moderator.githubID, permission="maintain")
        ghOrgRepo.add_to_collaborators(
            collaborator=project.creator.githubID, permission="push")

        ghOrgRepo.create_hook(
            name='web',
            events=[Event.PUSH],
            config=dict(
                url=f"{SITE}{url.getRoot(fromApp=APPNAME)}{url.projects.githubEvents(type=Code.HOOK,event=Event.PUSH,projID=project.get_id)}",
                content_type='form',
                secret=settings.GH_HOOK_SECRET,
                insecure_ssl=0,
                digest=Code.SHA256
            )
        )
        ghOrgRepo.create_hook(
            name='web',
            events=[Event.PR],
            config=dict(
                url=f"{SITE}{url.getRoot(fromApp=APPNAME)}{url.projects.githubEvents(type=Code.HOOK,event=Event.PR,projID=project.get_id)}",
                content_type='form',
                secret=settings.GH_HOOK_SECRET,
                insecure_ssl=0,
                digest=Code.SHA256
            )
        )
        ghOrgRepo.create_hook(
            name='web',
            events=[Event.STAR],
            config=dict(
                url=f"{SITE}{url.getRoot(fromApp=APPNAME)}{url.projects.githubEvents(type=Code.HOOK,event=Event.STAR,projID=project.get_id)}",
                content_type='form',
                secret=settings.GH_HOOK_SECRET,
                insecure_ssl=0,
                digest=Code.SHA256
            )
        )
        return True
    except Exception as e:
        errorLog(e)
        return False


def getGhOrgRepo(reponame: str) -> Repository:
    try:
        return GithubKnotters.get_repo(name=reponame)
    except Exception as e:
        errorLog(e)
        return None


def inviteMemberToGithubOrg(ghUser: NamedUser) -> bool:
    try:
        already = GithubKnotters.has_in_members(ghUser)
        if not already:
            GithubKnotters.invite_user(user=ghUser, role="direct_member")
        return True
    except Exception as e:
        errorLog(e)
        return False


def setupProjectDiscordChannel(reponame: str, creator: Profile, moderator: Profile) -> bool:
    """
    Creates discord chat channel for corresponding project.
    """
    return True


def getProjectLiveData(project: Project) -> dict:
    if ISPRODUCTION:
        ghOrgRepo = getGhOrgRepo(project.reponame)
        contribs = ghOrgRepo.get_contributors()
        languages = ghOrgRepo.get_languages()
        ghIDs = []

        for cont in contribs:
            ghIDs.append(str(cont.login))
        contributors = Profile.objects.filter(githubID__in=ghIDs).order_by('-xp')
        return dict(contributors=contributors, languages=languages)
    else:
        return dict(contributors=[], languages=[])

from .receivers import *