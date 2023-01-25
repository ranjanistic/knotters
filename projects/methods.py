from re import sub as re_sub
from traceback import format_exc
from uuid import UUID

from allauth.account.models import EmailAddress
from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.handlers.wsgi import WSGIRequest
from django.db.models.query_utils import Q
from django.http.response import HttpResponse
from main.bots import Discord, GithubKnotters
from main.env import SITE
from main.methods import (addMethodToAsyncQueue, errorLog, renderString,
                          renderView)
from main.strings import Code, Event, Message, url, Browse
from management.models import HookRecord
from people.methods import addTopicToDatabase
from people.models import Profile
from moderation.models import Moderation
from compete.models import Submission
from .apps import APPNAME
from .mailers import (sendCoreProjectApprovedNotification,
                      sendProjectApprovedNotification)
from .models import (BaseProject, Category, CoreProject,
                     CoreProjectVerificationRequest, FileExtension,
                     FreeProject, FreeProjectVerificationRequest, License,
                     Project, ProjectSocial, Tag, Snapshot)
from people.models import Topic


def renderer(request: WSGIRequest, file: str, data: dict = dict()) -> HttpResponse:
    """Renders the given file with the given data under templates/projects

    Args:
        request: The request object
        file: The file to render under templates/projects, without the extension
        data: The data to pass to the template

    Returns:
        HttpResponse: The rendered text/html view with default and provided context data
    """
    return renderView(request, file, data, fromApp=APPNAME)


def rendererstr(request: WSGIRequest, file: str, data: dict = dict()) -> HttpResponse:
    """Returns text/html content as http response with the given data.

    Args:
        request (WSGIRequest): The request object.
        file (str): The file for html content under templates/projects, without extension.
        data (dict, optional): The data to pass to the template. Defaults to dict().

    Returns:
        HttpResponse: The text based html string content http response with default and provided context.
    """
    return HttpResponse(renderString(request, file, data, fromApp=APPNAME))


def renderer_stronly(request: WSGIRequest, file: str, data: dict = dict()) -> str:
    """Returns text/html content as string with the given context data.

    Args:
        request (WSGIRequest): The request object.
        file (str): The file for html content under templates/people, without extension.
        data (dict, optional): The data to pass to the template. Defaults to dict().

    Returns:
        str: The text/html string content with default and provided context.
    """
    return renderString(request, file, data, fromApp=APPNAME)


def freeProfileData(request, nickname: str = None, projectID: UUID = None) -> dict:
    """Returns the context data to render a quick (free) project profile page.

    Args:
        request (WSGIRequest): The request object.
        nickname (str, optional): The nickname of the project. Defaults to None.
        projectID (UUID, optional): The id of the project. Defaults to None.

    NOTE: Only one of the projectID or nickname are allowed to be None. If nickname is provided, it will be preferred.

    Returns:
        dict: The context data to render a quick (free) project profile page.
    """
    try:
        cacheKey = f"{APPNAME}_free_project"
        if nickname:
            cacheKey = f"{cacheKey}_{nickname}"
            project: FreeProject = cache.get(cacheKey, None)
            if not project:
                project: FreeProject = FreeProject.objects.get(
                    nickname=nickname, trashed=False, suspended=False)
                cache.set(cacheKey, project, settings.CACHE_INSTANT)
        else:
            cacheKey = f"{cacheKey}_{projectID}"
            project: FreeProject = cache.get(cacheKey, None)
            if not project:
                project: FreeProject = FreeProject.objects.get(
                    id=projectID, trashed=False, suspended=False)
                cache.set(cacheKey, project, settings.CACHE_INSTANT)

        iscreator = False if not request.user.is_authenticated else project.creator == request.user.profile
        if project.suspended and not iscreator:
            raise ObjectDoesNotExist(project, iscreator)
        isAdmirer = request.user.is_authenticated and project.isAdmirer(
            request.user.profile)
        iscocreator = False if not request.user.is_authenticated else project.co_creators.filter(
            user=request.user).exists()
        isRater = False if not request.user.is_authenticated else project.is_rated_by(
            profile=request.user.profile)
        return dict(
            project=project,
            iscreator=iscreator,
            isAdmirer=isAdmirer,
            iscocreator=iscocreator,
            isRater = isRater
        )
    except (ObjectDoesNotExist, ValidationError):
        pass
    except Exception as e:
        errorLog(e)
        pass
    return False


def verifiedProfileData(request, reponame: str = None, projectID: UUID = None) -> dict:
    """Returns the context data to render a verified project profile page.

    Args:
        request (WSGIRequest): The request object.
        reponame (str, optional): The reponame of the project. Defaults to None.
        projectID (UUID, optional): The id of the project. Defaults to None.

    NOTE: Only one of the projectID or reponame are allowed to be None. If reponame is provided, it will be preferred.

    Returns:
        dict: The context data to render a verified project profile page.
    """
    try:
        cacheKey = f"{APPNAME}_verified_project"
        if reponame:
            cacheKey = f"{cacheKey}_{reponame}"
            project: Project = cache.get(cacheKey, None)
            if not project:
                project: Project = Project.objects.get(
                    reponame=reponame, trashed=False, status=Code.APPROVED)
                cache.set(cacheKey, project, settings.CACHE_INSTANT)
        else:
            cacheKey = f"{cacheKey}_{projectID}"
            project: Project = cache.get(cacheKey, None)
            if not project:
                project: Project = Project.objects.get(
                    id=projectID, trashed=False, status=Code.APPROVED)
                cache.set(cacheKey, project, settings.CACHE_INSTANT)

        iscreator = False if not request.user.is_authenticated else project.creator == request.user.profile
        ismoderator = False if not request.user.is_authenticated else project.moderator(
        ) == request.user.profile
        if project.suspended and not (iscreator or ismoderator):
            raise ObjectDoesNotExist(project, iscreator, ismoderator)
        isAdmirer = request.user.is_authenticated and project.isAdmirer(
            request.user.profile)
        iscocreator = False if not request.user.is_authenticated else project.co_creators.filter(
            user=request.user).exists()
        isRater = False if not request.user.is_authenticated else project.is_rated_by(
            profile=request.user.profile)
        return dict(
            project=project,
            iscreator=iscreator,
            ismoderator=ismoderator,
            isAdmirer=isAdmirer,
            iscocreator=iscocreator,
            isRater = isRater
        )
    except (ObjectDoesNotExist, ValidationError):
        pass
    except Exception as e:
        errorLog(e)
        pass
    return False


