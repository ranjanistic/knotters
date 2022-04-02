from uuid import uuid4, UUID
from deprecated import deprecated
from django.db import models
from django.utils import timezone
from main.bots import Github, GithubKnotters
from main.env import BOTMAIL
from django.core.cache import cache
from django.conf import settings
from main.methods import addMethodToAsyncQueue, human_readable_size, maxLengthInList, errorLog
from jsonfield import JSONField
from main.strings import CORE_PROJECT, Code, Message, url, PEOPLE, project, MANAGEMENT, DOCS
from moderation.models import Moderation
from management.models import GhMarketApp, HookRecord, ReportCategory, Invitation
from .apps import APPNAME

class Tag(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    name = models.CharField(max_length=1000, null=False,
                            blank=False, unique=True)
    creator = models.ForeignKey(f"{PEOPLE}.Profile", on_delete=models.SET_NULL, null=True,blank=True, related_name="tag_creator")
    def __str__(self):
        return self.name

    @property
    def get_id(self):
        return self.id.hex

    def getID(self):
        return self.get_id

    @property
    def totalTopics(self):
        from people.models import Topic
        return Topic.objects.filter(tags=self).count()

    @property
    def getTopics(self):
        from people.models import Topic
        return Topic.objects.filter(tags=self)

    @property
    def totalProjects(self):
        return BaseProject.objects.filter(tags=self).count()

    @property
    def getProjects(self):
        return BaseProject.objects.filter(tags=self)

    @property
    def totalCategories(self):
        return Category.objects.filter(tags=self).count()

    @property
    def getCategories(self):
        return Category.objects.filter(tags=self)


class Category(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    name = models.CharField(max_length=1000, null=False,
                            blank=False, unique=True)
    creator = models.ForeignKey(f"{PEOPLE}.Profile", on_delete=models.SET_NULL, null=True,blank=True, related_name="category_creator")
    tags = models.ManyToManyField(Tag, through='CategoryTag', default=[])

    def __str__(self):
        return self.name

    @property
    def label_type(self):
        return Code.CATEGORY

    @property
    def get_id(self) -> str:
        return self.id.hex

    @deprecated
    def getID(self) -> str:
        return self.get_id

    @property
    def getLink(self):
        return f"{url.getRoot(MANAGEMENT)}{url.management.label(self.label_type, self.get_id)}"

    @property
    def topicIDs(self):
        topics = self.getProjects().values_list("topics", flat=True).distinct()
        return list(filter(lambda x: x != None,topics))

    @property
    def topics(self):
        from people.models import Topic
        return Topic.objects.filter(id__in=self.topicIDs)

    @property
    def totalTopics(self):
        from people.models import Topic
        return Topic.objects.filter(id__in=self.topicIDs).count()

    @property
    def totalTags(self):
        return self.tags.count()

    @property
    def getTags(self):
        return self.tags.all()

    @property
    def totalProjects(self):
        return BaseProject.objects.filter(category=self).count()

    def getProjects(self):
        return BaseProject.objects.filter(category=self)

    def getProjectsLimited(self, limit=50):
        return BaseProject.objects.filter(category=self)[0:limit]

    @property
    def isDeletable(self):
        return self.totalProjects == 0


class CategoryTag(models.Model):
    class Meta:
        unique_together = ('category', 'tag')

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)


class License(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    name = models.CharField(max_length=50)
    keyword = models.CharField(max_length=80, null=True, blank=True,
                               help_text='The license keyword, refer https://docs.github.com/en/github/creating-cloning-and-archiving-repositories/creating-a-repository-on-github/licensing-a-repository#searching-github-by-license-type')
    description = models.CharField(max_length=1000,null=True, blank=True)
    content = models.CharField(max_length=300000, null=True, blank=True)
    public = models.BooleanField(default=False)
    default = models.BooleanField(default=False)
    creator = models.ForeignKey(f"{PEOPLE}.Profile", on_delete=models.PROTECT)
    createdOn = models.DateTimeField(auto_now=False, default=timezone.now, null=True,blank=True)
    modifiedOn = models.DateTimeField(auto_now=False, default=timezone.now, null=True,blank=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        try:
            if self.content != License.objects.get(id=self.id).content:
                self.modifiedOn = timezone.now()
        except:
            pass
        return super(License, self).save(*args, **kwargs)

    @property
    def get_id(self):
        return self.id.hex

    def getID(self):
        return self.get_id

    def getLink(self, success='', error='', message=''):
        return f'{url.getRoot(APPNAME)}{url.projects.license(id=self.getID())}{url.getMessageQuery(alert=message,error=error,success=success)}'

    @property
    def get_link(self):
        return self.getLink()

    @property
    def is_custom(self):
        return self.creator.getEmail() != BOTMAIL

    def isCustom(self):
        return self.is_custom

    def projects(self):
        cacheKey = f"license_baseprojects_{self.id}"
        projects = cache.get(cacheKey, [])
        if not len(projects):
            projects = BaseProject.objects.filter(license=self)
            if len(projects):
                cache.set(cacheKey, projects, settings.CACHE_INSTANT)
        return projects

    def totalprojects(self):
        return self.projects().count()

def projectImagePath(instance, filename):
    fileparts = filename.split('.')
    return f"{APPNAME}/avatars/{str(instance.getID())}_{str(uuid4().hex)}.{fileparts[len(fileparts)-1]}"

def defaultImagePath():
    return f"{APPNAME}/default.png"

class BaseProject(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    name = models.CharField(max_length=50, null=False, blank=False)
    image = models.ImageField(upload_to=projectImagePath, max_length=500, default=defaultImagePath, null=True, blank=True)
    description = models.CharField(max_length=5000, null=False, blank=False)
    createdOn = models.DateTimeField(auto_now=False, default=timezone.now)
    modifiedOn = models.DateTimeField(auto_now=False, default=timezone.now)
    creator = models.ForeignKey(f"{PEOPLE}.Profile", on_delete=models.PROTECT)
    migrated = models.BooleanField(
        default=False, help_text='Indicates whether this project was created by someone whose account was deleted.')
    migrated_by = models.ForeignKey(f"{PEOPLE}.Profile", on_delete=models.SET_NULL, null=True, blank=True, related_name="baseproject_migrated_by")
    migrated_on = models.DateTimeField(auto_now=False, null=True, blank=True)
    trashed = models.BooleanField(
        default=False, help_text="Deleted for creator, can be used when rejected.")
    license = models.ForeignKey(License, on_delete=models.PROTECT)
    acceptedTerms = models.BooleanField(default=True)
    suspended = models.BooleanField(default=False)
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    tags = models.ManyToManyField(Tag, through='ProjectTag', default=[])
    topics = models.ManyToManyField(
        f'{PEOPLE}.Topic', through='ProjectTopic', default=[])
    co_creators = models.ManyToManyField(f"{PEOPLE}.Profile",through="BaseProjectCoCreator",default=[],related_name='base_project_co_creator')
    admirers = models.ManyToManyField(f"{PEOPLE}.Profile", through='ProjectAdmirer', default=[], related_name='base_project_admirer')
    prime_collaborators = models.ManyToManyField(f"{PEOPLE}.Profile",through='BaseProjectPrimeCollaborator',default=[],related_name='base_project_prime_collaborator')
    
    def __str__(self):
        return self.name

    @property
    def get_id(self) -> str:
        return self.id.hex

    def getID(self) -> str:
        return self.get_id

    def sub_save(self):
        return

    def save(self, *args, **kwargs):
        try:
            previous = BaseProject.objects.get(id=self.id)
            if not (previous.image in [self.image,defaultImagePath()]):
                previous.image.delete(False)
        except:
            pass
        assert self.name is not None
        assert self.creator is not None
        assert self.category is not None
        assert self.license is not None
        assert self.acceptedTerms is True
        self.modifiedOn = timezone.now()
        self.sub_save()
        super(BaseProject, self).save(*args, **kwargs)

    @property
    def get_name(self) -> str:
        return self.name

    @property
    def get_dp(self) -> str:
        return f"{settings.MEDIA_URL}{str(self.image)}"

    @property
    def get_abs_dp(self) -> str:
        if self.get_dp.startswith('http:'):
            return self.get_dp
        return f"{settings.SITE}{self.get_dp}"

    def getDP(self) -> str:
        return self.get_dp
    
    def getTopics(self) -> list:
        return self.topics.all()

    def getPalleteTopics(self) -> list:
        return self.topics.filter()[:2]


    def getTopicsData(self):
        return ProjectTopic.objects.filter(project=self)

    def totalTopics(self):
        return self.topics.count()

    @property
    def getTags(self):
        return self.tags.all()

    def getPalleteTags(self) -> list:
        return self.tags.filter()[:2]

    def totalTags(self):
        return self.tags.count()
    
    def theme(self):
        if self.is_verified:
            return 'accent'
        if self.is_core:
            return 'vibrant'
        return "positive"

    def text_theme(self):
        if self.is_verified:
            return 'text-accent'
        if self.is_core:
            return "text-vibrant"
        return "text-positive"

    @property
    def is_normal(self):
        return not (self.suspended or self.trashed or not self.is_approved)

    @property
    def socialsites(self):
        cacheKey = f"baseproject_socialsites_{self.id}"
        sites = cache.get(cacheKey, [])
        if not len(sites):
            sites = ProjectSocial.objects.filter(project=self)
            if len(sites):
                cache.set(cacheKey, sites, settings.CACHE_INSTANT)
        return sites

    def addSocial(self, site:str):
        return ProjectSocial.objects.create(project=self,site=site)

    def removeSocial(self, id:UUID):
        return ProjectSocial.objects.filter(id=id,project=self).delete()
    
    @property
    def is_free(self):
        cacheKey = f"baseproject_is_free_{self.id}"
        isFree = cache.get(cacheKey, None)
        if isFree is None:
            isFree = FreeProject.objects.filter(id=self.id).exists()
            cache.set(cacheKey, isFree, settings.CACHE_LONG)
        return isFree

    @property
    def is_not_free(self):
        return not self.is_free

    @property
    def is_verified(self):
        cacheKey = f"baseproject_is_verified_{self.id}"
        isVerified = cache.get(cacheKey, None)
        if isVerified is None:
            isVerified = Project.objects.filter(id=self.id).exists()
            cache.set(cacheKey, isVerified, settings.CACHE_LONG)
        return isVerified

    @property
    def is_core(self):
        cacheKey = f"baseproject_is_core_{self.id}"
        isCore = cache.get(cacheKey, None)
        if isCore is None:
            isCore = CoreProject.objects.filter(id=self.id).exists()
            cache.set(cacheKey, isCore, settings.CACHE_LONG)
        return isCore

    @property
    def is_approved(self):
        cacheKey = f"baseproject_is_approved_{self.id}"
        isApproved = cache.get(cacheKey, None)
        if isApproved is None:
            isApproved = self.is_free or Project.objects.filter(id=self.id,status=Code.APPROVED).exists() or CoreProject.objects.filter(id=self.id,status=Code.APPROVED).exists()
            if isApproved:
                cache.set(cacheKey, isApproved, settings.CACHE_LONG)
        return isApproved

    @property
    def is_pending(self):
        cacheKey = f"baseproject_is_pending_{self.id}"
        isPending = cache.get(cacheKey, None)
        if isPending is None:
            isPending = Project.objects.filter(id=self.id,status=Code.MODERATION).exists() or CoreProject.objects.filter(id=self.id,status=Code.MODERATION).exists()
            if not isPending:
                cache.set(cacheKey, isPending, settings.CACHE_LONG)
        return isPending

    @property
    def is_rejected(self):
        cacheKey = f"baseproject_is_rejected_{self.id}"
        isRejected = cache.get(cacheKey, None)
        if isRejected is None:
            isRejected = Project.objects.filter(id=self.id,status=Code.REJECTED).exists() or CoreProject.objects.filter(id=self.id,status=Code.REJECTED).exists()
            if isRejected:
                cache.set(cacheKey, isRejected, settings.CACHE_LONG)
        return isRejected 

    def getProject(self,onlyApproved=False):
        cacheKey = f'{self.id}_subproject_appr_{onlyApproved}'
        project = cache.get(cacheKey, None)
        if project:
            return project
        try:
            project = FreeProject.objects.get(id=self.id)
            cache.set(cacheKey, project, settings.CACHE_SHORT)
        except:
            try:
                project = Project.objects.get(id=self.id)
                if onlyApproved and not project.isApproved():
                    return None
                cache.set(cacheKey, project, settings.CACHE_SHORT)
            except:
                project = CoreProject.objects.get(id=self.id)
                if onlyApproved and not project.isApproved():
                    return None
                cache.set(cacheKey, project, settings.CACHE_SHORT)
        return project

    @property
    def get_link(self) -> str:
        return self.getLink()

    @property
    def get_abs_link(self) -> str:
        if self.get_link.startswith('http:'):
            return self.get_link
        return f"{settings.SITE}{self.get_link}"
  
    def getLink(self, success: str = '', error: str = '', alert: str = '') -> str:
        return self.getProject().getLink(success, error, alert)
        
  
    @property
    def get_nickname(self):
        project = self.getProject()
        if project.verified:
            return project.reponame
        if project.core:
            return project.codename
        return project.nickname

    @property
    def total_admiration(self):
        cacheKey = f'{self.id}_total_admiration'
        count = cache.get(cacheKey, None)
        if not count:
            count = self.admirers.count()
            if count:
                cache.set(cacheKey, count, settings.CACHE_INSTANT)
        return count

    def total_admirers(self):
        return self.total_admiration

    def get_moderator(self):
        if self.is_free:
            return None
        return self.getProject(True).moderator

    def isAdmirer(self, profile):
        return self.admirers.filter(id=profile.id).exists()

    def under_invitation(self):
        """
        Under ownership invitation
        """
        return ProjectTransferInvitation.objects.filter(baseproject=self, resolved=False).exists()

    def can_invite_owner(self):
        return self.is_approved and not self.under_invitation() and not (self.is_not_free and (self.getProject().under_mod_invitation() or self.getProject().under_del_request()))

    def can_invite_profile(self, profile):
        """
        For ownership, primarily, but can be used for other invitations as well
        """
        return profile.is_normal and self.getProject().can_invite_profile(profile)

    def can_invite_owner_profile(self, profile):
        return self.can_invite_owner() and self.can_invite_profile(profile)

    def current_invitation(self):
        try:
            return ProjectTransferInvitation.objects.get(baseproject=self, resolved=False)
        except:
            return None

    def cancel_invitation(self):
        return ProjectTransferInvitation.objects.filter(baseproject=self).delete()
    
    def transfer_to(self,newcreator):
        if self.suspended or self.trashed:
            return False
        if self.is_free:
            FreeRepository.objects.filter(free_project=self.getProject()).delete()
        oldcreator = self.creator
        self.migrated_by = self.creator
        self.creator = newcreator
        self.migrated = True
        self.migrated_on = timezone.now()
        self.save()
        try:
            if self.is_not_free and self.is_approved:
                getproject = self.getProject()
                try:
                    nghid = newcreator.ghID
                    if nghid:
                        getproject.gh_repo().add_to_collaborators(nghid,permission='push')
                    oghid = oldcreator.ghID
                    if oghid:
                        getproject.gh_repo().remove_from_collaborators(oghid)
                except:
                    pass
                try:
                    nghuser = newcreator.gh_user()
                    if nghuser:
                        getproject.gh_team().add_membership(
                            member=nghuser,
                            role="maintainer"
                        )
                    oghuser = oldcreator.gh_user()
                    if oghuser:
                        getproject.gh_team().remove_membership(
                            member=oghuser
                        )
                except:
                    pass
        except:
            pass
        return True
    
    def max_allowed_assets(self):
        if self.is_free:
            return 5
        else: return 10

    def assets(self):
        return Asset.objects.filter(baseproject=self)

    def total_assets(self):
        return Asset.objects.filter(baseproject=self).count()

    def can_add_assets(self):
        return self.is_normal and self.total_assets() <= self.max_allowed_assets()

    def remaining_assets_limit(self):
        return self.max_allowed_assets() - self.total_assets()

    def public_assets(self):
        return Asset.objects.filter(baseproject=self,public=True)

    def total_public_assets(self):
        return Asset.objects.filter(baseproject=self,public=True).count()

    def private_assets(self):
        return Asset.objects.filter(baseproject=self,public=False)

    def total_private_assets(self):
        return Asset.objects.filter(baseproject=self,public=False).count()
    
    def add_cocreator(self,co_creator):
        if co_creator.is_normal:
            self.co_creators.add(co_creator)
            try:
                if self.is_not_free and self.is_approved:
                    getproject = self.getProject()
                    try:
                        nghuser = co_creator.gh_user()
                        if nghuser:
                            getproject.gh_team().add_membership(
                                member=nghuser,
                                role="member"
                            )
                    except:
                        pass
            except:
                pass
            return True
        else :
            return False
            
    def remove_cocreator(self,co_creator):
        if self.co_creators.filter(id=co_creator.id).exists():
            self.co_creators.remove(co_creator)
            try:
                if self.is_not_free and self.is_approved:
                    getproject = self.getProject()
                    try:
                        nghuser = co_creator.gh_user()
                        if nghuser:
                            getproject.gh_team().remove_membership(
                                member=nghuser,
                            )
                    except:
                        pass
            except:
                pass
            return True
        else:
            return False

    def total_cocreators(self):
        return self.co_creators.count()
    
    def under_cocreator_invitation(self):
        return BaseProjectCoCreatorInvitation.objects.filter(base_project=self, resolved=False).exists()

    def total_cocreator_invitations(self):
        return BaseProjectCoCreatorInvitation.objects.filter(base_project=self, resolved=False).count()
    
    def under_cocreator_invitation_profile(self,profile):
        return BaseProjectCoCreatorInvitation.objects.filter(base_project=self, resolved=False,receiver=profile).exists()

    def can_invite_cocreator(self):
        return self.is_approved and not self.under_invitation() and not (self.is_not_free and self.getProject().under_del_request()) and ((self.total_cocreator_invitations() +  self.total_cocreators())<=10)

    def has_cocreators(self):
        return self.co_creators.filter().exists()

    def can_invite_cocreator_profile(self, profile):
        return profile.is_normal and not self.co_creators.filter(user=profile.user).exists() and self.getProject().can_invite_cocreator_profile(profile) and not self.under_cocreator_invitation_profile(profile)

    def current_cocreator_invitations(self):
        return BaseProjectCoCreatorInvitation.objects.filter(base_project=self,resolved=False)

    def cancel_cocreator_invitation(self,profile):
        return BaseProjectCoCreatorInvitation.objects.filter(base_project=self,resolved=False,receiver=profile).delete()
    
    def cancel_all_cocreator_invitations(self):
        return BaseProjectCoCreatorInvitation.objects.filter(base_project=self,resolved=False).delete()

        


class BaseProjectPrimeCollaborator(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    prime_collaborator = models.ForeignKey(f"{PEOPLE}.Profile", on_delete=models.CASCADE,related_name="base_project_prime_collaborator_prime_collaborator")
    base_project = models.ForeignKey(BaseProject, on_delete=models.CASCADE,related_name="base_project_prime_collaborator_base_project")

class BaseProjectCoCreator(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    co_creator = models.ForeignKey(f"{PEOPLE}.Profile",on_delete=models.CASCADE,related_name="base_project_co_creator_co_creator")
    base_project = models.ForeignKey(BaseProject, on_delete=models.CASCADE,related_name="base_project_co_creator_base_project")

class BaseProjectCoCreatorInvitation(Invitation):
    base_project = models.ForeignKey(BaseProject, on_delete=models.CASCADE,related_name="base_project_co_creator_invitation_base_project")
    sender = models.ForeignKey(f'{PEOPLE}.Profile', on_delete=models.CASCADE, related_name='base_project_co_creator_invitation_sender')
    receiver = models.ForeignKey(f'{PEOPLE}.Profile', on_delete=models.CASCADE, related_name='base_project_co_creator_invitation_receiver')

    def accept(self):
        if self.expired: return False
        if self.resolved: return False
        done = self.base_project.add_cocreator(self.receiver)
        if not done:
            return False
        self.resolve()
        return done

    def decline(self):
        if self.expired:
            return False
        if self.resolved:
            return False
        self.delete()
        return True
    
    def getLink(self, success: str = '', error: str = '', alert: str = '') -> str:
        return f"{url.getRoot(APPNAME)}{url.projects.baseCocreatorInvite(self.get_id)}{url.getMessageQuery(alert,error,success)}"
    
    @property
    def get_link(self):
        return self.getLink()
    
    @property
    #@property --> Gets initialised when class object is created.
    def get_act_link(self):
        return f"{url.getRoot(APPNAME)}{url.projects.baseCocreatorInviteAct(self.get_id)}"

       
class BaseProjectPrimeCollaboratorInvitation(Invitation):
    base_project = models.ForeignKey(BaseProject, on_delete=models.CASCADE,related_name="base_project_prime_collaborator_invitation_base_project")
    sender = models.ForeignKey(f'{PEOPLE}.Profile', on_delete=models.CASCADE, related_name='base_project_prime_collaborator_invitation_sender')
    receiver = models.ForeignKey(f'{PEOPLE}.Profile', on_delete=models.CASCADE, related_name='base_project_prime_collaborator_invitation_receiver')

class Project(BaseProject):
    """
    This is verified project
    """
    url = models.CharField(max_length=500, null=True, blank=True)
    reponame = models.CharField(
        max_length=500, unique=True, null=False, blank=False)
    repo_id = models.IntegerField(default=0, null=True, blank=True)
    status = models.CharField(choices=project.PROJECTSTATESCHOICES, max_length=maxLengthInList(
        project.PROJECTSTATES), default=Code.MODERATION)
    approvedOn = models.DateTimeField(auto_now=False, blank=True, null=True)

    mentor = models.ForeignKey(f"{PEOPLE}.Profile", on_delete=models.SET_NULL, related_name='verified_project_mentor',null=True, blank=True)

    verified = True
    core = False

    def sub_save(self):
        assert len(self.reponame) > 0
        
    def getLink(self, success: str = '', error: str = '', alert: str = '') -> str:
        try:
            if self.status != Code.APPROVED:
                return self.moderation.getLink(alert=alert, error=error,success=success)
            return f"{url.getRoot(APPNAME)}{url.projects.profile(reponame=self.reponame)}{url.getMessageQuery(alert,error,success)}"
        except Exception as e:
            errorLog(e)
            return f"{url.getRoot(APPNAME)}{url.getMessageQuery(alert,error,success)}"

    def isApproved(self) -> bool:
        return self.status == Code.APPROVED

    def isLive(self) -> bool:
        return self.isApproved()

    def rejected(self) -> bool:
        return self.status == Code.REJECTED

    def underModeration(self) -> bool:
        return self.status == Code.MODERATION

    def gh_repo(self):
        try:
            if self.repo_id:
                repo = cache.get(f"gh_repo_data_{self.repo_id}", None)
                if not repo:
                    repo = GithubKnotters.get_repo(self.reponame)
                    cache.set(f"gh_repo_data_{self.repo_id}", repo, settings.CACHE_LONG)
                return repo
            else:
                repo = GithubKnotters.get_repo(self.reponame)
                self.repo_id = repo.id
                self.save()
                cache.set(f"gh_repo_data_{self.repo_id}", repo, settings.CACHE_LONG)
                return repo
        except Exception as e:
            if not GithubKnotters:
                return None
            errorLog(e)
            return None

    def gh_repo_link(self) -> str:
        repo = self.gh_repo()
        if not repo:
            return self.getLink(alert=Message.GH_REPO_NOT_SETUP)
        return repo.html_url

    def getRepoLink(self) -> str:
        return self.gh_repo_link()

    @property
    def gh_team_name(self):
        return f'team-{self.reponame}'

    def gh_team(self):
        try:
            if not self.isApproved(): return None
            cachekey = f"gh_team_data_{self.reponame}"
            team = cache.get(cachekey, None)
            if not team:
                team = GithubKnotters.get_team_by_slug(self.gh_team_name)
                cache.set(cachekey, team, settings.CACHE_LONG)
            return team
        except Exception as e:
            return None

    def base(self):
        cacheKey = f"baseproject_of_project_{self.id}"
        projectbase = cache.get(cacheKey, None)
        if projectbase is None:
            projectbase = BaseProject.objects.get(id=self.id)
            cache.set(cacheKey, projectbase, settings.CACHE_LONG)
        return projectbase

    @property
    def nickname(self):
        return self.reponame

    @property
    def moderation(self) -> Moderation:
        return Moderation.objects.filter(project=self, type=APPNAME).order_by('-requestOn','-respondOn').first()

    @property
    def moderator(self):
        mod = self.moderation
        return None if not mod else mod.moderator

    def getModerator(self) -> models.Model:
        if not self.isApproved():
            return None
        mod = self.moderation
        return None if not mod else mod.moderator

    def getModLink(self) -> str:
        try:
            return self.moderation.getLink()
        except:
            return str()

    def moderationRetriesLeft(self) -> int:
        maxtries = 0
        if self.status != Code.APPROVED:
            maxtries = 1 - Moderation.objects.filter(type=APPNAME, project=self, resolved=True).count()
        return maxtries

    def canRetryModeration(self) -> bool:
        return self.status != Code.APPROVED and self.moderationRetriesLeft() > 0 and not self.trashed and not self.suspended

    def getTrashLink(self) -> str:
        return url.projects.trash(self.getID())

    def editProfileLink(self):
        return f"{url.getRoot(APPNAME)}{url.projects.profileEdit(projectID=self.getID(),section=project.PALLETE)}"


    def under_mod_invitation(self):
        return ProjectModerationTransferInvitation.objects.filter(project=self, resolved=False).exists()

    def can_invite_mod(self):
        return self.status == Code.APPROVED and not self.trashed and not self.suspended and not self.under_mod_invitation() and not self.under_del_request()

    def can_invite_profile(self, profile):
        return (profile not in [self.creator, self.moderator, self.mentor]) and not (
            self.moderator.isBlockedProfile(profile) or self.creator.isBlockedProfile(profile) or (self.mentor and self.mentor.isBlockedProfile(profile))
        )

    def can_invite_mod_profile(self, profile):
        return self.can_invite_mod() and self.can_invite_profile(profile)

    def current_mod_invitation(self):
        try:
            return ProjectModerationTransferInvitation.objects.get(project=self, resolved=False)
        except:
            return None

    def cancel_moderation_invitation(self):
        return ProjectModerationTransferInvitation.objects.filter(project=self).delete()

    def transfer_moderation_to(self,newmoderator):
        if not (self.isApproved() or self.trashed or self.suspended):
            return False
        elif ProjectModerationTransferInvitation.objects.filter(project=self, sender=self.moderator, receiver=newmoderator, resolved=True).exists():
            mod = self.moderation
            if not mod:
                return False
            oldmoderator = mod.moderator
            mod.moderator = newmoderator
            mod.save()
            cache.delete(f"project_moderation_{self.get_id}")
            try:
                self.gh_repo().add_to_collaborators(newmoderator.ghID,permission='maintain')
                self.gh_repo().remove_from_collaborators(oldmoderator.ghID)
            except:
                pass
            try:
                self.gh_team().add_membership(
                    member=newmoderator.gh_user(),
                    role="maintainer"
                )
                self.gh_team().remove_membership(
                    member=oldmoderator.gh_user()
                )
            except:
                pass
            return True
        return False


    def under_del_request(self):
        return VerProjectDeletionRequest.objects.filter(project=self, sender=self.creator, receiver=self.moderator, resolved=False).exists()

    def cancel_del_request(self):
        return VerProjectDeletionRequest.objects.filter(project=self).delete()

    def current_del_request(self):
        try:
            return VerProjectDeletionRequest.objects.get(project=self, resolved=False)
        except:
            return None

    def can_request_deletion(self):
        return not (self.trashed or self.suspended or self.status != Code.APPROVED or self.under_invitation() or self.under_mod_invitation() or self.under_del_request())

    def request_deletion(self):
        if not self.can_request_deletion():
            return False
        return VerProjectDeletionRequest.objects.create(project=self, sender=self.creator, receiver=self.moderator)
    
    def moveToTrash(self) -> bool:
        if not self.isApproved():
            self.trashed = True
            self.creator.decreaseXP(by=2)
            self.save()
            if self.moderation and self.moderation.isPending():
                self.moderation.delete()
                self.delete()
        elif VerProjectDeletionRequest.objects.filter(project=self, sender=self.creator, receiver=self.moderator, resolved=True).exists():
            self.trashed = True
            self.creator.decreaseXP(by=2)
            self.save()
        return self.trashed

    def is_from_verification(self):
        return FreeProjectVerificationRequest.objects.filter(verifiedproject=self).exists() or CoreProjectVerificationRequest.objects.filter(verifiedproject=self).exists()
    
    def from_verification(self):
        return FreeProjectVerificationRequest.objects.filter(verifiedproject=self).first() or CoreProjectVerificationRequest.objects.filter(verifiedproject=self).first() or None
    
    def can_invite_cocreator_profile(self,profile):
        return self.can_invite_profile(profile)
        

def assetFilePath(instance, filename):
    fileparts = filename.split('.')
    return f"{APPNAME}/assets/{str(instance.baseproject.get_id)}-{str(instance.get_id)}_{uuid4().hex}.{fileparts[-1]}"

class Asset(models.Model):
    """
    A project's asset (file) model.
    """
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    baseproject = models.ForeignKey(BaseProject,on_delete=models.CASCADE)
    name = models.CharField(max_length=250, null=False, blank=False)
    file = models.FileField(upload_to=assetFilePath,max_length=500)
    public = models.BooleanField(default=False)
    created_on = models.DateTimeField(auto_now=False, default=timezone.now)
    modified_on = models.DateTimeField(auto_now=False)
    creator = models.ForeignKey(f"{PEOPLE}.Profile", on_delete=models.CASCADE, related_name="asset_creator")

    @property
    def get_id(self):
        return self.id.hex
    
    def save(self, *args, **kwargs):
        self.modified_on = timezone.now()
        super(Asset, self).save(*args, **kwargs)

    def move_to_project(self, baseproject:BaseProject) -> bool:
        """
        Moves the asset to a new project, if possible
        """
        if not baseproject.can_add_assets():
            return False
        self.baseproject = baseproject
        self.save()
        return True

    @property
    def get_link(self):
        return f"{settings.MEDIA_URL}{self.file.name}"

    @property
    def type(self):
        return self.file.name.split('.')[-1]

    @property
    def size(self):
        return self.file.size

    @property
    def display_size(self):
        return human_readable_size(self.file.size)


class FreeProject(BaseProject):
    """
    A quick project model
    """
    nickname = models.CharField(max_length=500, unique=True, null=False, blank=False)
    verified = False
    core = False

    def getLink(self, success: str = '', error: str = '', alert: str = '') -> str:
        return f"{url.getRoot(APPNAME)}{url.projects.profileFree(nickname=self.nickname)}{url.getMessageQuery(alert,error,success)}"

    def moveToTrash(self) -> bool:
        if not self.can_delete():
            return False
        self.creator.decreaseXP(by=2)
        self.delete()
        return True

    @property
    def has_linked_repo(self) -> bool:
        cacheKey = f"freeproject_freerepo_exists_{self.id}"
        freerepo = cache.get(cacheKey, None)
        if freerepo is None:
            freerepo = FreeRepository.objects.filter(free_project=self).exists()
            cache.set(cacheKey, freerepo, settings.CACHE_INSTANT)
        return freerepo

    @property
    def linked_repo(self):
        try:
            cacheKey = f"freeproject_freerepo_{self.id}"
            freerepo = cache.get(cacheKey, None)
            if freerepo is None:
                freerepo = FreeRepository.objects.get(free_project=self)
                cache.set(cacheKey, freerepo, settings.CACHE_INSTANT)
            return freerepo
        except:
            return None

    def editProfileLink(self):
        return f"{url.getRoot(APPNAME)}{url.projects.profileEdit(projectID=self.getID(),section=project.PALLETE)}"

    def base(self):
        cacheKey = f"baseproject_of_freeproject_{self.id}"
        projectbase = cache.get(cacheKey, None)
        if projectbase is None:
            projectbase = BaseProject.objects.get(id=self.id)
            cache.set(cacheKey, projectbase, settings.CACHE_LONG)
        return projectbase

    def can_invite_profile(self, profile):
        return profile not in [self.creator] and not (self.creator.isBlockedProfile(profile))

    def can_delete(self):
        return not (self.trashed or self.suspended or self.under_invitation() or self.under_verification_request())

    def under_verification_request(self):
        return FreeProjectVerificationRequest.objects.filter(freeproject=self, resolved=False).exists()

    def cancel_verification_request(self):
        req = self.current_verification_request()
        if req:
            if not req.verifiedproject.isApproved():
                req.verifiedproject.delete()
                return True
        return False

    def current_verification_request(self):
        try:
            return FreeProjectVerificationRequest.objects.get(freeproject=self, resolved=False)
        except:
            return None

    def can_request_verification(self):
        return not (self.trashed or self.suspended or self.under_invitation() or self.under_verification_request())

    def request_verification(self):
        if not self.can_request_verification():
            return False
        return FreeProjectVerificationRequest.objects.create(freeproject=self)
    
    def moveToVerified(self) -> bool:
        try:
            fpvr = FreeProjectVerificationRequest.objects.get(freeproject=self, resolved=True)
            if not fpvr.verifiedproject.isApproved():
                return False
            Snapshot.objects.filter(base_project=self.base()).update(base_project=fpvr.verifiedproject.base())
            ProjectSocial.objects.filter(project=self.base()).update(project=fpvr.verifiedproject.base())
            fpvr.verifiedproject.admirers.set(self.admirers.all())
            fpvr.verifiedproject.co_creators.set(self.co_creators.all())
            fpvr.verifiedproject.prime_collaborators.set(self.prime_collaborators.all())
            self.delete()
            return True
        except:
            return False

    def can_invite_cocreator_profile(self,profile):
        return self.can_invite_profile(profile)


class FreeRepository(models.Model):
    """
    One to one linked repository record for Quick (Free) projects
    """
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    free_project = models.OneToOneField(FreeProject, on_delete=models.CASCADE)
    repo_id = models.IntegerField()

    def gh_repo(self):
        try:
            data = cache.get(f"gh_repo_data_{self.repo_id}")
            if not data:
                api = self.free_project.creator.gh_api()
                if not api:
                    api = Github
                data = api.get_repo(int(self.repo_id))
                if data:
                    cache.set(f"gh_repo_data_{self.repo_id}", data, settings.CACHE_LONG)
            return data
        except Exception as e:
            return None

    @property
    def reponame(self):
        data = self.gh_repo()
        if data:
            return data.name
        return None

    @property
    def repolink(self):
        data = self.gh_repo()
        if data:
            return data.html_url
        return None

    def has_installed_app(self):
        return AppRepository.objects.filter(free_repo=self).exists()

    def installed_app(self):
        return AppRepository.objects.filter(free_repo=self).first()

    def is_submission(self):
        from compete.models import Submission
        return Submission.objects.filter(free_project=self).exists()

    def submission(self):
        from compete.models import Submission
        return Submission.objects.filter(free_project=self).first()



class AppRepository(models.Model):
    """
    Ghmarket app linked with FreeRepository
    """
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    free_repo = models.ForeignKey(FreeRepository, on_delete=models.CASCADE)
    gh_app = models.ForeignKey(GhMarketApp, on_delete=models.CASCADE)
    suspended = models.BooleanField(default=False)
    permissions = JSONField(default=dict)

    def __str__(self):
        return f"{self.gh_app} on {self.free_repo.reponame}"

    @property
    def get_id(self):
        return self.id.hex


class ProjectTag(models.Model):
    class Meta:
        unique_together = ('project', 'tag')

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    project = models.ForeignKey(
        BaseProject, on_delete=models.CASCADE, null=True, blank=True)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE,
                            related_name='project_tag')


class ProjectTopic(models.Model):
    class Meta:
        unique_together = ('project', 'topic')

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    project = models.ForeignKey(
        BaseProject, on_delete=models.CASCADE, null=True, blank=True)
    topic = models.ForeignKey(f'{PEOPLE}.Topic', on_delete=models.CASCADE,
                              null=True, blank=True, related_name='project_topic')

class ProjectSocial(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    project = models.ForeignKey(BaseProject, on_delete=models.CASCADE)
    site = models.URLField(max_length=800)


class CoreProject(BaseProject):
    """
    A core project's model
    """
    codename = models.CharField(max_length=500, unique=True, null=False, blank=False)
    repo_id = models.IntegerField(default=0, null=True, blank=True)
    budget = models.FloatField(default=0)
    mentor = models.ForeignKey(f"{PEOPLE}.Profile", on_delete=models.SET_NULL, related_name='core_project_mentor',null=True, blank=True)
    status = models.CharField(choices=project.PROJECTSTATESCHOICES, max_length=maxLengthInList(
        project.PROJECTSTATES), default=Code.MODERATION)
    approvedOn = models.DateTimeField(auto_now=False, blank=True, null=True)
    verified = False
    core = True
    

    def getLink(self, success: str = '', error: str = '', alert: str = '') -> str:
        return f"{url.getRoot(APPNAME)}{url.projects.profileCore(codename=self.codename)}{url.getMessageQuery(alert,error,success)}"

    def editProfileLink(self):
        return f"{url.getRoot(APPNAME)}{url.projects.profileEdit(projectID=self.getID(),section=project.PALLETE)}"
    
    def getLink(self, success: str = '', error: str = '', alert: str = '') -> str:
        try:
            if self.status != Code.APPROVED:
                return (Moderation.objects.filter(coreproject=self, type=CORE_PROJECT, status__in=[Code.REJECTED, Code.MODERATION]).order_by('-requestOn','-respondOn').first()).getLink(alert=alert, error=error,success=success)
            return f"{url.getRoot(APPNAME)}{url.projects.profileCore(codename=self.codename)}{url.getMessageQuery(alert,error,success)}"
        except:
            return f"{url.getRoot(APPNAME)}{url.getMessageQuery(alert,error,success)}"

    def isApproved(self) -> bool:
        return self.status == Code.APPROVED

    def isLive(self) -> bool:
        return self.isApproved()

    def rejected(self) -> bool:
        return self.status == Code.REJECTED

    def underModeration(self) -> bool:
        return self.status == Code.MODERATION

    
    def gh_repo(self):
        try:
            if self.repo_id:
                repo = cache.get(f"gh_repo_data_{self.repo_id}", None)
                if not repo:
                    repo = GithubKnotters.get_repo(self.codename)
                    cache.set(f"gh_repo_data_{self.repo_id}", repo, settings.CACHE_LONG)
                return repo
            else:
                repo = GithubKnotters.get_repo(self.codename)
                self.repo_id = repo.id
                self.save()
                cache.set(f"gh_repo_data_{self.repo_id}", repo, settings.CACHE_LONG)
                return repo
        except Exception as e:
            if not GithubKnotters:
                return None
            errorLog(e)
            return None

    def gh_repo_link(self) -> str:
        repo = self.gh_repo()
        if not repo:
            return self.getLink(alert=Message.GH_REPO_NOT_SETUP)
        return repo.html_url

    def getRepoLink(self) -> str:
        return self.gh_repo_link()
    
    @property
    def gh_team_name(self):
        return f'team-{self.codename}'

    def gh_team(self):
        try:
            if not self.isApproved(): return None
            cachekey = f"gh_team_data_{self.codename}"
            team = cache.get(cachekey, None)
            if not team:
                team = GithubKnotters.get_team_by_slug(self.gh_team_name)
                cache.set(cachekey, team, settings.CACHE_LONG)
            return team
        except Exception as e:
            return None

    @property
    def nickname(self):
        return self.codename

    def base(self):
        cacheKey = f"baseproject_of_coreproject_{self.id}"
        projectbase = cache.get(cacheKey, None)
        if projectbase is None:
            projectbase = BaseProject.objects.get(id=self.id)
            cache.set(cacheKey, projectbase, settings.CACHE_LONG)
        return projectbase

    @property
    def moderation(self) -> Moderation:
        return Moderation.objects.filter(coreproject=self, type=CORE_PROJECT).order_by('-requestOn','-respondOn').first()
                                        
    @property
    def moderator(self):
        mod = self.moderation
        return None if not mod else mod.moderator

    def getModerator(self) -> models.Model:
        if not self.isApproved():
            return None
        mod = self.moderation
        return None if not mod else mod.moderator

    def getModLink(self) -> str:
        try:
            return self.moderation.getLink()
        except:
            return str()

    def moderationRetriesLeft(self) -> int:
        if self.status != Code.APPROVED:
            return 2 - Moderation.objects.filter(type=CORE_PROJECT, coreproject=self).count()
        return 0

    def canRetryModeration(self) -> bool:
        return self.status != Code.APPROVED and self.moderationRetriesLeft() > 0 and not self.trashed and not self.suspended

    def getTrashLink(self) -> str:
        return url.projects.trash(self.getID())

    def editProfileLink(self):
        return f"{url.getRoot(APPNAME)}{url.projects.profileEdit(projectID=self.getID(),section=project.PALLETE)}"
    
    def under_mod_invitation(self):
        return CoreModerationTransferInvitation.objects.filter(coreproject=self, resolved=False).exists()

    def current_mod_invitation(self):
        try:
            return CoreModerationTransferInvitation.objects.get(coreproject=self, resolved=False)
        except:
            return None

    def can_invite_mod(self):
        return self.status == Code.APPROVED and not self.trashed and not self.suspended and not self.under_mod_invitation() and not self.under_del_request()

    def can_invite_profile(self, profile):
        
        return profile.is_manager() and (profile not in [self.creator, self.moderator, self.mentor]) and not (
            self.moderator.isBlockedProfile(profile) or self.creator.isBlockedProfile(profile) or (self.mentor and self.mentor.isBlockedProfile(profile))
        )

    def can_invite_mod_profile(self, profile):
        return self.can_invite_mod() and self.can_invite_profile(profile)

    def cancel_moderation_invitation(self):
        return CoreModerationTransferInvitation.objects.filter(coreproject=self).delete()

    def transfer_moderation_to(self,newmoderator):
        if not (self.isApproved() or self.trashed or self.suspended):
            return False
        elif CoreModerationTransferInvitation.objects.filter(coreproject=self, sender=self.moderator, receiver=newmoderator, resolved=True).exists():
            mod = self.moderation
            if not mod:
                return False
            oldmoderator = mod.moderator
            mod.moderator = newmoderator
            mod.save()
            cache.delete(f"coreproject_moderation_{self.get_id}")
            try:
                self.gh_repo().add_to_collaborators(newmoderator.ghID,permission='maintain')
                self.gh_repo().remove_from_collaborators(oldmoderator.ghID)
            except:
                pass
            try:
                self.gh_team().add_membership(
                    member=newmoderator.gh_user(),
                    role="maintainer"
                )
                self.gh_team().remove_membership(
                    member=oldmoderator.gh_user()
                )
            except:
                pass
            return True
        return False

    def under_del_request(self):
        return CoreProjectDeletionRequest.objects.filter(coreproject=self, resolved=False).exists()

    def current_del_request(self):
        try:
            return CoreProjectDeletionRequest.objects.get(coreproject=self, resolved=False)
        except:
            return None

    def can_request_deletion(self):
        return not (self.trashed or self.suspended or self.status != Code.APPROVED or self.under_invitation() or self.under_mod_invitation() or self.under_del_request() or self.under_verification_request())

    def request_deletion(self):
        if not self.can_request_deletion():
            return False
        return CoreProjectDeletionRequest.objects.create(coreproject=self, sender=self.creator, receiver=self.moderator)

    def cancel_del_request(self):
        return CoreProjectDeletionRequest.objects.filter(coreproject=self).delete()
    
    def moveToTrash(self) -> bool:
        if not (self.isApproved() or self.trashed or self.suspended):
            self.trashed = True
            self.creator.decreaseXP(by=2)
            self.save()
            if self.moderation and self.moderation.isPending():
                self.moderation.delete()
                self.delete()
        elif CoreProjectDeletionRequest.objects.filter(coreproject=self, sender=self.creator, receiver=self.moderator, resolved=True).exists():
            self.trashed = True
            self.creator.decreaseXP(by=2)
            self.save()
        return self.trashed

    def under_verification_request(self):
        return CoreProjectVerificationRequest.objects.filter(coreproject=self, resolved=False).exists()

    def cancel_verification_request(self):
        req = self.current_verification_request()
        if req:
            if not req.verifiedproject.isApproved():
                req.verifiedproject.delete()
                return True
        return False

    def current_verification_request(self):
        try:
            return CoreProjectVerificationRequest.objects.get(coreproject=self, resolved=False)
        except:
            return None

    def can_request_verification(self):
        return not (self.trashed or self.suspended or self.under_invitation() or self.under_verification_request() or self.under_del_request() or self.under_mod_invitation())

    def request_verification(self):
        if not self.can_request_verification():
            return False
        return CoreProjectVerificationRequest.objects.create(coreproject=self)
    
    def moveToVerified(self) -> bool:
        try:
            cpvr = CoreProjectVerificationRequest.objects.get(coreproject=self, resolved=True)
            if not cpvr.verifiedproject.isApproved():
                return False
            Snapshot.objects.filter(base_project=self.base()).update(base_project=cpvr.verifiedproject.base())
            ProjectSocial.objects.filter(project=self.base()).update(project=cpvr.verifiedproject.base())
            cpvr.verifiedproject.admirers.set(self.admirers.all())
            self.gh_repo().edit(private=False)
            self.delete()
            return True
        except:
            return False
    
    def can_invite_cocreator_profile(self,profile):
        return self.can_invite_profile(profile)


class LegalDoc(models.Model):
    class Meta:
        unique_together = ('name', 'pseudonym')

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    name = models.CharField(max_length=1000)
    pseudonym = models.CharField(max_length=1000, unique=True)
    about = models.CharField(max_length=100, null=True, blank=True)
    content = models.CharField(max_length=100000)
    icon = models.CharField(max_length=20, default='policy')
    contactmail = models.CharField(max_length=30, default=BOTMAIL)
    lastUpdate = models.DateTimeField(
        auto_now=False, default=timezone.now, editable=False)
    effectiveDate = models.DateTimeField(auto_now=False, default=timezone.now)
    notify_all = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if LegalDoc.objects.filter(id=self.id).exists():
            if self.content != (LegalDoc.objects.get(id=self.id)).content:
                self.lastUpdate = timezone.now()
                if self.notify_all:
                    addMethodToAsyncQueue(f"{MANAGEMENT}.mailers.alertLegalUpdate", self.name, self.getLink())
        self.notify_all = False
        super(LegalDoc, self).save(*args, **kwargs)

    def getLink(self):
        return f"{url.getRoot(DOCS)}{url.docs.type(self.pseudonym)}"


class ProjectHookRecord(HookRecord):
    """
    Github Webhook event record to avoid redelivery misuse.
    """
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='hook_record_project')

class BotHookRecord(HookRecord):
    """
    Github Webhook event record to avoid redelivery misuse.
    """
    ghmarketapp = models.ForeignKey(GhMarketApp, on_delete=models.CASCADE, related_name='hook_record_ghmarketapp')
    baseproject = models.ForeignKey(BaseProject, on_delete=models.CASCADE, null=True,blank=True, related_name='bot_hook_record_baseproject')

class CoreProjectHookRecord(HookRecord):
    """
    Github Webhook event record to avoid redelivery misuse.
    """
    coreproject = models.ForeignKey(CoreProject, on_delete=models.CASCADE, related_name='hook_record_project')

def snapMediaPath(instance, filename):
    fileparts = filename.split('.')
    return f"{APPNAME}/snapshots/{str(instance.get_id)}-{str(uuid4().hex)}.{fileparts[len(fileparts)-1]}"

class Snapshot(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    base_project = models.ForeignKey(BaseProject, on_delete=models.CASCADE, related_name='base_project_snapshot')
    text = models.CharField(max_length=6000,null=True,blank=True)
    image = models.ImageField(upload_to=snapMediaPath, max_length=500, null=True, blank=True)
    video = models.FileField(upload_to=snapMediaPath, max_length=500, null=True, blank=True)
    creator = models.ForeignKey(f"{PEOPLE}.Profile", on_delete=models.CASCADE, related_name='project_snapshot_creator')
    created_on = models.DateTimeField(auto_now=False, default=timezone.now)
    modified_on = models.DateTimeField(auto_now=False, default=timezone.now)
    admirers = models.ManyToManyField(f"{PEOPLE}.Profile", through='SnapshotAdmirer', default=[], related_name='snapshot_admirer')
    suspended = models.BooleanField(default=False)

    @property
    def get_id(self):
        return self.id.hex

    def save(self, *args, **kwargs):
        self.modified_on = timezone.now()
        super(Snapshot, self).save(*args, **kwargs)

    @property
    def project_id(self):
        return self.base_project.get_id

    @property
    def get_image(self):
        return f"{settings.MEDIA_URL}{str(self.image)}"

    @property
    def get_video(self):
        return f"{settings.MEDIA_URL}{str(self.video)}"

    @property
    def get_link(self) -> str:
        return self.getLink()

    def getLink(self, success: str = '', error: str = '', alert: str = '') -> str:
        return f"{url.getRoot()}{url.view_snapshot(snapID=self.get_id)}{url.getMessageQuery(alert,error,success)}"

    def is_admirer(self, profile):
        cacheKey = f"admirer_{profile.id}_of_snap_{self.id}"
        isadm = cache.get(cacheKey, None)
        if isadm is None:
            isadm = SnapshotAdmirer.objects.filter(snapshot=self, profile=profile).exists()
            cache.set(cacheKey, isadm, settings.CACHE_LONG)
        return isadm

class ReportedProject(models.Model):
    class Meta:
        unique_together = ('profile', 'baseproject', 'category')

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    profile = models.ForeignKey(f'{PEOPLE}.Profile', on_delete=models.CASCADE, related_name='project_reporter_profile')
    baseproject = models.ForeignKey(BaseProject, on_delete=models.CASCADE, related_name='reported_baseproject')
    category = models.ForeignKey(ReportCategory, on_delete=models.PROTECT, related_name='reported_project_category')

class ReportedSnapshot(models.Model):
    class Meta:
        unique_together = ('profile', 'snapshot', 'category')

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    profile = models.ForeignKey(f'{PEOPLE}.Profile', on_delete=models.CASCADE, related_name='snapshot_reporter_profile')
    snapshot = models.ForeignKey(Snapshot, on_delete=models.CASCADE, related_name='reported_snapshot')
    category = models.ForeignKey(ReportCategory, on_delete=models.PROTECT, related_name='reported_snapshot_category')

class ProjectAdmirer(models.Model):
    class Meta:
        unique_together = ('profile', 'base_project')

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    profile = models.ForeignKey(f'{PEOPLE}.Profile', on_delete=models.CASCADE, related_name='project_admirer_profile')
    base_project = models.ForeignKey(BaseProject, on_delete=models.CASCADE, related_name='admired_baseproject')

class SnapshotAdmirer(models.Model):
    class Meta:
        unique_together = ('profile', 'snapshot')

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    profile = models.ForeignKey(f'{PEOPLE}.Profile', on_delete=models.CASCADE, related_name='snapshot_admirer_profile')
    snapshot = models.ForeignKey(Snapshot, on_delete=models.CASCADE, related_name='admired_snapshot')


class FileExtension(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    extension = models.CharField(max_length=50, unique=True)
    description = models.CharField(max_length=500, null=True, blank=True)
    topics = models.ManyToManyField(f'{PEOPLE}.Topic', through='TopicFileExtension', default=[], related_name='file_extension_topics')

    def __str__(self):
        return str(self.extension)
        
    def getTags(self):
        tags = []
        for topic in self.topics.all():
            tags = tags + list(topic.getTags())
        return tags

    def getTopics(self):
        topics = cache.get(f"file_ext_topics_{self.id}",[])
        if not len(topics):
            topics = self.topics.all()
            if len(topics):
                cache.set(f"file_ext_topics_{self.id}", topics, settings.CACHE_INSTANT)
        return topics

class TopicFileExtension(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    topic = models.ForeignKey(f'{PEOPLE}.Topic', on_delete=models.CASCADE, related_name='topic_file_extension_topic')
    file_extension = models.ForeignKey(FileExtension, on_delete=models.CASCADE, related_name='topic_file_extension_extension')

class ProjectTransferInvitation(Invitation):
    baseproject = models.OneToOneField(BaseProject, on_delete=models.CASCADE, related_name='invitation_baseproject')
    sender = models.ForeignKey(f'{PEOPLE}.Profile', on_delete=models.CASCADE, related_name='transfer_invitation_sender')
    receiver = models.ForeignKey(f'{PEOPLE}.Profile', on_delete=models.CASCADE, related_name='transfer_invitation_receiver')

    class Meta:
        unique_together = ('sender', 'receiver', 'baseproject')
    
    def getLink(self, success: str = '', error: str = '', alert: str = '') -> str:
        return f"{url.getRoot(APPNAME)}{url.projects.projectTransInvite(self.get_id)}{url.getMessageQuery(alert,error,success)}"

    @property
    def get_link(self):
        return self.getLink()

    @property
    def get_act_link(self):
        return f"{url.getRoot(APPNAME)}{url.projects.projectTransInviteAct(self.get_id)}"

    def accept(self):
        if self.expired: return False
        if self.resolved: return False
        done = self.baseproject.transfer_to(self.receiver)
        if not done: return done
        self.resolve()
        return done

    def decline(self):
        return super(ProjectTransferInvitation, self).decline()

class CoreModerationTransferInvitation(Invitation):
    coreproject = models.OneToOneField(CoreProject, on_delete=models.CASCADE, related_name='mod_invitation_coreproject')
    sender = models.ForeignKey(f'{PEOPLE}.Profile', on_delete=models.CASCADE, related_name='mod_coretransfer_invitation_sender')
    receiver = models.ForeignKey(f'{PEOPLE}.Profile', on_delete=models.CASCADE, related_name='mod_coretransfer_invitation_receiver')

    class Meta:
        unique_together = ('sender', 'receiver','coreproject')

    def getLink(self, success: str = '', error: str = '', alert: str = '') -> str:
        return f"{url.getRoot(APPNAME)}{url.projects.coreModTransInvite(self.get_id)}{url.getMessageQuery(alert,error,success)}"

    @property
    def get_link(self):
        return self.getLink()

    @property
    def get_act_link(self):
        return f"{url.getRoot(APPNAME)}{url.projects.coreModTransInviteAct(self.get_id)}"

    def accept(self):
        if self.expired: return False
        if self.resolved: return False
        self.resolve()
        done = self.coreproject.transfer_moderation_to(self.receiver)
        if not done:
            self.unresolve()
        return done

    def decline(self):
        return super(CoreModerationTransferInvitation, self).decline()

class ProjectModerationTransferInvitation(Invitation):
    project = models.OneToOneField(Project, on_delete=models.CASCADE, related_name='mod_invitation_verifiedproject')
    sender = models.ForeignKey(f'{PEOPLE}.Profile', on_delete=models.CASCADE, related_name='mod_verifiedtransfer_invitation_sender')
    receiver = models.ForeignKey(f'{PEOPLE}.Profile', on_delete=models.CASCADE, related_name='mod_verifiedtransfer_invitation_receiver')

    class Meta:
        unique_together = ('sender', 'receiver','project')

    def getLink(self, success: str = '', error: str = '', alert: str = '') -> str:
        return f"{url.getRoot(APPNAME)}{url.projects.verifiedModTransInvite(self.get_id)}{url.getMessageQuery(alert,error,success)}"

    @property
    def get_link(self):
        return self.getLink()

    @property
    def get_act_link(self):
        return f"{url.getRoot(APPNAME)}{url.projects.verifiedModTransInviteAct(self.get_id)}"

    def accept(self):
        if self.expired: return False
        if self.resolved: return False
        self.resolve()
        done = self.project.transfer_moderation_to(self.receiver)
        if not done:
            self.unresolve()
        return done

    def decline(self):
        return super(ProjectModerationTransferInvitation, self).decline()

class VerProjectDeletionRequest(Invitation):
    project = models.OneToOneField(Project, on_delete=models.CASCADE, related_name='deletion_request_project')
    sender = models.ForeignKey(f'{PEOPLE}.Profile', on_delete=models.CASCADE, related_name='deletion_request_sender')
    receiver = models.ForeignKey(f'{PEOPLE}.Profile', on_delete=models.CASCADE, related_name='deletion_request_receiver')

    class Meta:
        unique_together = ('sender', 'receiver','project')

    def getLink(self, success: str = '', error: str = '', alert: str = '') -> str:
        return f"{url.getRoot(APPNAME)}{url.projects.verDeletionRequest(self.get_id)}{url.getMessageQuery(alert,error,success)}"

    @property
    def get_link(self):
        return self.getLink()

    @property
    def get_act_link(self):
        return f"{url.getRoot(APPNAME)}{url.projects.verDeletionRequestAct(self.get_id)}"

    def accept(self):
        if self.expired: return False
        if self.resolved: return False
        self.resolve()
        done = self.project.moveToTrash()
        if not done:
            self.unresolve()
        return done

    def decline(self):
        self.delete()
        return True

class CoreProjectDeletionRequest(Invitation):
    coreproject = models.OneToOneField(CoreProject, on_delete=models.CASCADE, related_name='deletion_request_coreproject')
    sender = models.ForeignKey(f'{PEOPLE}.Profile', on_delete=models.CASCADE, related_name='deletion_coreproject_request_sender')
    receiver = models.ForeignKey(f'{PEOPLE}.Profile', on_delete=models.CASCADE, related_name='deletion_coreproject_request_receiver')

    class Meta:
        unique_together = ('sender', 'receiver','coreproject')

    def getLink(self, success: str = '', error: str = '', alert: str = '') -> str:
        return f"{url.getRoot(APPNAME)}{url.projects.coreDeletionRequest(self.get_id)}{url.getMessageQuery(alert,error,success)}"

    @property
    def get_link(self):
        return self.getLink()

    @property
    def get_act_link(self):
        return f"{url.getRoot(APPNAME)}{url.projects.coreDeletionRequestAct(self.get_id)}"

    def accept(self):
        if self.expired: return False
        if self.resolved: return False
        self.resolve()
        done = self.coreproject.moveToTrash()
        if not done:
            self.unresolve()
        return done

    def decline(self):
        self.delete()
        return True

class FreeProjectVerificationRequest(Invitation):
    
    freeproject = models.OneToOneField(FreeProject, on_delete=models.CASCADE, related_name='free_under_verification_freeproject')
    verifiedproject = models.OneToOneField(Project, on_delete=models.CASCADE, related_name='free_under_verification_verifiedproject')
    from_free = True
    from_core = False
    class Meta:
        unique_together = ('freeproject', 'verifiedproject')

    def accept(self):
        if self.expired: return False
        if self.resolved: return False
        self.resolve()
        done = self.freeproject.moveToVerified()
        if not done:
            self.unresolve()
        return done

    def decline(self):
        self.delete()
        return True

    def getLink(self, success: str = '', error: str = '', alert: str = '') -> str:
        return self.verifiedproject.getLink(success, error, alert)

class CoreProjectVerificationRequest(Invitation):
    
    coreproject = models.OneToOneField(CoreProject, on_delete=models.CASCADE, related_name='core_under_verification_coreproject')
    verifiedproject = models.OneToOneField(Project, on_delete=models.CASCADE, related_name='core_under_verification_verifiedproject')
    from_free = False
    from_core = True
    class Meta:
        unique_together = ('coreproject', 'verifiedproject')

    def accept(self):
        if self.expired: return False
        if self.resolved: return False
        self.resolve()
        done = self.coreproject.moveToVerified()
        if not done:
            self.unresolve()
        return done

    def decline(self):
        self.delete()
        return True

    def getLink(self, success: str = '', error: str = '', alert: str = '') -> str:
        return self.verifiedproject.getLink(success, error, alert)
