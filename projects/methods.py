from inspect import iscoroutine
from traceback import format_exc
from uuid import UUID
from django.core.exceptions import ObjectDoesNotExist
from django.core.handlers.wsgi import WSGIRequest
from django.db.models.query_utils import Q
from django.core.cache import cache
from django.http.response import HttpResponse
from allauth.account.models import EmailAddress
from management.models import HookRecord
from people.models import Profile, Topic
from github import NamedUser, Repository
from main.bots import GithubKnotters, Discord
from main.strings import Code, Event, url, Message
from main.methods import addMethodToAsyncQueue, errorLog, renderString, renderView
from django.conf import settings
from main.env import SITE
from .models import Category, CoreProject, CoreProjectVerificationRequest, FileExtension, FreeProject, FreeProjectVerificationRequest, License, Project, ProjectHookRecord, ProjectSocial, Tag
from .apps import APPNAME
from .mailers import sendProjectApprovedNotification, sendCoreProjectApprovedNotification


def renderer(request: WSGIRequest, file: str, data: dict = dict()) -> HttpResponse:
    return renderView(request, file, data, fromApp=APPNAME)


def rendererstr(request: WSGIRequest, file: str, data: dict = dict()) -> HttpResponse:
    return HttpResponse(renderString(request, file, data, fromApp=APPNAME))

def renderer_stronly(request: WSGIRequest, file: str, data: dict = dict()) -> str:
    return renderString(request, file, data, fromApp=APPNAME)


def freeProfileData(request, nickname = None, projectID = None):
    """
    Returns profile data for free project.
    """
    try:
        cacheKey = f"{APPNAME}_free_project"
        if nickname:
            cacheKey = f"{cacheKey}_{nickname}"
            project = cache.get(cacheKey, None)
            if not project:
                project = FreeProject.objects.get(nickname=nickname, trashed=False, suspended=False)
                cache.set(cacheKey, project, settings.CACHE_INSTANT)
        else:
            cacheKey = f"{cacheKey}_{projectID}"
            project = cache.get(cacheKey, None)
            if not project:
                project = FreeProject.objects.get(id=projectID, trashed=False, suspended=False)
                cache.set(cacheKey, project, settings.CACHE_INSTANT)

        iscreator = False if not request.user.is_authenticated else project.creator == request.user.profile
        if project.suspended and not iscreator:
            raise ObjectDoesNotExist('suspended',projectID)
        isAdmirer = request.user.is_authenticated and project.isAdmirer(
            request.user.profile)
        iscocreator = False if not request.user.is_authenticated else project.co_creators.filter(user=request.user).exists()
        return dict(
            project=project,
            iscreator=iscreator,
            isAdmirer=isAdmirer,
            iscocreator=iscocreator 
        )
    except ObjectDoesNotExist:
        return False
    except Exception as e:
        errorLog(e)
        return False

def verifiedProfileData(request, reponame = None, projectID = None):
    """
    Returns profile data for verified project.
    """
    try:
        cacheKey = f"{APPNAME}_verified_project"
        if reponame:
            cacheKey = f"{cacheKey}_{reponame}"
            project = cache.get(cacheKey, None)
            if not project:
                project = Project.objects.get(reponame=reponame, trashed=False, status=Code.APPROVED)
                cache.set(cacheKey, project, settings.CACHE_INSTANT)
        else:
            cacheKey = f"{cacheKey}_{projectID}"
            project = cache.get(cacheKey, None)
            if not project:
                project = Project.objects.get(id=projectID, trashed=False, status=Code.APPROVED)
                cache.set(cacheKey, project, settings.CACHE_INSTANT)

        iscreator = False if not request.user.is_authenticated else project.creator == request.user.profile
        ismoderator = False if not request.user.is_authenticated else project.moderator == request.user.profile
        if project.suspended and not (iscreator or ismoderator):
            raise ObjectDoesNotExist('suspended', project)
        isAdmirer = request.user.is_authenticated and project.isAdmirer(request.user.profile)
        iscocreator = False if not request.user.is_authenticated else project.co_creators.filter(user=request.user).exists()
        return dict(
            project=project,
            iscreator=iscreator,
            ismoderator=ismoderator,
            isAdmirer=isAdmirer,
            iscocreator=iscocreator
        )
    except ObjectDoesNotExist:
        return False
    except Exception as e:
        errorLog(e)
        return False