def coreProfileData(request, codename: str = None, projectID: UUID = None) -> dict:
    """Returns the context data to render a core project profile page.

    Args:
        request (WSGIRequest): The request object.
        codename (str, optional): The codename of the project. Defaults to None.
        projectID (UUID, optional): The id of the project. Defaults to None.

    NOTE: Only one of the projectID or codename are allowed to be None. If codename is provided, it will be preferred.

    Returns:
        dict: The context data to render a core project profile page.
    """
    try:
        cacheKey = f"{APPNAME}_core_project"
        if codename:
            cacheKey = f"{cacheKey}_{codename}"
            project: CoreProject = cache.get(cacheKey, None)
            if not project:
                project: CoreProject = CoreProject.objects.get(
                    codename=codename, trashed=False, status=Code.APPROVED)
                cache.set(cacheKey, project, settings.CACHE_INSTANT)
        else:
            cacheKey = f"{cacheKey}_{projectID}"
            project: CoreProject = cache.get(cacheKey, None)
            if not project:
                project: CoreProject = CoreProject.objects.get(
                    id=projectID, trashed=False, status=Code.APPROVED)
                cache.set(cacheKey, project, settings.CACHE_INSTANT)

        iscreator = False if not request.user.is_authenticated else project.creator == request.user.profile
        ismoderator = False if not request.user.is_authenticated else project.moderator(
        ) == request.user.profile
        if project.suspended and not (iscreator or ismoderator):
            raise ObjectDoesNotExist('suspended', project)
        isAdmirer = request.user.is_authenticated and project.isAdmirer(
            request.user.profile)
        iscocreator = False if not request.user.is_authenticated else project.co_creators.filter(
            user=request.user).exists()
        isRater = False if not request.user.is_authenticated else project.is_rated_by(
            profile=request.user.profile)
        return dict(
            project=project,
            iscreator=iscreator,
            ismoderator=ismoderator,
            isAdmirer=isAdmirer,
            iscocreator=iscocreator,
            isRater = isRater
        )
    except (ObjectDoesNotExist, ValidationError):
        pass
    except Exception as e:
        errorLog(e)
        pass
    return False

def baseProfileData(request, projectID: UUID = None) -> dict:
    """Returns the context data to render a base project profile page.

    Args:
        request (WSGIRequest): The request object.
        codename (str, optional): The codename of the project. Defaults to None.
        projectID (UUID, optional): The id of the project. Defaults to None.

    NOTE: Only one of the projectID or codename are allowed to be None. If codename is provided, it will be preferred.

    Returns:
        dict: The context data to render a core project profile page.
    """
    try:
        cacheKey = f"{APPNAME}_base_project"
        
        cacheKey = f"{cacheKey}_{projectID}"
        project: BaseProject = cache.get(cacheKey, None)
        if not project:
            project: BaseProject = BaseProject.objects.get(
                id=projectID, trashed=False)
            cache.set(cacheKey, project, settings.CACHE_INSTANT)

        iscreator = False if not request.user.is_authenticated else project.creator == request.user.profile
        # ismoderator = False if not request.user.is_authenticated else project.moderator(
        # ) == request.user.profile
        if project.suspended and not (iscreator):
            raise ObjectDoesNotExist('suspended', project)
        isAdmirer = request.user.is_authenticated and project.isAdmirer(
            request.user.profile)
        iscocreator = False if not request.user.is_authenticated else project.co_creators.filter(
            user=request.user).exists()
        userRatingScore = 0 if not request.user.is_authenticated else project.rating_by_user(profile=request.user.profile)
        return dict(
            project=project,
            iscreator=iscreator,
            # ismoderator=ismoderator,
            isAdmirer=isAdmirer,
            iscocreator=iscocreator,
            userRatingScore=userRatingScore
        )
    except (ObjectDoesNotExist, ValidationError):
        pass
    except Exception as e:
        errorLog(e)
        pass
    return False


def createFreeProject(name: str, category: UUID, nickname: str, description: str, creator: Profile, licenseID: UUID, sociallinks: list = []) -> FreeProject:
    """
    Creates a free project on knotters.

    Args:
        name (str): Display name of project
        category (UUID): The category ID of project
        nickname (str): Nickname a unique indetifier of project
        description (str): Visible about (bio) of project
        creator (Profile): The profile of project creator
        licenseID (UUID): The id of license
        sociallinks (list): List of social links

    Returns:
        FreeProject: The created free project
        bool: False if exception occured
    """
    try:
        nickname = uniqueRepoName(nickname)
        if not nickname:
            return False
        license: License = License.get_cache_one(id=licenseID)
        category: Category = Category.get_cache_one(id=category)
        project: FreeProject = FreeProject.objects.create(
            creator=creator, name=name, description=description, category=category,
            license=license,
            nickname=nickname)
        socials = list(map(lambda s: ProjectSocial(
            project=project, site=str(s).strip()), sociallinks[:5]))
        ProjectSocial.objects.bulk_create(socials)
        return project
    except (ObjectDoesNotExist, ValidationError):
        pass
    except Exception as e:
        errorLog(e)
        pass
    return False


