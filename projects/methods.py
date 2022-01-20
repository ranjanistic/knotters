from uuid import UUID
from django.core.handlers.wsgi import WSGIRequest
from django.core.cache import cache
from django.http.response import HttpResponse
from people.models import Profile
from github import NamedUser, Repository
from main.bots import Github, GithubKnotters
from main.strings import Code, Event, url, Message
from main.methods import addMethodToAsyncQueue, errorLog, renderString, renderView
from django.conf import settings
from main.env import ISPRODUCTION, SITE
from .models import Category, CoreProject, FreeProject, License, Project, ProjectSocial, Tag
from .apps import APPNAME
from .mailers import sendProjectApprovedNotification


def renderer(request: WSGIRequest, file: str, data: dict = dict()) -> HttpResponse:
    return renderView(request, file, data, fromApp=APPNAME)


def rendererstr(request: WSGIRequest, file: str, data: dict = dict()) -> HttpResponse:
    return HttpResponse(renderString(request, file, data, fromApp=APPNAME))

def renderer_stronly(request: WSGIRequest, file: str, data: dict = dict()) -> str:
    return renderString(request, file, data, fromApp=APPNAME)


def createFreeProject(name: str, category: str, nickname: str, description: str, creator: Profile, licenseID: UUID,sociallinks=[]) -> Project or bool:
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
        nickname = uniqueRepoName(nickname)
        if not nickname:
            return False
        license = License.objects.get(id=licenseID)
        category = Category.objects.get(id=category)
        project = FreeProject.objects.create(creator=creator, name=name, description=description, category=category, license=license, nickname=nickname)
        socials = []
        for soc in sociallinks:
            socials.append(ProjectSocial(project=project,site=str(soc).strip()))
        ProjectSocial.objects.bulk_create(socials)
        return project
    except Exception as e:
        errorLog(e)
        return False

def createProject(name: str, category: str, reponame: str, description: str, creator: Profile, licenseID: UUID, url: str = str()) -> Project or bool:
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
        categoryObj = addCategoryToDatabase(category, creator)
        if not categoryObj:
            return False
        return Project.objects.create(
            creator=creator, name=name, reponame=reponame, description=description, category=categoryObj, url=url, license=license)
    except Exception as e:
        errorLog(e)
        return False

def createCoreProject(name: str, category: str, codename: str, description: str, creator: Profile) -> CoreProject or bool:
    """
    Creates core project on knotters under moderation status.

    :name: Display name of project
    :category: The category of project
    :reponame: Repository name, a unique indetifier of project
    :description: Visible about (bio) of project
    :tags: List of tag strings
    :creator: The profile of project creator
    """
    try:
        codename = uniqueRepoName(codename)
        if not codename:
            return False
        categoryObj = addCategoryToDatabase(category, creator)
        if not categoryObj:
            return False
        return CoreProject.objects.create(creator=creator, name=name, codename=codename, description=description, category=categoryObj)
    except Exception as e:
        errorLog(e)
        return False


def addCategoryToDatabase(category: str, creator = None) -> Category:
    category = str(category).strip().replace('\n', str())
    if not category:
        return False
    categoryObj = None
    try:
        categoryObj = Category.objects.filter(name__iexact=category).first()
        if not categoryObj:
            categoryObj = Category.objects.create(name=category, creator=creator)
    except:
        if not categoryObj:
            categoryObj = Category.objects.create(name=category, creator=creator)
    return categoryObj


def addTagToDatabase(tag: str, creator = None) -> Tag:
    tag = str(tag).strip('#').strip().replace(
        '\n', str()).replace(" ", "_").strip()
    if not tag or tag == '':
        return False
    tagobj = uniqueTag(tag)
    if tagobj == True:
        tagobj = Tag.objects.create(name=tag, creator=creator)
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
    elif FreeProject.objects.filter(nickname__iexact=str(reponame), trashed=False).exists():
        return False
    return reponame if reponame and reponame != str() else False