def coreProfileData(request, codename = None, projectID = None):
    """
    Returns profile data for core project.
    """
    try:
        cacheKey = f"{APPNAME}_core_project"
        if codename:
            cacheKey = f"{cacheKey}_{codename}"
            project = cache.get(cacheKey, None)
            if not project:
                project = CoreProject.objects.get(codename=codename, trashed=False, status=Code.APPROVED)
                cache.set(cacheKey, project, settings.CACHE_INSTANT)
        else:
            cacheKey = f"{cacheKey}_{projectID}"
            project = cache.get(cacheKey, None)
            if not project:
                project = CoreProject.objects.get(id=projectID, trashed=False, status=Code.APPROVED)
                cache.set(cacheKey, project, settings.CACHE_INSTANT)

        iscreator = False if not request.user.is_authenticated else project.creator == request.user.profile
        ismoderator = False if not request.user.is_authenticated else project.moderator == request.user.profile
        if project.suspended and not (iscreator or ismoderator):
            raise ObjectDoesNotExist('suspended', project)
        isAdmirer = request.user.is_authenticated and project.isAdmirer(request.user.profile)
        iscocreator = False if not request.user.is_authenticated else project.co_creators.filter(user=request.user).exists()

        return dict(
            project=project,
            iscreator=iscreator,
            ismoderator=ismoderator,
            isAdmirer=isAdmirer,
            iscocreator=iscocreator
        )
    except ObjectDoesNotExist:
        return False
    except Exception as e:
        errorLog(e)
        return False


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
        license = License.objects.get(id=licenseID,public=True)
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

def createProject(name: str, category: str, reponame: str, description: str, creator: Profile, licenseID: UUID, url: str = str(), forConversion = False) -> Project or bool:
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
        reponame = uniqueRepoName(reponame, forConversion)
        if not reponame:
            return False
        license = License.objects.get(id=licenseID,public=True)
        categoryObj = addCategoryToDatabase(category, creator)
        if not categoryObj:
            return False
        return Project.objects.create(
            creator=creator, name=name, reponame=reponame, description=description, category=categoryObj, url=url, license=license)
    except Exception as e:
        errorLog(e)
        return False

def createCoreProject(name: str, category: Category, codename: str, description: str, creator: Profile, license: License,budget:int=0) -> CoreProject or bool:
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
        return CoreProject.objects.create(creator=creator, name=name, codename=codename, description=description, category=category, license=license,budget=budget)
    except Exception as e:
        errorLog(e)
        return False

def createConversionProjectFromFree(freeproject:FreeProject) -> Project:    
    try:
        if Project.objects.filter(reponame=freeproject.nickname,status__in=[Code.MODERATION,Code.APPROVED], trashed=False,suspended=False).exists():
            return False
        return Project.objects.create(
            creator=freeproject.creator,
            name=freeproject.name,
            reponame=freeproject.nickname,
            description=freeproject.description,
            category=freeproject.category,
            license=freeproject.license
        )
    except Exception as e:
        errorLog(e)
        return False

def createConversionProjectFromCore(coreproject:CoreProject, licenseID: UUID) -> Project:    
    try:
        if Project.objects.filter(reponame=coreproject.codename,status__in=[Code.MODERATION,Code.APPROVED], trashed=False,suspended=False).exists():
            return False
        license = License.objects.get(id=licenseID,public=True)
        return Project.objects.create(
            creator=coreproject.creator,
            name=coreproject.name,
            reponame=coreproject.codename,
            description=coreproject.description,
            category=coreproject.category,
            license=license
        )
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