def createProject(name: str, category: str, reponame: str, description: str, creator: Profile, licenseID: UUID, url: str = str(), forConversion=False) -> Project:
    """
    Creates verified project on knotters under moderation status.

    Args:
        name (str): Display name of project
        category (str): The category name of project
        reponame (str): a unique indetifier of project
        description (str): Visible about (bio) of project
        creator (Profile): The profile of project creator
        licenseID (UUID): The id of license
        url (str): relevant link

    Returns:
        Project: The created verified project
        bool: False if exception occured
    """
    try:
        reponame = uniqueRepoName(reponame, forConversion)
        if not reponame:
            return False
        license = License.get_cache_one(id=licenseID)
        categoryObj = addCategoryToDatabase(category, creator)
        if not categoryObj:
            return False
        return Project.objects.create(
            creator=creator, name=name, reponame=reponame,
            description=description, category=categoryObj, url=url, license=license
        )
    # except (ObjectDoesNotExist, ValidationError):
    #     pass
    except Exception as e:
        errorLog(e)
        pass
    return False


def createCoreProject(name: str, category: Category, codename: str, description: str, creator: Profile, license: License, budget: int = 0) -> CoreProject:
    """
    Creates core project on knotters under moderation status.

    Args:
        name (str): Display name of project
        category (Category): The category of project
        codename (str): a unique indetifier of project
        description (str): Visible about (bio) of project
        creator (Profile): The profile of project creator
        license (License): The license instance
        budget (int): The project budget

    Returns:
        CoreProject: The created core project
        bool: False if exception occured
    """
    try:
        codename = uniqueRepoName(codename)
        if not codename:
            return False
        return CoreProject.objects.create(
            creator=creator, name=name, codename=codename, description=description,
            category=category, license=license, budget=budget
        )
    except (ObjectDoesNotExist, ValidationError):
        pass
    except Exception as e:
        errorLog(e)
        pass
    return False


def createConversionProjectFromFree(freeproject: FreeProject) -> Project:
    """Creates a verified project under moderation status from existing free project

    Args:
        freeproject (FreeProject): The existing freeproject instance

    Returns:
        Project: A new verified project instance
        bool: False if exception occurs
    """
    try:
        if not freeproject.is_normal():
            return False
        if Project.objects.filter(reponame=freeproject.nickname, status__in=[Code.MODERATION, Code.APPROVED], trashed=False, suspended=False, is_archived=False).exists():
            return False
        return Project.objects.create(
            creator=freeproject.creator,
            name=freeproject.name,
            reponame=freeproject.nickname,
            description=freeproject.description,
            category=freeproject.category,
            license=freeproject.license
        )
    except (ObjectDoesNotExist, ValidationError):
        pass
    except Exception as e:
        errorLog(e)
        pass
    return False


def createConversionProjectFromCore(coreproject: CoreProject, licenseID: UUID) -> Project:
    """Creates a verified project under moderation status from existing live core project

    Args:
        coreproject (CoreProject): The existing CoreProject instance

    Returns:
        Project: A new verified project instance
        bool: False if exception occurs
    """
    try:
        if Project.objects.filter(reponame=coreproject.codename, status__in=[Code.MODERATION, Code.APPROVED], trashed=False, suspended=False).exists():
            return False
        license = License.get_cache_one(id=licenseID)
        return Project.objects.create(
            creator=coreproject.creator,
            name=coreproject.name,
            reponame=coreproject.codename,
            description=coreproject.description,
            category=coreproject.category,
            license=license
        )
    except (ObjectDoesNotExist, ValidationError):
        pass
    except Exception as e:
        errorLog(e)
        pass
    return False


def addCategoryToDatabase(category: str, creator: Profile = None) -> Category:
    """To add a new category in database

    Args:
        category (str): The name of new category
        creator (Profile, optional): The creator profile instance. Defaults to knottersbot.

    Returns:
        Category: A category instance (new/existing)
    """
    category = re_sub(r'[^a-zA-Z0-9\/\- ]', "", category[:50])
    category = " ".join(list(filter(lambda c: c, category.split(' '))))
    category = "-".join(list(filter(lambda c: c, category.split('-'))))
    category = "/".join(list(filter(lambda c: c,
                        category.split('/')))).capitalize()
    if not category:
        return False
    categoryObj = None
    if not creator:
        creator = Profile.KNOTBOT()
    try:
        categoryObj: Category = Category.objects.filter(
            name__iexact=category).first()
        if not categoryObj:
            categoryObj: Category = Category.objects.create(
                name=category, creator=creator)
    except:
        if not categoryObj:
            categoryObj: Category = Category.objects.create(
                name=category, creator=creator)
    return categoryObj


def addTagToDatabase(tag: str, creator: Profile = None) -> Tag:
    """To add a new tag in database

    Args:
        category (str): The name of new tag
        creator (Profile, optional): The creator profile instance. Defaults to knottersbot.

    Returns:
        Tag: A tag instance (new/existing)
    """
    tag = re_sub(r'[^a-zA-Z0-9\_]', "", tag[:100])
    tag = "_".join(list(filter(lambda t: t, tag.split('_')))).lower()
    if not tag:
        return False
    tagobj = uniqueTag(tag)
    if tagobj is True:
        if not creator:
            creator = Profile.KNOTBOT()
        tagobj = Tag.objects.create(name=tag, creator=creator)
    return tagobj