def uniqueTag(tagname: str) -> Tag:
    """
    Checks for unique tag name among existing tags. Returns true if given tagname is unique, otherwise returns the matching Tag object
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
        task = cache.get(f'approved_project_setup_{project.id}')
        if task in [Message.SETTING_APPROVED_PROJECT, Message.SETUP_APPROVED_PROJECT_DONE]:
            return True
        cache.set(f'approved_project_setup_{project.id}', Message.SETTING_APPROVED_PROJECT, None)
        addMethodToAsyncQueue(f"{APPNAME}.methods.{setupOrgGihtubRepository.__name__}",project,moderator)
        return True
    except Exception as e:
        errorLog(e)
        return False

def setupApprovedCoreProject(project: CoreProject, moderator: Profile) -> bool:
    """
    Setup project which has been approved by moderator. (project status should be: LIVE)

    Creates github org repository and setup restrictions & allowances.

    Creates discord chat channel.
    """
    try:
        if not project.isApproved():
            return False
        task = cache.get(f'approved_coreproject_setup_{project.id}')
        if task in [Message.SETTING_APPROVED_PROJECT, Message.SETUP_APPROVED_PROJECT_DONE]:
            return True
        cache.set(f'approved_coreproject_setup_{project.id}', Message.SETTING_APPROVED_PROJECT, None)
        addMethodToAsyncQueue(f"{APPNAME}.methods.{setupOrgGihtubRepository.__name__}",project,moderator)
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
        if not project.creator.ghID or not moderator.ghID:
            return False

        ghUser = Github.get_user(project.creator.ghID)
        ghMod = Github.get_user(moderator.ghID)

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
                ghOrgRepo.create_file('LICENSE','Add LICENSE',str(project.license.content))

        ghBranch = ghOrgRepo.get_branch("main")

        ghBranch.edit_protection(
            strict=True,
            enforce_admins=False,
            dismiss_stale_reviews=True,
            required_approving_review_count=1,
            user_push_restrictions=[moderator.ghID],
        )

        inviteMemberToGithubOrg(ghUser)

        try:
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
        except:
            pass

        ghOrgRepo.add_to_collaborators(
            collaborator=moderator.ghID, permission="maintain")
        ghOrgRepo.add_to_collaborators(
            collaborator=project.creator.ghID, permission="push")

        ghOrgRepo.create_hook(
            name='web',
            config=dict(
                url=f"{SITE}{url.getRoot(fromApp=APPNAME)}{url.projects.githubEvents(type=Code.HOOK,projID=project.get_id)}",
                content_type='form',
                secret=settings.GH_HOOK_SECRET,
                insecure_ssl=0,
                digest=Code.SHA256
            )
        )
        cache.set(f'approved_project_setup_{project.id}', Message.SETUP_APPROVED_PROJECT_DONE, None)
        addMethodToAsyncQueue(f"{APPNAME}.mailers.{sendProjectApprovedNotification.__name__}",project)
        return True
    except Exception as e:
        errorLog(e)
        return False

def setupOrgGihtubRepository(coreproject: CoreProject, moderator: Profile) -> bool:
    """
    Creates github org repository and setup restrictions & allowances for corresponding project.

    Invites creator to organization & created repository

    :reponame: The name of repository to be created
    """
    try:
        if not coreproject.isApproved():
            return False
        if not moderator.ghID:
            return False
        ghUser = None
        try:
            ghUser = Github.get_user(coreproject.creator.ghID)
        except:
            pass
        ghMod = Github.get_user(moderator.ghID)

        ghOrgRepo = getGhOrgRepo(coreproject.codename)

        if not ghOrgRepo:
            ghOrgRepo = GithubKnotters.create_repo(
                name=coreproject.codename,
                homepage=f"{SITE}{coreproject.getLink()}",
                description=coreproject.description,
                auto_init=True,
                has_issues=True,
                has_projects=True,
                has_wiki=True,
                private=True,
                has_downloads=True,
                allow_squash_merge=True,
                allow_merge_commit=True,
                allow_rebase_merge=True,
                delete_branch_on_merge=False
            )

        ghBranch = ghOrgRepo.get_branch("main")

        ghBranch.edit_protection(
            strict=False,
            enforce_admins=False,
            dismiss_stale_reviews=True,
            required_approving_review_count=0,
        )
        if ghUser:
            inviteMemberToGithubOrg(ghUser)

        try:
            ghrepoteam = GithubKnotters.create_team(
                name=f"team-{coreproject.codename}",
                repo_names=[ghOrgRepo],
                permission="push",
                description=f"{coreproject.name}'s team",
                privacy='closed'
            )

            if GithubKnotters.has_in_members(ghMod):
                ghrepoteam.add_membership(
                    member=ghMod,
                    role="maintainer"
                )
            if ghUser:
                if GithubKnotters.has_in_members(ghUser):
                    ghrepoteam.add_membership(
                        member=ghUser,
                        role="member"
                    )
        except:
            pass

        ghOrgRepo.add_to_collaborators(
            collaborator=moderator.ghID, permission="maintain")
        if ghUser:
            ghOrgRepo.add_to_collaborators(
                collaborator=coreproject.creator.ghID, permission="push")

        ghOrgRepo.create_hook(
            name='web',
            config=dict(
                url=f"{SITE}{url.getRoot(fromApp=APPNAME)}{url.projects.githubEvents(type=Code.HOOK,projID=coreproject.get_id)}",
                content_type='form',
                secret=settings.GH_HOOK_SECRET,
                insecure_ssl=0,
                digest=Code.SHA256
            )
        )
        cache.set(f'approved_coreproject_setup_{coreproject.id}', Message.SETUP_APPROVED_PROJECT_DONE, None)
        addMethodToAsyncQueue(f"{APPNAME}.mailers.{sendProjectApprovedNotification.__name__}",coreproject)
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


def getProjectLiveData(project: Project):
    if ISPRODUCTION:
        ghOrgRepo = getGhOrgRepo(project.reponame)
        contribs = ghOrgRepo.get_contributors()
        languages = ghOrgRepo.get_languages()
        ghIDs = []
        for cont in contribs:
            ghIDs.append(str(cont.login))
        contributors = Profile.objects.filter(githubID__in=ghIDs).order_by('-xp')
        contributors = list(filter(lambda c: not c.is_manager, list(contributors)))
        return contributors, languages
    else:
        return [], []

from .receivers import *