def uniqueRepoName(reponame: str, forConversion = False) -> bool:
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

    if FreeProject.objects.filter(nickname__iexact=str(reponame), trashed=False).exists():
        if not (forConversion and FreeProjectVerificationRequest.objects.filter(freeproject__nickname__iexact=str(reponame), resolved=False).exists()):
            return False
        else:
            return False

    project = CoreProject.objects.filter(
        codename=str(reponame), trashed=False).first()
    if project:
        if project.rejected() and project.canRetryModeration():
            return False
        if project.underModeration():
            return False
        if project.isApproved():
            if not (forConversion and CoreProjectVerificationRequest.objects.filter(coreproject__nickname__iexact=str(reponame), resolved=False).exists()):
                return False
            else:
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
        if task in [Message.SETTING_APPROVED_PROJECT]:
            return True
        cache.set(f'approved_project_setup_{project.id}', Message.SETTING_APPROVED_PROJECT, settings.CACHE_LONG)
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
        if task in [Message.SETTING_APPROVED_PROJECT]:
            return True
        cache.set(f'approved_coreproject_setup_{project.id}', Message.SETTING_APPROVED_PROJECT, settings.CACHE_LONG)
        addMethodToAsyncQueue(f"{APPNAME}.methods.{setupOrgCoreGihtubRepository.__name__}",project,moderator)
        return True
    except Exception as e:
        errorLog(e)
        return False


def setupOrgGihtubRepository(project: Project, moderator: Profile):
    """
    Creates github org repository and setup restrictions & allowances for corresponding project.

    Invites creator to organization & created repository

    :reponame: The name of repository to be created
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
                    ghOrgRepo.create_file('LICENSE','Add LICENSE',str(project.license.content))
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
            done = setupVProjectDiscord(project)
            if done:
                msg += f'discord done {done}'
            else:
                raise Exception()
        except Exception as e:
            msg += f'discord err'

        cache.set(f'approved_project_setup_{project.id}', Message.SETUP_APPROVED_PROJECT_DONE, settings.CACHE_LONG)
        addMethodToAsyncQueue(f"{APPNAME}.mailers.{sendProjectApprovedNotification.__name__}",project)
        return True, msg
    except Exception as e:
        errorLog(e)
        return False, e

def setupOrgCoreGihtubRepository(coreproject: CoreProject, moderator: Profile):
    """
    Creates github org repository and setup restrictions & allowances for corresponding project.

    Invites creator to organization & created repository

    :reponame: The name of repository to be created
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
            ghOrgRepo.create_file('LICENSE','Add LICENSE',str(coreproject.license.content))
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
            done = setupCProjectDiscord(coreproject)
            if done:
                msg += f'discord done {done}'
            else:
                raise Exception()
        except Exception as e:
            msg += f'discord err'

        cache.set(f'approved_coreproject_setup_{coreproject.id}', Message.SETUP_APPROVED_PROJECT_DONE, settings.CACHE_LONG)
        addMethodToAsyncQueue(f"{APPNAME}.mailers.{sendCoreProjectApprovedNotification.__name__}",coreproject)
        return True, msg
    except Exception as e:
        errorLog(e)
        return False, e

def setupVProjectDiscord(project:Project):
    return Discord.createChannel(project.reponame, public=True, category="PROJECTS", message=f"Official discord channel for {project.name} {project.get_abs_link}")

def setupCProjectDiscord(coreproject:CoreProject):
    return Discord.createChannel(coreproject.codename, public=False, category="PROJECTS", message=f"Official discord channel for {coreproject.name} {coreproject.get_abs_link}")

def getGhOrgRepo(reponame: str) -> Repository:
    try:
        return GithubKnotters.get_repo(name=reponame)
    except Exception as e:
        return None

def getGhOrgTeam(teamname: str) -> Repository:
    try:
        return GithubKnotters.get_team_by_slug(teamname)
    except Exception as e:
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