def uniqueRepoName(reponame: str, forConversion: bool = False) -> "str|bool":
    """
    Checks for unique nickname name among all kinds of existing projects

    Args:
        reponame (str): The nickname to check for uniqueness
        forConversion (bool, optional): Whether this nickname is for conversion, in that case,
            the provided reponame is also checked against any pending verification request records, and is 
            allowed to be unique if any found.

    Returns:
        str: The reponame, if unique
        bool: False, if not.
    """
    if len(reponame) < 3 or len(reponame) > 20:
        return False

    reponame = re_sub(r'[^a-z0-9\-]', "", reponame[:20])
    reponame = "-".join(list(filter(lambda c: c, reponame.split('-')))).lower()

    project: Project = Project.objects.filter(
        reponame=reponame, trashed=False).first()
    if project:
        if project.rejected() and project.canRetryModeration():
            return False
        if project.underModeration() or project.isApproved():
            return False

    if FreeProject.objects.filter(nickname__iexact=reponame, trashed=False).exists():
        if not (forConversion and FreeProjectVerificationRequest.objects.filter(freeproject__nickname__iexact=reponame, resolved=False).exists()):
            return False
        else:
            return False

    project: CoreProject = CoreProject.objects.filter(
        codename=reponame, trashed=False).first()
    if project:
        if project.rejected() and project.canRetryModeration():
            return False
        if project.underModeration():
            return False
        if project.isApproved():
            if not (forConversion and CoreProjectVerificationRequest.objects.filter(coreproject__nickname__iexact=reponame, resolved=False).exists()):
                return False
            else:
                return False

    return reponame if reponame else False


def uniqueTag(tagname: str) -> Tag:
    """
    Checks for unique tag name among existing tags.

    Returns:
        Tag: The matching Tag object
        bool: True, if given tagname is unique
    """
    try:
        return Tag.objects.get(name__iexact=tagname)
    except:
        return True


def setupApprovedProject(project: Project, moderator: Profile) -> str:
    """
    Setup verified project which has been approved by moderator. (project status should be: LIVE)

    Args:
        project (Project): The approved verified project instance
        moderator (Profile): The moderator of the project (Could've been retrieved from project instance as well!?)

    Returns:
        str: The task ID of setting up project
        bool: False if any exception
    """
    try:
        if not project.isApproved():
            return False
        taskKey = f'approved_project_setup_{project.id}'
        task = cache.get(taskKey)
        if task == Message.SETTING_APPROVED_PROJECT:
            return True
        cache.set(taskKey, Message.SETTING_APPROVED_PROJECT,
                  settings.CACHE_LONG)
        return addMethodToAsyncQueue(
            f"{APPNAME}.methods.{setupOrgGihtubRepository.__name__}", project, moderator, taskKey)
    except Exception as e:
        errorLog(e)
        return False


def setupApprovedCoreProject(project: CoreProject, moderator: Profile) -> str:
    """
    Setup core project which has been approved by moderator. (project status should be: LIVE)

    Args:
        project (CoreProject): The approved core project instance
        moderator (Profile): The moderator of the project (Could've been retrieved from project instance as well!?)

    Returns:
        str: The task ID of setting up project
        bool: False if any exception
    """
    try:
        if not project.isApproved():
            return False
        taskKey = f'approved_coreproject_setup_{project.id}'
        task = cache.get(taskKey)
        if task == Message.SETTING_APPROVED_PROJECT:
            return True
        cache.set(taskKey, Message.SETTING_APPROVED_PROJECT,
                  settings.CACHE_LONG)
        return addMethodToAsyncQueue(
            f"{APPNAME}.methods.{setupOrgCoreGihtubRepository.__name__}", project, moderator, taskKey)
    except Exception as e:
        errorLog(e)
        return False


def setupOrgGihtubRepository(project: Project, moderator: Profile, taskKey: str) -> bool:
    """
    Creates github org repository and setup restrictions & allowances for corresponding project.
    Invites creator to organization & created repository
    Setup discord chat channel.

    Args:
        project (Project): The approved verified project instance
        moderator (Profile): The profile instance of its moderator
        taskKey (str): The key of task status in cache DB

    Returns:
        bool, str: True, message if successfully done, else False, error
    """
    try:
        if not project.isApproved():
            return False, "Verified project not approved"
        if not project.creator.has_ghID() or not moderator.has_ghID():
            return False, "Creator or moderator has no github ID"

        ghUser = project.creator.gh_user()
        ghMod = moderator.gh_user()

        ghOrgRepo = project.gh_repo()
        msg = 'init setup: '
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
                msg += 'repository done, license done, '
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
                msg += 'repository done, '
                try:
                    ghOrgRepo.create_file(
                        'LICENSE', 'Add LICENSE', str(project.license.content))
                    msg += 'license done, '
                except:
                    pass

        try:
            ghBranch = ghOrgRepo.get_branch("main")
            ghBranch.edit_protection(
                strict=True,
                enforce_admins=False,
                dismiss_stale_reviews=True,
                required_approving_review_count=1,
                user_push_restrictions=[moderator.ghID()],
            )
            msg += 'branch done, '
        except Exception as e:
            msg += f'branch err: {e},'
            pass

        try:
            if not ghOrgRepo.has_in_collaborators(ghMod):
                ghOrgRepo.add_to_collaborators(
                    collaborator=ghMod, permission="maintain")
                msg += 'repo maintainer done, '
            if not ghOrgRepo.has_in_collaborators(ghUser):
                ghOrgRepo.add_to_collaborators(
                    collaborator=ghUser, permission="push")
                msg += 'repo collaborator done, '
        except Exception as e:
            msg += f'repo collab err: {e},'
            pass

        ghrepoteam = project.gh_team()

        try:
            if not ghrepoteam:
                ghrepoteam = GithubKnotters.create_team(
                    name=project.gh_team_name,
                    repo_names=[ghOrgRepo],
                    permission="push",
                    description=f"{project.name}'s team",
                    privacy='closed'
                )
                msg += 'team done, '
        except Exception as e:
            msg += f'team err: {e},'
            pass

        try:
            if ghrepoteam:
                if not ghrepoteam.has_in_members(ghMod):
                    ghrepoteam.add_membership(
                        member=ghMod,
                        role="maintainer"
                    )
                    msg += 'team maintainer done, '
                if not ghrepoteam.has_in_members(ghUser):
                    ghrepoteam.add_membership(
                        member=ghUser,
                        role="member"
                    )
                    msg += 'team member done, '
        except Exception as e:
            msg += f'team member err: {e},'
            pass

        try:
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
            msg += 'hook done, '
        except Exception as e:
            msg += f'hook err: {e},'
            pass

        try:
            if setupVProjectDiscord(project):
                msg += f'discord done'
            else:
                raise Exception(project, "discrod not setup")
        except Exception as e:
            msg += f'discord err'

        cache.set(taskKey, Message.SETUP_APPROVED_PROJECT_DONE,
                  settings.CACHE_LONG)
        sendProjectApprovedNotification(project)
        return True, msg
    except Exception as e:
        errorLog(e)
        return False, e


def setupOrgCoreGihtubRepository(coreproject: CoreProject, moderator: Profile, taskKey: str) -> bool:
    """
    Creates github org repository and setup restrictions & allowances for corresponding project.
    Invites creator to organization & created repository
    Setup private discord chat channel.

    Args:
        coreproject (CoreProject): The approved core project instance
        moderator (Profile): The profile instance of its moderator
        taskKey (str): The key of task status in cache DB

    Returns:
        bool, str: True, message if successfully done, else False, error
    """
    try:
        if not coreproject.isApproved():
            return False, "Core project is not approved"
        if not moderator.has_ghID():
            return False, "Moderator has no github account"

        ghUser = coreproject.creator.gh_user()

        ghMod = moderator.gh_user()

        ghOrgRepo = coreproject.gh_repo()

        msg = 'init setup: '

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
            msg = "repository done, "

        try:
            ghOrgRepo.create_file('LICENSE', 'Add LICENSE',
                                  str(coreproject.license.content))
            msg = msg + "license done, "
        except Exception as e:
            msg += f'license err: {e},'
            pass

        try:
            if not ghOrgRepo.has_in_collaborators(ghMod):
                ghOrgRepo.add_to_collaborators(
                    collaborator=ghMod, permission="maintain")
                msg = msg + "repo maintainer done, "
            if ghUser:
                if not ghOrgRepo.has_in_collaborators(ghUser):
                    ghOrgRepo.add_to_collaborators(
                        collaborator=ghUser, permission="push")
                    msg = msg + "repo member done, "
        except Exception as e:
            msg += f'repo collab: {e},'
            pass

        ghrepoteam = coreproject.gh_team()
        try:
            if not ghrepoteam:
                ghrepoteam = GithubKnotters.create_team(
                    name=coreproject.gh_team_name,
                    repo_names=[ghOrgRepo],
                    permission="push",
                    description=f"{coreproject.name}'s team",
                    privacy='closed'
                )
                msg = msg + "team done, "
        except Exception as e:
            msg += f'team err: {e},'
            pass

        try:
            if ghrepoteam:
                if not ghrepoteam.has_in_members(ghMod):
                    ghrepoteam.add_membership(
                        member=ghMod,
                        role="maintainer"
                    )
                    msg = msg + "team maintainer done, "
                if ghUser:
                    if not ghrepoteam.has_in_members(ghUser):
                        ghrepoteam.add_membership(
                            member=ghUser,
                            role="member"
                        )
                        msg = msg + "team member done, "
        except Exception as e:
            msg += f'team member err: {e},'
            pass

        try:
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
            msg = msg + "hook done."
        except Exception as e:
            msg += f'hook err: {e},'
            pass

        try:
            if setupCProjectDiscord(coreproject):
                msg += f'discord done'
            else:
                raise Exception(coreproject, "discord error")
        except Exception as e:
            msg += f'discord err'

        cache.set(taskKey, Message.SETUP_APPROVED_PROJECT_DONE,
                  settings.CACHE_LONG)
        sendCoreProjectApprovedNotification(coreproject)
        return True, msg
    except Exception as e:
        errorLog(e)
        return False, e


def setupVProjectDiscord(project: Project) -> str:
    """Setup a Discord channel for the verified project

    Args:
        project (Project): The verified project instance

    Returns:
        str: The discord channel ID
        bool: False if failed to create a channel
    """
    return Discord.createChannel(project.reponame, public=True, category="PROJECTS", message=f"Official discord channel for {project.name} {project.get_abs_link}")


def setupCProjectDiscord(coreproject: CoreProject) -> str:
    """Setup a Discord channel for the core project

    Args:
        project (Project): The core project instance

    Returns:
        str: The discord channel ID
        bool: False if failed to create a channel
    """
    return Discord.createChannel(coreproject.codename, public=False, category="PROJECTS", message=f"Official discord channel for {coreproject.name} {coreproject.get_abs_link}")