def getProjectLiveData(project):
    try:
        ghOrgRepo = project.gh_repo()
        contributors = cache.get(f"project_livedata_contribs_{project.id}", None)
        if not contributors:
            contribs = ghOrgRepo.get_contributors()
            ghIDs = []
            for cont in contribs:
                ghIDs.append(str(cont.login))
            contributors = Profile.objects.filter(githubID__in=ghIDs).order_by('-xp')
            contributors = list(filter(lambda c: not c.is_manager(), list(contributors)))
            cache.set(f"project_livedata_contribs_{project.id}", contributors, settings.CACHE_SHORT)
        languages = cache.get(f"project_livedata_langs_{project.id}", None)
        if not languages:
            languages = ghOrgRepo.get_languages()
            cache.set(f"project_livedata_langs_{project.id}", languages, settings.CACHE_SHORT)
        commits = cache.get(f"project_livedata_commits_{project.id}", None)
        if not commits:
            commits = ghOrgRepo.get_commits()[:20]
            cache.set(f"project_livedata_commits_{project.id}", commits, settings.CACHE_MINI)
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

def deleteGhOrgVerifiedRepository(project: Project):
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


def handleGithubKnottersRepoHook(hookrecordID, ghevent, postData, project):
    try:
        status = cache.get(f'gh_event_hook_status_{hookrecordID}', Code.NO)
        if status == Code.OK:
            return True, 'Processing or processed'
        cache.set(f'gh_event_hook_status_{hookrecordID}', Code.OK, settings.CACHE_LONG)
        hookrecord = HookRecord.objects.get(id=hookrecordID, success=False)
        if ghevent == Event.PUSH:
            commits = postData["commits"]
            repository = postData["repository"]
            if not Topic.objects.filter(name__iexact=repository['language']).exists():
                Topic.objects.create(name=repository['language'])
            committers = {}
            un_committers = []
            for commit in commits:
                commit_author_ghID = commit["author"]["username"]
                commit_author_email = commit["author"]["email"]
                if commit_author_ghID not in un_committers:
                    commit_committer = committers.get(commit_author_ghID, None)
                    if not commit_committer:
                        commit_committer = Profile.objects.filter(Q(Q(githubID=commit_author_ghID) | Q(
                            user__email=commit_author_email)), is_active=True, suspended=False, to_be_zombie=False).first()
                        if not commit_committer:
                            emailaddr = EmailAddress.objects.filter(
                                email=commit_author_email, verified=True).first()
                            if not emailaddr:
                                un_committers.append(commit_author_ghID)
                                continue
                            else:
                                commit_committer = emailaddr.user.profile
                            committers[commit_author_ghID] = commit_committer
                        else:
                            committers[commit_author_ghID] = commit_committer
                    added = commit.get("added",[])
                    removed = commit.get("removed",[])
                    modified = commit.get("modified",[])
                    changed = added + removed + modified
                    extensions = {}
                    for change in changed:
                        parts = change.split('.')
                        if len(parts) < 1:
                            continue
                        ext = parts[len(parts)-1]
                        extdic = extensions.get(ext, {})
                        fileext = extdic.get('fileext', None)
                        if not fileext:
                            fileext, _ = FileExtension.objects.get_or_create(
                                extension__iexact=ext, defaults=dict(extension=ext))
                            extensions[ext] = dict(fileext=fileext, topics=[])
                            try:
                                ftops = fileext.getTopics()
                                if not len(ftops):
                                    fileext.topics.set(ftops|project.topics.all())
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
                                    topic=topic, by=by, notify = False, reason=f"{commit_author_ghID} committed to {project.name}")
                                if hastopic:
                                    extensions[ext]['topics'][tpos]['xp'] = lastxp+by
                                else:
                                    extensions[ext]['topics'].append(
                                        dict(topic=topic, xp=(lastxp+by)))
            if len(changed) > 1:
                project.creator.increaseXP(
                    by=(((len(commits)//len(committers))//2) or 1),notify = False, reason=f"Commits pushed to {project.name}")
                if project.verified or project.core:
                    project.moderator.increaseXP(
                        by=(((len(commits)//len(committers))//3) or 1),notify = False, reason=f"Commits pushed to {project.name}")
        elif ghevent == Event.PR:
            pr = postData.get('pull_request', None)
            action = postData.get('action', None)
            pr_creator_ghID = pr['user']['login']
            if action == 'opened':
                pr_creator = Profile.objects.filter(
                    githubID=pr_creator_ghID, is_active=True, suspended=False,to_be_zombie=False).first()
                if pr_creator:
                    pr_creator.increaseXP(by=2,notify = False, reason=f"PR opened by {pr_creator_ghID} on {project.name}")
            elif action == 'closed':
                pr_creator = Profile.objects.filter(
                    githubID=pr_creator_ghID, is_active=True, suspended=False,to_be_zombie=False).first()
                if pr['merged']:
                    if pr_creator:
                        pr_creator.increaseXP(by=3,notify = False, reason=f"PR by {pr_creator_ghID} merged on {project.name}")
                    project.creator.increaseXP(by=1,notify = False , reason=f"PR by {pr_creator_ghID} merged on {project.name}")
                    if project.verified or project.core:
                        project.moderator.increaseXP(by=1,notify = False , reason=f"PR by {pr_creator_ghID} merged on {project.name}")
                else:
                    if pr_creator:
                        pr_creator.decreaseXP(by=2, notify = False, reason=f"PR by {pr_creator_ghID} closed unmerged on {project.name}")
            elif action == 'reopened':
                pr_creator = Profile.objects.filter(
                    githubID=pr_creator_ghID, is_active=True ,suspended=False,to_be_zombie=False).first()
                if pr_creator:
                    pr_creator.increaseXP(by=2,notify = False, reason=f"PR by {pr_creator_ghID} reopened on {project.name}")
            elif action == 'review_requested':
                reviewer_gh_id = pr['requested_reviewer']['login']
                pr_reviewer = Profile.objects.filter(
                    githubID=reviewer_gh_id, is_active=True, suspended=False,to_be_zombie=False).first()
                if pr_reviewer:
                    pr_reviewer.increaseXP(by=2, notify=False, reason=f"PR by {pr_creator_ghID} requested review by {reviewer_gh_id} on {project.name}")
            elif action == 'review_request_removed':
                reviewer_gh_id = pr['requested_reviewer']['login']
                pr_reviewer = Profile.objects.filter(
                    githubID=reviewer_gh_id, is_active=True, suspended=False,to_be_zombie=False).first()
                if pr_reviewer:
                    pr_reviewer.decreaseXP(by=2, notify=False, reason=f"PR by {pr_creator_ghID} removed review by {reviewer_gh_id} on {project.name}")
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
                pr_reviewer = Profile.objects.filter(
                    githubID=reviewer_gh_id, is_active=True, suspended=False,to_be_zombie=False).first()
                if pr_reviewer:
                    for topic in project.topics.all():
                        pr_reviewer.increaseTopicPoints(topic=topic, by=1,notify=False, reason=f"PR by {pr_creator_ghID} reviewed by {reviewer_gh_id} on {project.name}")
            elif action == 'dismissed':
                pr_reviewer = Profile.objects.filter(
                    githubID=reviewer_gh_id, is_active=True, suspended=False,to_be_zombie=False).first()
                if pr_reviewer:
                    for topic in project.topics.all():
                        pr_reviewer.decreaseTopicPoints(topic=topic, by=1,notify=False, reason=f"PR by {pr_creator_ghID} dismissed review by {reviewer_gh_id} on {project.name}")
            else:
                return False, f"Unhandled '{ghevent}' action: {action}"
        elif ghevent == Event.STAR:
            action = postData.get('action', None)
            if action == 'created':
                project.creator.increaseXP(by=1,notify = False, reason=f"Starred {project.name}")
                if project.verified or project.core:
                    project.moderator.increaseXP(by=1,notify = False, reason=f"Starred {project.name}")
            elif action == 'deleted':
                project.creator.decreaseXP(by=1, notify = False, reason=f"Unstarred {project.name}")
                if project.verified or project.core:
                    project.moderator.decreaseXP(by=1, notify = False, reason=f"Unstarred {project.name}")
            else:
                return False, f"Unhandled '{ghevent}' action: {action}"
        else:
            return False, f"Unhandled '{ghevent}'"
        hookrecord.success = True
        hookrecord.save()
        return True, f"hook record ID: {hookrecordID}"
    except ObjectDoesNotExist:
        return False, f"objnotexist hook record ID: {hookrecordID}"
    except:
        return False, format_exc()

from .receivers import *