def getProjectLiveData(project: Project) -> list:
    """Returns third party platform data of verified/core project instance

    Args:
        project (Project/CoreProject): A verified or core project instance

    Returns:
        list<NamedUser>, list<, list: contributors, languages, commits
    """
    try:
        ghOrgRepo = project.gh_repo()
        contribKey = f"project_livedata_contribs_{project.id}"
        langKey = f"project_livedata_langs_{project.id}"
        commitsKey = f"project_livedata_commits_{project.id}"
        contributors = cache.get(contribKey, None)
        if not contributors:
            contribs = ghOrgRepo.get_contributors()
            ghIDs = []
            for cont in contribs:
                ghIDs.append(str(cont.login))
            contributors = Profile.objects.filter(
                githubID__in=ghIDs).order_by('-xp')
            contributors = list(
                filter(lambda c: not c.is_manager(), list(contributors)))
            cache.set(contribKey, contributors, settings.CACHE_SHORT)
        languages = cache.get(langKey, None)
        if not languages:
            languages = ghOrgRepo.get_languages()
            cache.set(langKey, languages, settings.CACHE_SHORT)
        commits = cache.get(commitsKey, None)
        if not commits:
            commits = ghOrgRepo.get_commits()[:2]
            cache.set(commitsKey, commits, settings.CACHE_MINI)
        commit = None
        for commit in commits:
            if Profile.objects.filter(githubID=commit.author.login).exists():
                commit = dict(
                    sha=commit.sha,
                    url=commit.html_url,
                    profile=Profile.objects.get(githubID=commit.author.login),
                    date=commit.commit.author.date,
                    message=commit.commit.message,
                    files=commit.files,
                )
                break
        return contributors, languages, [commit]
    except:
        return [], [], []


def deleteGhOrgVerifiedRepository(project: Project) -> bool:
    """To delete github repository & team of a verified project, or at least archive it.

    Args:
        project (Project): The verified project instance

    Returns:
        bool: True (it tries, so anyway)
    """
    try:
        ghOrgteam = project.gh_team()
        if ghOrgteam:
            ghOrgteam.delete()
    except Exception as e:
        errorLog(e)
        pass
    try:
        ghOrgRepo = project.gh_repo()
        if ghOrgRepo:
            ghOrgRepo.edit(archive=True)
    except Exception as e:
        errorLog(e)
        pass
    return True


def deleteGhOrgCoreepository(coreproject: CoreProject):
    """To delete github repository & team of a core project, or at least archive it.

    Args:
        coreproject (CoreProject): The core project instance

    Returns:
        bool: True (it tries, so anyway)
    """
    try:
        ghOrgteam = coreproject.gh_team()
        if ghOrgteam:
            ghOrgteam.delete()
    except Exception as e:
        errorLog(e)
        pass
    try:
        ghOrgRepo = coreproject.gh_repo()
        if ghOrgRepo:
            ghOrgRepo.edit(archive=True)
    except Exception as e:
        errorLog(e)
        pass
    return True


def handleGithubKnottersRepoHook(hookrecordID: UUID, ghevent: str, postData: dict, project: BaseProject):
    """Handle github repository hook event for any project

    Args:
        hookrecordID (UUID): The hook record ID
        ghevent (str): The github event
        postData (dict): The post data from github
        project (BaseProject): The base project instance

    Returns:
        bool, str: True, message if handled, False, error message if not handled
    """
    try:
        statusKey = f'gh_event_hook_status_{hookrecordID}'
        status = cache.get(statusKey, Code.NO)
        if status == Code.OK:
            return True, 'Processing or processed'
        cache.set(statusKey, Code.OK, settings.CACHE_LONG)
        hookrecord: HookRecord = HookRecord.objects.get(
            id=hookrecordID, success=False)
        if ghevent == Event.PUSH:
            commits = postData["commits"]
            repository = postData["repository"]
            addTopicToDatabase(repository['language'])
            committers = {}
            un_committers = []
            for commit in commits:
                commit_author_ghID = commit["author"]["username"]
                commit_author_email = commit["author"]["email"]
                if commit_author_ghID not in un_committers:
                    commit_committer = committers.get(commit_author_ghID, None)
                    if not commit_committer:
                        commit_committer: Profile = Profile.objects.filter(Q(Q(githubID=commit_author_ghID) | Q(
                            user__email=commit_author_email)), is_active=True, suspended=False, to_be_zombie=False).first()
                        if not commit_committer:
                            emailaddr: EmailAddress = EmailAddress.objects.filter(
                                email=commit_author_email, verified=True).first()
                            if not emailaddr:
                                un_committers.append(commit_author_ghID)
                                continue
                            else:
                                commit_committer: Profile = emailaddr.user.profile
                            committers[commit_author_ghID] = commit_committer
                        else:
                            committers[commit_author_ghID] = commit_committer
                    added = commit.get("added", [])
                    removed = commit.get("removed", [])
                    modified = commit.get("modified", [])
                    changed = added + removed + modified
                    extensions = {}
                    for change in changed:
                        parts = change.split('.')
                        if len(parts) < 1:
                            continue
                        ext = parts[-1]
                        extdic = extensions.get(ext, {})
                        fileext = extdic.get('fileext', None)
                        if not fileext:
                            if not FileExtension.objects.filter(extension__iexact=ext).exists():
                                fileext: FileExtension = FileExtension.objects.create(
                                    extension__iexact=ext)
                            extensions[ext] = dict(fileext=fileext, topics=[])
                            try:
                                ftops = fileext.getTopics()
                                if not len(ftops):
                                    fileext.topics.set(
                                        ftops | project.topics.all())
                            except:
                                pass
                        for topic in fileext.topics.all():
                            hastopic = False
                            increase = True
                            lastxp = 0
                            tpos = -1
                            if len(extensions[ext]['topics']) > 0:
                                for top in extensions[ext]['topics']:
                                    tpos = tpos + 1
                                    if top['topic'] == topic:
                                        hastopic = True
                                        lastxp = top['xp']
                                        if lastxp > 4:
                                            increase = False
                                        break

                            if increase:
                                by = 1
                                commit_committer.increaseTopicPoints(
                                    topic=topic, by=by, notify=False, reason=f"{commit_author_ghID} committed to {project.name}")
                                if hastopic:
                                    extensions[ext]['topics'][tpos]['xp'] = lastxp+by
                                else:
                                    extensions[ext]['topics'].append(
                                        dict(topic=topic, xp=(lastxp+by)))
            if len(changed) > 1:
                project.creator.increaseXP(
                    by=(((len(commits)//len(committers))//2) or 1), notify=False, reason=f"Commits pushed to {project.name}")
                if project.is_not_free():
                    project.get_moderator().increaseXP(
                        by=(((len(commits)//len(committers))//3) or 1), notify=False, reason=f"Commits pushed to {project.name}")
        elif ghevent == Event.PR:
            pr = postData.get('pull_request', None)
            action = postData.get('action', None)
            pr_creator_ghID = pr['user']['login']
            if action == 'opened':
                pr_creator: Profile = Profile.objects.filter(
                    githubID=pr_creator_ghID, is_active=True, suspended=False, to_be_zombie=False).first()
                if pr_creator:
                    pr_creator.increaseXP(
                        by=2, notify=False, reason=f"PR opened by {pr_creator_ghID} on {project.name}")
            elif action == 'closed':
                pr_creator: Profile = Profile.objects.filter(
                    githubID=pr_creator_ghID, is_active=True, suspended=False, to_be_zombie=False).first()
                if pr['merged']:
                    if pr_creator:
                        pr_creator.increaseXP(
                            by=3, notify=False, reason=f"PR by {pr_creator_ghID} merged on {project.name}")
                    project.creator.increaseXP(
                        by=1, notify=False, reason=f"PR by {pr_creator_ghID} merged on {project.name}")
                    if project.is_not_free():
                        project.get_moderator().increaseXP(
                            by=1, notify=False, reason=f"PR by {pr_creator_ghID} merged on {project.name}")
                else:
                    if pr_creator:
                        pr_creator.decreaseXP(
                            by=2, notify=False, reason=f"PR by {pr_creator_ghID} closed unmerged on {project.name}")
            elif action == 'reopened':
                pr_creator: Profile = Profile.objects.filter(
                    githubID=pr_creator_ghID, is_active=True, suspended=False, to_be_zombie=False).first()
                if pr_creator:
                    pr_creator.increaseXP(
                        by=2, notify=False, reason=f"PR by {pr_creator_ghID} reopened on {project.name}")
            elif action == 'review_requested':
                reviewer_gh_id = pr['requested_reviewer']['login']
                pr_reviewer: Profile = Profile.objects.filter(
                    githubID=reviewer_gh_id, is_active=True, suspended=False, to_be_zombie=False).first()
                if pr_reviewer:
                    pr_reviewer.increaseXP(
                        by=2, notify=False, reason=f"PR by {pr_creator_ghID} requested review by {reviewer_gh_id} on {project.name}")
            elif action == 'review_request_removed':
                reviewer_gh_id = pr['requested_reviewer']['login']
                pr_reviewer: Profile = Profile.objects.filter(
                    githubID=reviewer_gh_id, is_active=True, suspended=False, to_be_zombie=False).first()
                if pr_reviewer:
                    pr_reviewer.decreaseXP(
                        by=2, notify=False, reason=f"PR by {pr_creator_ghID} removed review by {reviewer_gh_id} on {project.name}")
            else:
                return False, f"Unhandled '{ghevent}' action: {action}"
        elif ghevent == Event.PR_REVIEW:
            pr = postData.get('pull_request', None)
            pr_creator_ghID = pr['user']['login']
            review = postData.get('review', None)
            action = postData.get('action', None)
            reviewer_gh_id = review['user']['login']
            # pr['requested_reviewers']
            if action == 'submitted':
                pr_reviewer: Profile = Profile.objects.filter(
                    githubID=reviewer_gh_id, is_active=True, suspended=False, to_be_zombie=False).first()
                if pr_reviewer:
                    for topic in project.topics.all():
                        pr_reviewer.increaseTopicPoints(
                            topic=topic, by=1, notify=False, reason=f"PR by {pr_creator_ghID} reviewed by {reviewer_gh_id} on {project.name}")
            elif action == 'dismissed':
                pr_reviewer: Profile = Profile.objects.filter(
                    githubID=reviewer_gh_id, is_active=True, suspended=False, to_be_zombie=False).first()
                if pr_reviewer:
                    for topic in project.topics.all():
                        pr_reviewer.decreaseTopicPoints(
                            topic=topic, by=1, notify=False, reason=f"PR by {pr_creator_ghID} dismissed review by {reviewer_gh_id} on {project.name}")
            else:
                return False, f"Unhandled '{ghevent}' action: {action}"
        elif ghevent == Event.STAR:
            action = postData.get('action', None)
            if action == 'created':
                project.creator.increaseXP(
                    by=1, notify=False, reason=f"Starred {project.name}")
                if project.is_not_free():
                    project.get_moderator().increaseXP(
                        by=1, notify=False, reason=f"Starred {project.name}")
            elif action == 'deleted':
                project.creator.decreaseXP(
                    by=1, notify=False, reason=f"Unstarred {project.name}")
                if project.is_not_free():
                    project.get_moderator().decreaseXP(
                        by=1, notify=False, reason=f"Unstarred {project.name}")
            else:
                return False, f"Unhandled '{ghevent}' action: {action}"
        else:
            return False, f"Unhandled '{ghevent}'"
        hookrecord.success = True
        hookrecord.save()
        return True, f"hook record ID: {hookrecordID}"
    except ObjectDoesNotExist:
        return False, f"objectdoesnotexist hook record ID: {hookrecordID}"
    except:
        return False, format_exc()


def topicSearchList(query: str, excluding, limit: int, cacheKey: str):
    """
    Returns topics list
    """
    topicslist = cache.get(cacheKey, [])
    if not len(topicslist):
        topics = Topic.objects.exclude(id__in=excluding).filter(
            Q(name__istartswith=query)
            | Q(name__iexact=query)
            | Q(name__icontains=query)
        )[:limit]
        topicslist = list(map(lambda topic: dict(
            id=topic.get_id,
            name=topic.name
        ), topics))
        cache.set(cacheKey, topicslist, settings.CACHE_INSTANT)
    return topicslist

def tagSearchList(query: str, excludeIDs, limit: int, cacheKey: str):
    """
    Returns tags list
    """
    tags = cache.get(cacheKey, [])
    if not len(tags):
        tags = Tag.objects.exclude(id__in=excludeIDs).filter(
            Q(name__istartswith=query)
            | Q(name__iendswith=query)
            | Q(name__iexact=query)
            | Q(name__icontains=query)
        )[:limit]
        cache.set(cacheKey, tags, settings.CACHE_SHORT)

    tagslist = list(map(lambda tag: dict(
        id=tag.getID(),
        name=tag.name
    ), tags[:limit]))
    return tagslist

def transfer_approved_project_moderation(sender:Profile, receiver: Profile):
    """To transfer all approved projects of leaving moderator"""
    newmoderator = receiver
    oldmoderator = sender
    approved_moderations = Moderation.objects.filter(moderator=sender, status=Code.APPROVED, resolved=True) #update
    approved_moderations.update(moderator=newmoderator)
    addMethodToAsyncQueue(f"{APPNAME}.methods.{transfer_approved_repositories.__name__}", newmoderator, oldmoderator, approved_moderations)
    return True


def transfer_approved_repositories(newmoderator, oldmoderator, approved_moderations):
    """
    """
    for moderation in approved_moderations:
        try:
            moderation.project.gh_repo().add_to_collaborators(newmoderator.ghID, permission='maintain')
            moderation.project.gh_repo().remove_from_collaborators(oldmoderator.ghID)
        except Exception as e:
            errorLog(e)
        try:
            moderation.project.gh_team().add_membership(
                member=newmoderator.gh_user(),
                role="maintainer"
            )
            moderation.project.gh_team().remove_membership(
                member=oldmoderator.gh_user()
            )
        except Exception as e:
            errorLog(e)
    return True


def recommendedProjectsList(profile: Profile, excludeUserIDs: list):
    """
    Updates present list of recommended projects for given profile.
    """
    try:
        r = settings.REDIS_CLIENT
        query = Q(topics__in=profile.getTopics())
        authquery = ~Q(creator=profile)

        projects = BaseProject.objects.filter(Q(trashed=False, suspended=False), authquery, query).exclude(creator__user__id__in=excludeUserIDs)
        projects = list(
            set(list(filter(lambda p: p.is_approved(), projects))))
        count = len(projects)
        if count < 1:
            projects = BaseProject.objects.filter(Q(trashed=False, suspended=False), authquery).exclude(
                creator__user__id__in=excludeUserIDs)
            projects = list(
                set(list(filter(lambda p: p.is_approved(), projects))))
        project_ids = [str(project.id) for project in projects]
        if project_ids:
            r.delete(f"{Browse.RECOMMENDED_PROJECTS}_{profile.id}")
            r.rpush(f"{Browse.RECOMMENDED_PROJECTS}_{profile.id}", *project_ids)
    except Exception as e:
        errorLog(e)


def topicProjectsList(profile: Profile, excludeUserIDs: list):
    """
    Updates present list of topic related projects for given profile.
    """
    try:
        r = settings.REDIS_CLIENT
        if profile.totalAllTopics():
            topic = profile.getAllTopics()[0]
        else:
            topic = profile.recommended_topics()[0]
        r.set(f"{Browse.TOPIC_PROJECTS}_{profile.id}_topic", topic)
        projects = BaseProject.objects.filter(trashed=False, suspended=False, topics=topic).exclude(
            creator__user__id__in=excludeUserIDs)
        projects = list(
            set(list(filter(lambda p: p.is_approved(), projects))))
        project_ids = [str(project.id) for project in projects]
        if project_ids:
            r.delete(f"{Browse.TOPIC_PROJECTS}_{profile.id}")
            r.rpush(f"{Browse.TOPIC_PROJECTS}_{profile.id}", *project_ids)
    except Exception as e:
        errorLog(e)


def snapshotsList(profile: Profile, excludeUserIDs: list):
    """
    Updates present list of snapshots for a given profile.
    """
    try:
        r = settings.REDIS_CLIENT
        projIDs = Submission.objects.filter(competition__admirers=profile).exclude(
                            free_project=None).values_list("free_project__id", flat=True)
        snaps = Snapshot.objects.filter(
            Q(
                Q(creator=profile)
                | Q(base_project__creator=profile)
                | Q(base_project__co_creators=profile)
                | Q(base_project__id__in=list(projIDs))
                | Q(creator__admirers=profile)
                | Q(base_project__admirers=profile)
            ),
            base_project__suspended=False, base_project__trashed=False, base_project__is_archived=False, suspended=False
        ).exclude(creator__user__id__in=excludeUserIDs).distinct().order_by("-created_on")
        snap_ids = [str(snap.id) for snap in snaps]
        if snap_ids:
            r.delete(f"{Browse.PROJECT_SNAPSHOTS}_{profile.id}")
            r.rpush(f"{Browse.PROJECT_SNAPSHOTS}_{profile.id}", *snap_ids)
    except Exception as e:
        errorLog(e)