from uuid import UUID, uuid4

from deprecated import deprecated
from django.conf import settings
from django.core.cache import cache
from django.db import models
from django.utils import timezone
from github.Repository import Repository
from github.Team import Team
from jsonfield import JSONField
from main.bots import Github, GithubKnotters
from main.env import BOTMAIL
from main.methods import errorLog, human_readable_size, maxLengthInList
from main.strings import (CORE_PROJECT, DOCS, MANAGEMENT, PEOPLE, Code,
                          Message, project, url)
from management.models import (GhMarketApp, HookRecord, Invitation,
                               ReportCategory)
from moderation.models import Moderation

from .apps import APPNAME


class Tag(models.Model):
    """A tag model"""
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    name = models.CharField(max_length=150, null=False,
                            blank=False, unique=True)
    creator = models.ForeignKey(f"{PEOPLE}.Profile", on_delete=models.SET_NULL,
                                null=True, blank=True, related_name="tag_creator")

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
    """A project category model"""
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    name = models.CharField(max_length=100, null=False,
                            blank=False, unique=True)
    """name (CharField): The name of the category"""

    creator = models.ForeignKey(f"{PEOPLE}.Profile", on_delete=models.SET_NULL,
                                null=True, blank=True, related_name="category_creator")
    """creator (ForeignKey<Profile>): The creator of the category"""
    tags = models.ManyToManyField(Tag, through='CategoryTag', default=[])
    """tags (ManyToManyField<Tag>): The tags of the category"""

    ALL_CACHE_KEY = f"{APPNAME}_categories_all"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        super(Category, self).save(*args, **kwargs)
        self.reset_all_cache()

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
        return list(filter(lambda x: x != None, topics))

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

    def get_all(*args) -> models.QuerySet:
        """Get all categories, preferably from cache"""
        cacheKey = Category.ALL_CACHE_KEY
        cats = cache.get(cacheKey, [])
        if not len(cats):
            cats = Category.objects.filter()
            cache.set(cacheKey, cats, settings.CACHE_ETERNAL)
        return cats

    def reset_all_cache(*args) -> models.QuerySet:
        """Reset all categories cache"""
        cache.delete(Category.ALL_CACHE_KEY)
        cats = Category.objects.filter()
        cache.set(Category.ALL_CACHE_KEY, cats, settings.CACHE_ETERNAL)
        return cats

    def get_cache_one(*args, id) -> "Category":
        """Get one Category by id, preferably from cache"""
        return Category.get_all().get(id=id)


class CategoryTag(models.Model):
    """The model for relation between a category and a tag"""
    class Meta:
        unique_together = ('category', 'tag')

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    """category (ForeignKey<Category>): The category in relation"""
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)
    """tag (ForeignKey<Tag>): The tag in relation"""


class License(models.Model):
    """A license model for projects"""
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    name = models.CharField(max_length=50)
    """name (CharField): The name of the license"""
    keyword = models.CharField(max_length=80, null=True, blank=True,
                               help_text='The license keyword, refer https://docs.github.com/en/github/creating-cloning-and-archiving-repositories/creating-a-repository-on-github/licensing-a-repository#searching-github-by-license-type')
    """keyword (CharField): The keyword of the license (nickname type)"""
    description = models.CharField(max_length=1000, null=True, blank=True)
    """description (CharField): The description of the license"""
    content = models.CharField(max_length=300000, null=True, blank=True)
    """content (CharField): The content of the license"""
    public = models.BooleanField(default=False)
    """public (BooleanField): Whether the license is public or not (like allowed for open source projects or not)"""
    default = models.BooleanField(default=False)
    """default (BooleanField): Whether the license is default or not (default makes it to the first one in the list)"""
    creator = models.ForeignKey(f"{PEOPLE}.Profile", on_delete=models.PROTECT)
    """creator (ForeignKey<Profile>): The creator of the license"""
    createdOn = models.DateTimeField(
        auto_now=False, default=timezone.now, null=True, blank=True)
    """createdOn (DateTimeField): The creation date of the license"""
    modifiedOn = models.DateTimeField(
        auto_now=False, default=timezone.now, null=True, blank=True)
    """modifiedOn (DateTimeField): The modification date of the license"""

    ALL_CACHE_KEY = f"{APPNAME}_license_all_public"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        try:
            if self.content != License.objects.get(id=self.id).content:
                self.modifiedOn = timezone.now()
        except:
            pass
        super(License, self).save(*args, **kwargs)
        if self.public:
            self.reset_all_cache()

    @property
    def CACHE_KEYS(self):
        class CKEYS():
            license_baseprojects = f"license_baseprojects_{self.id}"
        return CKEYS()

    @property
    def get_id(self):
        return self.id.hex

    def getID(self):
        return self.get_id

    def getLink(self, success: str = '', error: str = '', message: str = '') -> str:
        """Get the link to the license view

        Args:
            success (str, optional): The success message. Defaults to ''.
            error (str, optional): The error message. Defaults to ''.
            message (str, optional): The message. Defaults to ''.

        Returns:
            str: The link to the license view
        """
        return f'{url.getRoot(APPNAME)}{url.projects.license(id=self.getID())}{url.getMessageQuery(alert=message,error=error,success=success)}'

    @property
    def get_link(self):
        return self.getLink()

    @property
    def is_custom(self):
        return self.creator.getEmail() != BOTMAIL and not self.public

    def isCustom(self):
        return self.is_custom

    def projects(self) -> models.QuerySet:
        """Get the Base projects that use this license

        Returns:
            models.QuerySet<BaseProject>: The Base projects instances that use this license
        """
        cacheKey = self.CACHE_KEYS.license_baseprojects
        projects = cache.get(cacheKey, [])
        if not len(projects):
            projects = BaseProject.objects.filter(
                license=self, suspended=False, trashed=False, is_archived=False)
            cache.set(cacheKey, projects, settings.CACHE_INSTANT)
        return projects

    def totalprojects(self):
        return self.projects().count()

    def get_all(*args) -> models.QuerySet:
        """Get all provided public licenses, preferably from cache"""
        cacheKey = License.ALL_CACHE_KEY
        licenses = cache.get(cacheKey, [])
        if not len(licenses):
            from people.models import Profile
            licenses = License.objects.filter(
                creator=Profile.KNOTBOT(), public=True).order_by("-default")
            cache.set(cacheKey, licenses, settings.CACHE_ETERNAL)
        return licenses

    def reset_all_cache(*args) -> models.QuerySet:
        """Reset all licenses cache"""
        cache.delete(License.ALL_CACHE_KEY)
        from people.models import Profile
        licenses = License.objects.filter(
            creator=Profile.KNOTBOT(), public=True).order_by("-default")
        cache.set(License.ALL_CACHE_KEY, licenses, settings.CACHE_ETERNAL)
        return licenses

    def get_cache_one(*args, id) -> "License":
        """Get one provided public license by id, preferably from cache"""
        return License.get_all().get(id=id)


def projectImagePath(instance, filename):
    fileparts = filename.split('.')
    return f"{APPNAME}/avatars/{str(instance.getID())}_{str(uuid4().hex)}.{fileparts[-1]}"


def defaultImagePath():
    return f"{APPNAME}/default.png"


class BaseProject(models.Model):
    """The base model for all kinds of projects"""
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    name = models.CharField(max_length=50, null=False, blank=False)
    """name (CharField): The name of the project"""
    image = models.ImageField(upload_to=projectImagePath, max_length=500,
                              default=defaultImagePath, null=True, blank=True)
    """image (ImageField): The image of the project"""
    description = models.CharField(max_length=5000, null=False, blank=False)
    """description (CharField): The description of the project"""
    createdOn = models.DateTimeField(auto_now=False, default=timezone.now)
    """createdOn (DateTimeField): The creation date of the project"""
    modifiedOn = models.DateTimeField(auto_now=False, default=timezone.now)
    """modifiedOn (DateTimeField): The modification date of the project"""
    creator = models.ForeignKey(f"{PEOPLE}.Profile", on_delete=models.PROTECT)
    """creator (ForeignKey<Profile>): The creator of the project"""
    migrated = models.BooleanField(
        default=False, help_text='Indicates whether this project was created by someone whose account was deleted.')
    """migrated (BooleanField): Indicates whether this project was created by someone else and transferred."""
    migrated_by = models.ForeignKey(f"{PEOPLE}.Profile", on_delete=models.SET_NULL,
                                    null=True, blank=True, related_name="baseproject_migrated_by")
    """migrated_by (ForeignKey<Profile>): The profile who migrated this project"""
    migrated_on = models.DateTimeField(auto_now=False, null=True, blank=True)
    """migrated_on (DateTimeField): The date when this project was last migrated"""
    trashed = models.BooleanField(
        default=False, help_text="Deleted for creator, can be used when rejected.")
    """trashed (BooleanField): Indicates whether this project was trashed"""
    license = models.ForeignKey(License, on_delete=models.PROTECT)
    """license (ForeignKey<License>): The license of the project"""
    acceptedTerms = models.BooleanField(default=True)
    """acceptedTerms (BooleanField): Indicates whether the creator accepted the terms for this project"""
    suspended = models.BooleanField(default=False)
    """suspended (BooleanField): Indicates whether the project is suspended"""
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    """category (ForeignKey<Category>): The category of the project"""
    tags = models.ManyToManyField(Tag, through='ProjectTag', default=[])
    """tags (ManyToManyField<Tag>): The tags of the project"""
    topics = models.ManyToManyField(
        f'{PEOPLE}.Topic', through='ProjectTopic', default=[])
    """topics (ManyToManyField<Topic>): The topics of the project"""
    co_creators = models.ManyToManyField(f"{PEOPLE}.Profile", through="BaseProjectCoCreator", default=[
    ], related_name='base_project_co_creator')
    """co_creators (ManyToManyField<Profile>): The co-creators of the project"""
    admirers = models.ManyToManyField(f"{PEOPLE}.Profile", through='ProjectAdmirer', default=[
    ], related_name='base_project_admirer')
    """admirers (ManyToManyField<Profile>): The admirers of the project"""
    prime_collaborators = models.ManyToManyField(f"{PEOPLE}.Profile", through='BaseProjectPrimeCollaborator', default=[
    ], related_name='base_project_prime_collaborator')
    """prime_collaborators (ManyToManyField<Profile>): The prime collaborators of the project"""

    is_archived = models.BooleanField(default=False)
    """is_archived (BooleanField): Indicates whether the project is archived"""
    archive_forward_link = models.URLField(
        max_length=500, null=True, blank=True)
    """archive_forward_link (URLField): The forward link for people to visit if project is archived (optional)"""

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
            if not (previous.image in [self.image, defaultImagePath()]):
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
    def CACHE_KEYS(self):
        class CKEYS():
            homepage_projects = f"{APPNAME}_homepage_projects"
            baseproject_isfree = f"baseproject_is_free_{self.id}"
            baseproject_isverified = f"baseproject_is_verified_{self.id}"
            baseproject_iscore = f"baseproject_is_core_{self.id}"
            baseproject_is_approved = f"baseproject_is_approved_{self.id}"
            baseproject_is_pending = f"baseproject_is_pending_{self.id}"
            baseproject_is_rejected = f"baseproject_is_rejected_{self.id}"
            total_admirations = f'{self.id}_total_admiration'
        return CKEYS()

    def homepage_project() -> "BaseProject":
        cacheKey = 'homepage_project'
        project = cache.get(cacheKey, None)
        if not project:
            from people.models import Profile
            project = BaseProject.objects.filter(creator=Profile.KNOTBOT(),
                                                 suspended=False, trashed=False, is_archived=False).order_by("createdOn").first()
            cache.set(cacheKey, project, settings.CACHE_LONG)
        return project

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

    def getPalleteTopics(self, limit: int = 2) -> models.QuerySet:
        """Returns the topics of the project to be used in the pallete

        Args:
            limit (int, optional): The limit of topics to be returned. Defaults to 2.

        Returns:
            models.QuerySet<Topic>: The topic instances of the project to be used in the pallete
        """
        return self.topics.filter()[:limit]

    def getTopicsData(self) -> models.QuerySet:
        """Returns the topics relation instances of the project

        Returns:
            models.QuerySet<ProjectTopic>: The topic relation instances of the project
        """
        return ProjectTopic.objects.filter(project=self)

    def totalTopics(self) -> int:
        """Returns the total number of topics of the project"""
        return self.topics.count()

    @property
    def getTags(self) -> models.QuerySet:
        """Returns the tags of the project

        models.QuerySet<Tag>: The tag instances of the project
        """
        return self.tags.all()

    def getPalleteTags(self, limit: int = 2) -> models.QuerySet:
        """Returns the tags of the project to be used in the pallete

        Args:
            limit (int, optional): The limit of tags to be returned. Defaults to 2.

        Returns:
            models.QuerySet<Tag>: The tag instances of the project to be used in the pallete
        """
        return self.tags.filter()[:limit]

    def totalTags(self) -> int:
        """Returns the total number of tags of the project"""
        return self.tags.count()

    def theme(self) -> str:
        """Returns the theme of the project, depends on client side theme class names and project type."""
        if self.is_verified:
            return 'accent'
        if self.is_core:
            return 'vibrant'
        return "positive"

    def text_theme(self) -> str:
        """Returns the text theme of the project, depends on client side theme class names and project type."""
        if self.is_verified:
            return 'text-accent'
        if self.is_core:
            return "text-vibrant"
        return "text-positive"

    @property
    def is_normal(self) -> bool:
        """Returns True if the project is a normal project.

            Normal project is check for:
                - Is not suspended
                - Is not trashed
                - Is not archived
                - Has accepted terms
                - Is approved (if verified or core)

        Returns:
            bool: True if the project is a normal project
        """
        return not (self.suspended or self.trashed or self.is_archived or not self.acceptedTerms or not self.is_approved)

    @property
    def socialsites(self) -> models.QuerySet:
        """Returns the social sites instances of the project.

        Returns:
            models.QuerySet<ProjectSocial>: The social site instances of the project
        """
        cacheKey = f"baseproject_socialsites_{self.id}"
        sites = cache.get(cacheKey, [])
        if not len(sites):
            sites = ProjectSocial.objects.filter(project=self)
            if len(sites):
                cache.set(cacheKey, sites, settings.CACHE_INSTANT)
        return sites

    def addSocial(self, site: str) -> "ProjectSocial":
        """Adds a social site to the project.

        Args:
            site (str): The social site to be added

        Returns:
            ProjectSocial: The social site instance
        """
        return ProjectSocial.objects.create(project=self, site=site)

    def removeSocial(self, id: UUID):
        """Removes a social site from the project.

        Args:
            id (UUID): The id of the social site instance to be removed

        Returns:
            Tuple[int, dict[str, int]]: The number of affected rows, and the affected rows
        """
        return ProjectSocial.objects.filter(id=id, project=self).delete()

    @property
    def is_free(self) -> bool:
        """Returns True if the project is of type Quick (Freeproject)"""
        cacheKey = self.CACHE_KEYS.baseproject_isfree
        isFree = cache.get(cacheKey, None)
        if isFree is None:
            isFree = FreeProject.objects.filter(id=self.id).exists()
            cache.set(cacheKey, isFree, settings.CACHE_LONG)
        return isFree

    @property
    def is_not_free(self) -> bool:
        """Returns True if the project is not of type Quick (Freeproject)"""
        return not self.is_free

    @property
    def is_verified(self) -> bool:
        """Returns True if the project is of type Verified"""
        cacheKey = self.CACHE_KEYS.baseproject_isverified
        isVerified = cache.get(cacheKey, None)
        if isVerified is None:
            isVerified = Project.objects.filter(id=self.id).exists()
            cache.set(cacheKey, isVerified, settings.CACHE_LONG)
        return isVerified

    @property
    def is_core(self) -> bool:
        """Returns True if the project is of type Core"""
        cacheKey = self.CACHE_KEYS.baseproject_iscore
        isCore = cache.get(cacheKey, None)
        if isCore is None:
            isCore = CoreProject.objects.filter(id=self.id).exists()
            cache.set(cacheKey, isCore, settings.CACHE_LONG)
        return isCore

    @property
    def is_approved(self) -> bool:
        """Returns True if the project is approved (or Free)"""
        cacheKey = self.CACHE_KEYS.baseproject_is_approved
        isApproved = cache.get(cacheKey, None)
        if isApproved is None:
            isApproved = self.is_free or Project.objects.filter(id=self.id, status=Code.APPROVED).exists(
            ) or CoreProject.objects.filter(id=self.id, status=Code.APPROVED).exists()
            if isApproved:
                cache.set(cacheKey, isApproved, settings.CACHE_LONG)
        return isApproved

    @property
    def is_pending(self) -> bool:
        """Returns True if the project is pending"""
        cacheKey = self.CACHE_KEYS.baseproject_is_pending
        isPending = cache.get(cacheKey, None)
        if isPending is None:
            isPending = Project.objects.filter(id=self.id, status=Code.MODERATION).exists(
            ) or CoreProject.objects.filter(id=self.id, status=Code.MODERATION).exists()
            if not isPending:
                cache.set(cacheKey, isPending, settings.CACHE_LONG)
        return isPending

    @property
    def is_rejected(self) -> bool:
        """Returns True if the project is rejected"""
        cacheKey = self.CACHE_KEYS.baseproject_is_rejected
        isRejected = cache.get(cacheKey, None)
        if isRejected is None:
            isRejected = Project.objects.filter(id=self.id, status=Code.REJECTED).exists(
            ) or CoreProject.objects.filter(id=self.id, status=Code.REJECTED).exists()
            if isRejected:
                cache.set(cacheKey, isRejected, settings.CACHE_LONG)
        return isRejected

    def getProject(self, onlyApproved: bool = False):
        """Returns the child project instance.

        Args:
            onlyApproved (bool): If True, only status approved projects are returned, else status is not checked.

        Returns:
            Project/FreeProject/CoreProject: The child project instance
        """
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
        """Returns the link to the project profile"""
        return self.getLink()

    @property
    def get_abs_link(self) -> str:
        """Returns the absolute link to the project profile"""
        if self.get_link.startswith('http:'):
            return self.get_link
        return f"{settings.SITE}{self.get_link}"

    def getLink(self, success: str = '', error: str = '', alert: str = '') -> str:
        return self.getProject().getLink(success, error, alert)

    @property
    def get_nickname(self):
        """Returns the nickname of the project (extracting from child project)"""
        project = self.getProject()
        if project.verified:
            return project.reponame
        if project.core:
            return project.codename
        return project.nickname

    @property
    def total_admiration(self) -> int:
        """Returns the total number of admirers of the project"""
        cacheKey = self.CACHE_KEYS.total_admirations
        count = cache.get(cacheKey, None)
        if not count:
            count = self.admirers.count()
            cache.set(cacheKey, count, settings.CACHE_INSTANT)
        return count

    def total_admirers(self) -> int:
        """Returns the total number of admirers of the project"""
        return self.total_admiration

    def get_moderator(self):
        """Returns the moderator Profile instance of the project (extracting from child project, None for FreeProject)"""
        if self.is_free:
            return None
        return self.getProject(True).moderator

    def isAdmirer(self, profile) -> bool:
        """Returns True if the profile is an admirer of the project"""
        return self.admirers.filter(id=profile.id).exists()

    def under_invitation(self) -> bool:
        """Returns True if the project is under pending ownership invitation"""
        return ProjectTransferInvitation.objects.filter(baseproject=self, resolved=False).exists()

    def can_invite_owner(self) -> bool:
        """Returns True if a new owner can be invited for the project.

        General Conditions for this:
        - Project is normal
        - Not already under owndership invite
        - Not under moderatorship invite
        - No pending deletion request
        """
        return self.is_normal and not self.under_invitation() and not (self.is_not_free and (self.getProject().under_mod_invitation() or self.getProject().under_del_request()))

    def can_invite_profile(self, profile) -> bool:
        """To check if the given profile can be invited to the project,
            Uses same child project method to check as well.

        Args:
            profile (Profile): The profile to be invited

        Returns:
            bool: True if the profile can be invited to the project
        """
        return profile.is_normal and self.getProject().can_invite_profile(profile)

    def can_invite_owner_profile(self, profile) -> bool:
        """To check if the given profile can be invited as owner to the project.

        Args:
            profile (Profile): The profile to be invited

        Returns: 
            bool: True if the profile can be invited to the project
        """
        return self.can_invite_owner() and self.can_invite_profile(profile) and (profile.is_manager() if self.is_core else True)

    def current_invitation(self) -> "ProjectTransferInvitation":
        """Returns the current owndership invitation instance for the project."""
        try:
            return ProjectTransferInvitation.objects.get(baseproject=self, resolved=False)
        except:
            return None

    def cancel_invitation(self):
        """Cancels the current owndership invitation for the project by deleting the invitation record.

        Returns:
            Tuple[int, dict[str, int]]: The number of affected rows, and the affected rows
        """
        return ProjectTransferInvitation.objects.filter(baseproject=self).delete()

    def transfer_to(self, newcreator) -> bool:
        """Transfers the project to the new creator (primarily on ownership acceptance)

        Args:
            newcreator (Profile): The new creator profile instance

        Returns:
            bool: True if the transfer was successful
        """
        if not self.is_normal:
            return False
        if self.is_free:
            FreeRepository.objects.filter(
                free_project=self.getProject()).delete()
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
                        getproject.gh_repo().add_to_collaborators(nghid, permission='push')
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

    def max_allowed_assets(self) -> int:
        """Returns the maximum number of assets allowed for the project depending upon type."""
        if self.is_free:
            return 5
        else:
            return 10

    def assets(self) -> models.QuerySet:
        """Returns all asset instances of the project.

        Returns:
            models.QuerySet: The asset instances of the project
        """
        return Asset.objects.filter(baseproject=self)

    def total_assets(self) -> int:
        """Returns the total number of assets of the project."""
        return Asset.objects.filter(baseproject=self).count()

    def can_add_assets(self) -> bool:
        """Returns True if the project can add more assets."""
        return self.is_normal and self.total_assets() <= self.max_allowed_assets()

    def remaining_assets_limit(self) -> int:
        """Returns the number of more assets spaces remaining for the project."""
        return self.max_allowed_assets() - self.total_assets()

    def public_assets(self) -> models.QuerySet:
        """Returns all public asset instances of the project."""
        return Asset.objects.filter(baseproject=self, public=True)

    def total_public_assets(self) -> int:
        """Returns the total number of public assets of the project."""
        return Asset.objects.filter(baseproject=self, public=True).count()

    def private_assets(self) -> models.QuerySet:
        """Returns all private asset instances of the project."""
        return Asset.objects.filter(baseproject=self, public=False)

    def total_private_assets(self) -> int:
        """Returns the total number of private assets of the project."""
        return Asset.objects.filter(baseproject=self, public=False).count()

    def add_cocreator(self, co_creator) -> bool:
        """Adds a co-creator to the project (primarily on cocreatorship acceptance)

        Args:
            co_creator (Profile): The co-creator profile instance

        Returns:
            bool: True if the addition was successful
        """
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
        else:
            return False

    def remove_cocreator(self, co_creator) -> bool:
        """Removes an existing co-creator from the project"""
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

    def total_cocreators(self) -> int:
        """Returns the total number of cocreators of the project."""
        return self.co_creators.count()

    def under_cocreator_invitation(self) -> bool:
        """Returns True if the project is under any pending cocreator invitations."""
        return BaseProjectCoCreatorInvitation.objects.filter(base_project=self, resolved=False).exists()

    def total_cocreator_invitations(self) -> int:
        """Returns the total number of pending cocreator invitations of the project."""
        return BaseProjectCoCreatorInvitation.objects.filter(base_project=self, resolved=False).count()

    def under_cocreator_invitation_profile(self, profile) -> bool:
        """Returns True if the project is under any pending cocreator invitations for the given profile."""
        return BaseProjectCoCreatorInvitation.objects.filter(base_project=self, resolved=False, receiver=profile, expiresOn__gt=timezone.now()).exists()

    def can_invite_cocreator(self) -> bool:
        """Returns True if the project can invite more cocreators."""
        return self.is_normal and not self.under_invitation() and not (self.is_not_free and self.getProject().under_del_request()) and ((self.total_cocreator_invitations() + self.total_cocreators()) <= 10)

    def has_cocreators(self) -> bool:
        """Returns True if the project has any cocreators."""
        return self.co_creators.filter().exists()

    def can_invite_cocreator_profile(self, profile) -> bool:
        """Returns True if the project can invite the given profile as a cocreator."""
        return profile.is_normal and not self.co_creators.filter(user=profile.user).exists() and self.getProject().can_invite_cocreator_profile(profile) and not self.under_cocreator_invitation_profile(profile)

    def current_cocreator_invitations(self) -> models.QuerySet:
        """Returns all current pending cocreator invitation instances of the project."""
        return BaseProjectCoCreatorInvitation.objects.filter(base_project=self, resolved=False)

    def cancel_cocreator_invitation(self, profile):
        """Cancels the pending cocreator invitation for the given profile, by deleting the invitation record."""
        return BaseProjectCoCreatorInvitation.objects.filter(base_project=self, resolved=False, receiver=profile).delete()

    def cancel_all_cocreator_invitations(self):
        """Cancels all pending cocreator invitations for the given project, by deleting the invitation records."""
        return BaseProjectCoCreatorInvitation.objects.filter(base_project=self, resolved=False).delete()

    def moveToArchive(self, archive_forward_link: str = None) -> bool:
        """Move the project to archive.
        If archive_forward_link is provided, it will be used as the forwarding link for this archived project.

        Args:
            archive_forward_link (str, optional): Forwarding link for this archived project.

        Returns:
            bool: True if the project is moved to archive successfully.
        """
        try:
            if not self.is_normal:
                return False
            if self.is_free:
                FreeRepository.objects.filter(
                    free_project=self.getProject()).delete()
            self.archive_forward_link = archive_forward_link
            self.is_archived = True
            self.save()
            return True
        except:
            return False


class BaseProjectPrimeCollaborator(models.Model):
    """The model for relation between a project and a prime collaborator."""
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    prime_collaborator = models.ForeignKey(
        f"{PEOPLE}.Profile", on_delete=models.CASCADE, related_name="base_project_prime_collaborator_prime_collaborator")
    """prime_collaborator (ForeignKey<Profile>): The prime collaborator profile instance."""
    base_project = models.ForeignKey(
        BaseProject, on_delete=models.CASCADE, related_name="base_project_prime_collaborator_base_project")
    """base_project (ForeignKey<BaseProject>): The base project instance."""


class BaseProjectCoCreator(models.Model):
    """The model for relation between a project and a co-creator."""
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    co_creator = models.ForeignKey(
        f"{PEOPLE}.Profile", on_delete=models.CASCADE, related_name="base_project_co_creator_co_creator")
    """co_creator (ForeignKey<Profile>): The co-creator profile instance."""
    base_project = models.ForeignKey(
        BaseProject, on_delete=models.CASCADE, related_name="base_project_co_creator_base_project")
    """base_project (ForeignKey<BaseProject>): The base project instance."""


class BaseProjectCoCreatorInvitation(Invitation):
    """The model for a co-creator invitation."""
    base_project = models.ForeignKey(BaseProject, on_delete=models.CASCADE,
                                     related_name="base_project_co_creator_invitation_base_project")
    """base_project (ForeignKey<BaseProject>): The base project instance."""
    sender = models.ForeignKey(f'{PEOPLE}.Profile', on_delete=models.CASCADE,
                               related_name='base_project_co_creator_invitation_sender')
    """sender (ForeignKey<Profile>): The sender profile instance (owner of the project)."""
    receiver = models.ForeignKey(f'{PEOPLE}.Profile', on_delete=models.CASCADE,
                                 related_name='base_project_co_creator_invitation_receiver')
    """receiver (ForeignKey<Profile>): The receiver profile instance."""

    def accept(self) -> bool:
        """Accepts the invitation and adds the receiver as a co-creator of the project."""
        if self.expired:
            return False
        if self.resolved:
            return False
        done = self.base_project.add_cocreator(self.receiver)
        if not done:
            return False
        self.resolve()
        return done

    def decline(self) -> bool:
        """Declines the invitation and deletes the invitation record."""
        if self.expired:
            return False
        if self.resolved:
            return False
        self.delete()
        return True

    def getLink(self, success: str = '', error: str = '', alert: str = '') -> str:
        """Returns the link to the invitation view, to be used by receiver via GET method."""
        return f"{url.getRoot(APPNAME)}{url.projects.baseCocreatorInvite(self.get_id)}{url.getMessageQuery(alert,error,success)}"

    @property
    def get_link(self):
        return self.getLink()

    @property
    def get_act_link(self):
        """Returns the link to act on invitation, to be used by receiver via POST method."""
        return f"{url.getRoot(APPNAME)}{url.projects.baseCocreatorInviteAct(self.get_id)}"


class BaseProjectPrimeCollaboratorInvitation(Invitation):
    """The model for a prime collaborator invitation."""
    base_project = models.ForeignKey(BaseProject, on_delete=models.CASCADE,
                                     related_name="base_project_prime_collaborator_invitation_base_project")
    """base_project (ForeignKey<BaseProject>): The base project instance."""
    sender = models.ForeignKey(f'{PEOPLE}.Profile', on_delete=models.CASCADE,
                               related_name='base_project_prime_collaborator_invitation_sender')
    """sender (ForeignKey<Profile>): The sender profile instance (owner/moderator of the project)."""
    receiver = models.ForeignKey(f'{PEOPLE}.Profile', on_delete=models.CASCADE,
                                 related_name='base_project_prime_collaborator_invitation_receiver')
    """receiver (ForeignKey<Profile>): The receiver profile instance."""


class Project(BaseProject):
    """
    This is verified project model
    """
    url = models.CharField(max_length=500, null=True, blank=True)
    reponame = models.CharField(
        max_length=500, unique=True, null=False, blank=False)
    """reponame (CharField): The repository name. (becomes nickname)"""
    repo_id = models.IntegerField(default=0, null=True, blank=True)
    """repo_id (IntegerField): The repository id."""
    status = models.CharField(choices=project.PROJECTSTATESCHOICES, max_length=maxLengthInList(
        project.PROJECTSTATES), default=Code.MODERATION)
    """status (CharField): The project moderation status."""
    approvedOn = models.DateTimeField(auto_now=False, blank=True, null=True)
    """approvedOn (DateTimeField): The date and time when the project was approved."""

    mentor = models.ForeignKey(f"{PEOPLE}.Profile", on_delete=models.SET_NULL,
                               related_name='verified_project_mentor', null=True, blank=True)
    """mentor (ForeignKey<Profile>): The mentor profile instance."""

    verified = True
    core = False

    @property
    def CACHE_KEYS(self):
        class CKEYS():
            gh_repo_data = f"gh_repo_data_{self.repo_id}"
            gh_team_data = f"gh_team_data_{self.reponame}"
            base_project = f"baseproject_of_project_{self.id}"
        return CKEYS()

    def sub_save(self):
        assert len(self.reponame) > 0

    def getLink(self, success: str = '', error: str = '', alert: str = '') -> str:
        """Returns the link to the project profile."""
        try:
            if self.status != Code.APPROVED:
                return self.moderation.getLink(alert=alert, error=error, success=success)
            return f"{url.getRoot(APPNAME)}{url.projects.profile(reponame=self.reponame)}{url.getMessageQuery(alert,error,success)}"
        except Exception as e:
            errorLog(e)
            return f"{url.getRoot(APPNAME)}{url.getMessageQuery(alert,error,success)}"

    def isApproved(self) -> bool:
        """Returns True if the project is approved."""
        return self.status == Code.APPROVED

    def isLive(self) -> bool:
        """Returns True if the project is live (approved)"""
        return self.isApproved()

    def rejected(self) -> bool:
        """Returns True if the project is rejected."""
        return self.status == Code.REJECTED

    def underModeration(self) -> bool:
        """Returns True if the project is under moderation."""
        return self.status == Code.MODERATION

    def gh_repo(self) -> Repository:
        """Returns the GitHub API repository object of the project"""
        try:
            cacheKey = self.CACHE_KEYS.gh_repo_data
            if self.repo_id:
                repo = cache.get(cacheKey, None)
                if not repo:
                    repo = GithubKnotters.get_repo(self.reponame)
                    cache.set(cacheKey, repo, settings.CACHE_LONG)
                return repo
            else:
                repo = GithubKnotters.get_repo(self.reponame)
                self.repo_id = repo.id
                self.save()
                cache.set(cacheKey, repo, settings.CACHE_LONG)
                return repo
        except Exception as e:
            if not GithubKnotters:
                return None
            errorLog(e)
            return None

    def gh_repo_link(self) -> str:
        """Returns the GitHub repository link of the project"""
        repo = self.gh_repo()
        if not repo:
            return self.getLink(alert=Message.GH_REPO_NOT_SETUP)
        return repo.html_url

    def getRepoLink(self) -> str:
        """Returns the GitHub repository link of the project"""
        return self.gh_repo_link()

    @property
    def gh_team_name(self):
        """Returns the GitHub team name of the project"""
        return f'team-{self.reponame}'

    def gh_team(self) -> Team:
        """Returns the GitHub API team object of the project"""
        try:
            if not self.isApproved():
                return None
            cachekey = self.CACHE_KEYS.gh_team_data
            team = cache.get(cachekey, None)
            if not team:
                team = GithubKnotters.get_team_by_slug(self.gh_team_name)
                cache.set(cachekey, team, settings.CACHE_LONG)
            return team
        except Exception as e:
            return None

    def base(self) -> BaseProject:
        """Returns the base project instance of this child project"""
        cacheKey = self.CACHE_KEYS.base_project
        projectbase = cache.get(cacheKey, None)
        if projectbase is None:
            projectbase = BaseProject.objects.get(id=self.id)
            cache.set(cacheKey, projectbase, settings.CACHE_LONG)
        return projectbase

    @property
    def nickname(self) -> str:
        """Returns the nickname of the project (reponame)"""
        return self.reponame

    @property
    def moderation(self) -> Moderation:
        """Returns the moderation instance of the project"""
        return Moderation.objects.filter(project=self, type=APPNAME).order_by('-requestOn', '-respondOn').first()

    @property
    def moderator(self):
        """Returns the moderator profile instance of the project"""
        mod = self.moderation
        return None if not mod else mod.moderator

    def getModerator(self) -> models.Model:
        """Returns the moderator profile instance of the project"""
        if not self.isApproved():
            return None
        mod = self.moderation
        return None if not mod else mod.moderator

    def getModLink(self) -> str:
        """Returns the moderation view link of the project"""
        try:
            return self.moderation.getLink()
        except:
            return str()

    def moderationRetriesLeft(self) -> int:
        """Returns the number of retries left for the moderation re-request"""
        maxtries = 0
        if self.status != Code.APPROVED:
            maxtries = 1 - \
                Moderation.objects.filter(
                    type=APPNAME, project=self, resolved=True).count()
        return maxtries

    def canRetryModeration(self) -> bool:
        """Returns True if the project can be re-requested for moderation"""
        return self.status != Code.APPROVED and self.moderationRetriesLeft() > 0 and not self.trashed and not self.suspended

    def getTrashLink(self) -> str:
        """Returns the trash link of the project, to be used by creator via POST method"""
        return url.projects.trash(self.getID())

    def editProfileLink(self) -> str:
        """Returns the edit profile link of the project, to be used by creators/moderator via POST method"""
        return f"{url.getRoot(APPNAME)}{url.projects.profileEdit(projectID=self.getID(),section=project.PALLETE)}"

    def under_mod_invitation(self) -> bool:
        """Returns True if the project is under pending moderatorship transfer invitation (approved project)"""
        return ProjectModerationTransferInvitation.objects.filter(project=self, resolved=False).exists()

    def can_invite_mod(self) -> bool:
        """Returns True if moderatorship transfer can be initiated for the project (approved project)"""
        return self.status == Code.APPROVED and not self.trashed and not self.suspended and not self.under_mod_invitation() and not self.under_del_request()

    def can_invite_profile(self, profile) -> bool:
        """Returns True if the profile can be invited for the project (general) (approved project)

        Args:
            profile (Profile): The profile to be invited

        Returns: 
            bool: True if the profile can be invited as new moderator for the project
        """
        return (profile not in [self.creator, self.moderator, self.mentor]) and not (
            self.moderator.isBlockedProfile(profile) or self.creator.isBlockedProfile(
                profile) or (self.mentor and self.mentor.isBlockedProfile(profile))
        )

    def can_invite_mod_profile(self, profile) -> bool:
        """Returns True if the profile can be invited as new moderator for the project (approved project)

        Args:
            profile (Profile): The profile to be invited

        Returns: 
            bool: True if the profile can be invited as new moderator for the project
        """
        return self.can_invite_mod() and self.can_invite_profile(profile)

    def current_mod_invitation(self) -> "ProjectModerationTransferInvitation":
        """Returns the current pending moderatorship transfer invitation instance for the project (approved project)"""
        try:
            return ProjectModerationTransferInvitation.objects.get(project=self, resolved=False)
        except:
            return None

    def cancel_moderation_invitation(self):
        """Cancels the pending moderatorship transfer invitation for the project (approved project) by deleting the invitation record"""
        return ProjectModerationTransferInvitation.objects.filter(project=self).delete()

    def transfer_moderation_to(self, newmoderator) -> bool:
        """Transfers the moderatorship to the new moderator for the project (approved project), primarily after moderatorship acceptence by new moderator.

        Args:
            newmoderator (Profile): The new moderator to be transferred
        
        Returns:
            bool: True if the moderatorship transfer was successful
        """
        if not self.is_normal:
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
                self.gh_repo().add_to_collaborators(newmoderator.ghID, permission='maintain')
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

    def under_del_request(self) -> bool:
        """Returns True if the project is under pending deletion request"""
        return VerProjectDeletionRequest.objects.filter(project=self, sender=self.creator, receiver=self.moderator, resolved=False).exists()

    def cancel_del_request(self):
        """Cancels the pending deletion request for the project (approved project) by deleting the request record"""
        return VerProjectDeletionRequest.objects.filter(project=self).delete()

    def current_del_request(self) -> "VerProjectDeletionRequest":
        """Returns the current pending deletion request instance for the project (approved project)"""
        try:
            return VerProjectDeletionRequest.objects.get(project=self, resolved=False)
        except:
            return None

    def can_request_deletion(self) -> bool:
        """Returns True if the project can be deleted (approved project)"""
        return not (self.trashed or self.suspended or self.status != Code.APPROVED or self.under_invitation() or self.under_mod_invitation() or self.under_del_request())

    def request_deletion(self) -> bool:
        """Requests the deletion of the project (approved project)"""
        if not self.can_request_deletion():
            return False
        return VerProjectDeletionRequest.objects.create(project=self, sender=self.creator, receiver=self.moderator)

    def moveToTrash(self) -> bool:
        """Moves the project to trash, after the deletion request is approved"""
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

    def is_from_verification(self) -> bool:
        """Returns True if the project was created from a verification request"""
        return FreeProjectVerificationRequest.objects.filter(verifiedproject=self).exists() or CoreProjectVerificationRequest.objects.filter(verifiedproject=self).exists()

    def from_verification(self) -> "FreeProjectVerificationRequest":
        """Returns the verification request instance for the project"""
        return FreeProjectVerificationRequest.objects.filter(verifiedproject=self).first() or CoreProjectVerificationRequest.objects.filter(verifiedproject=self).first() or None

    def can_invite_cocreator_profile(self, profile) -> bool:
        """Returns True if the profile can be invited as new cocreator for the project (approved project)
        
        Args:
            profile (Profile): The profile to be invited
        
        Returns:
            bool: True if the profile can be invited as new cocreator for the project
        """
        return self.can_invite_profile(profile)


def assetFilePath(instance, filename):
    fileparts = filename.split('.')
    return f"{APPNAME}/assets/{str(instance.baseproject.get_id)}-{str(instance.get_id)}_{uuid4().hex}.{fileparts[-1]}"


class Asset(models.Model):
    """
    A project's asset (file) model.
    """
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    baseproject = models.ForeignKey(BaseProject, on_delete=models.CASCADE)
    """baseproject (ForiegnKey<BaseProject>): The project that the asset belongs to"""
    name = models.CharField(max_length=250, null=False, blank=False)
    """name (CharField): The name of the asset"""
    file = models.FileField(upload_to=assetFilePath, max_length=500)
    """file (FileField): The asset file"""
    public = models.BooleanField(default=False)
    """public (BooleanField): Whether the asset is public or not"""
    created_on = models.DateTimeField(auto_now=False, default=timezone.now)
    """created_on (DateTimeField): The date and time the asset was created"""
    modified_on = models.DateTimeField(auto_now=False)
    """modified_on (DateTimeField): The date and time the asset was last modified"""
    creator = models.ForeignKey(
        f"{PEOPLE}.Profile", on_delete=models.CASCADE, related_name="asset_creator")
    """creator (ForeignKey<Profile>): The profile that created the asset"""

    @property
    def get_id(self):
        return self.id.hex

    def save(self, *args, **kwargs):
        self.modified_on = timezone.now()
        super(Asset, self).save(*args, **kwargs)

    def move_to_project(self, baseproject: BaseProject) -> bool:
        """
        Moves the asset to a new project, if possible

        Args:
            baseproject (BaseProject): The project to move the asset to
        
        Returns:
            bool: True if the asset was moved to the new project
        """
        if not baseproject.can_add_assets() or self.baseproject == baseproject:
            return False
        self.baseproject = baseproject
        self.save()
        return True

    @property
    def get_link(self):
        """Returns the asset's link"""
        return f"{settings.MEDIA_URL}{self.file.name}"

    @property
    def type(self):
        """Returns the asset's type"""
        return self.file.name.split('.')[-1]

    @property
    def size(self):
        """Returns the asset's size"""
        return self.file.size

    @property
    def display_size(self):
        """Returns the asset's human readable size"""
        return human_readable_size(self.file.size)


class FreeProject(BaseProject):
    """
    A quick project model
    """
    nickname = models.CharField(
        max_length=500, unique=True, null=False, blank=False)
    """nickname (CharField): The project's nickname"""
    verified = False
    core = False

    
    @property
    def CACHE_KEYS(self):
        class CKEYS():
            free_repo_exists = f"freeproject_freerepo_exists_{self.id}"
            linked_free_repo = f"freeproject_freerepo_{self.id}"
            base_project = f"baseproject_of_freeproject_{self.id}"
        return CKEYS()

    def getLink(self, success: str = '', error: str = '', alert: str = '') -> str:
        """Link to the project's profile"""
        return f"{url.getRoot(APPNAME)}{url.projects.profileFree(nickname=self.nickname)}{url.getMessageQuery(alert,error,success)}"

    def moveToTrash(self) -> bool:
        """Moves the project to trash"""
        if not self.can_delete():
            return False
        self.creator.decreaseXP(by=2, reason="Quick project deleted")
        self.delete()
        return True

    @property
    def has_linked_repo(self) -> bool:
        """Returns True if the project has a linked repo"""
        cacheKey = self.CACHE_KEYS.free_repo_exists
        freerepo = cache.get(cacheKey, None)
        if freerepo is None:
            freerepo = FreeRepository.objects.filter(
                free_project=self).exists()
            cache.set(cacheKey, freerepo, settings.CACHE_INSTANT)
        return freerepo

    @property
    def linked_repo(self) -> "FreeRepository":
        """Returns the project's linked repository instance"""
        try:
            cacheKey = self.CACHE_KEYS.linked_free_repo
            freerepo = cache.get(cacheKey, None)
            if freerepo is None:
                freerepo = FreeRepository.objects.get(free_project=self)
                cache.set(cacheKey, freerepo, settings.CACHE_INSTANT)
            return freerepo
        except:
            return None

    def editProfileLink(self) -> str:
        """Returns the link to the project's profile edit page, to be used by creators via POST"""
        return f"{url.getRoot(APPNAME)}{url.projects.profileEdit(projectID=self.getID(),section=project.PALLETE)}"

    def base(self) -> BaseProject:
        """Returns this child project's base project instance"""
        cacheKey = self.CACHE_KEYS.base_project
        projectbase = cache.get(cacheKey, None)
        if projectbase is None:
            projectbase = BaseProject.objects.get(id=self.id)
            cache.set(cacheKey, projectbase, settings.CACHE_LONG)
        return projectbase

    def can_invite_profile(self, profile) -> bool:
        """Returns True if the profile can be invited to the project (generally)"""
        return profile not in [self.creator] and not (self.creator.isBlockedProfile(profile))

    def can_delete(self) -> bool:
        """Returns True if the project can be deleted"""
        return not (self.trashed or self.suspended or self.under_invitation() or self.under_verification_request())

    def under_verification_request(self) -> bool:
        """Returns True if the project is under a verification request"""
        return FreeProjectVerificationRequest.objects.filter(freeproject=self, resolved=False).exists()

    def cancel_verification_request(self) -> bool:
        """Cancels the project's verification request, by deleting the pending verified project."""
        req = self.current_verification_request()
        if req:
            if not req.verifiedproject.isApproved():
                req.verifiedproject.delete()
                return True
        return False

    def current_verification_request(self) -> "FreeProjectVerificationRequest":
        """Returns the project's current verification request"""
        try:
            return FreeProjectVerificationRequest.objects.get(freeproject=self, resolved=False)
        except:
            return None

    def can_request_verification(self) -> bool:
        """Returns True if the project can be verified"""
        return not (self.trashed or self.suspended or self.under_invitation() or self.under_verification_request())

    def request_verification(self) -> bool:
        """Requests the project's verification"""
        if not self.can_request_verification():
            return False
        return FreeProjectVerificationRequest.objects.create(freeproject=self)

    def moveToVerified(self) -> bool:
        """Moves the project to verified, after successfull approval of the verification request by moderator.
        Does so by moving all assets of this project to now approve verified project, and then deletes this project,
        or if this project was a part of competition's submission then archives this project.
        """
        try:
            fpvr = FreeProjectVerificationRequest.objects.get(
                freeproject=self, resolved=True)
            if not fpvr.verifiedproject.isApproved():
                return False
            Snapshot.objects.filter(base_project=self.base()).update(
                base_project=fpvr.verifiedproject.base())
            ProjectSocial.objects.filter(project=self.base()).update(
                project=fpvr.verifiedproject.base())
            fpvr.verifiedproject.admirers.set(self.admirers.all())
            fpvr.verifiedproject.co_creators.set(self.co_creators.all())
            fpvr.verifiedproject.prime_collaborators.set(
                self.prime_collaborators.all())
            if self.is_submission():
                self.moveToArchive(fpvr.verifiedproject.get_abs_link)
            else:
                self.delete()
            return True
        except:
            return False

    def is_submission(self) -> bool:
        """Returns True if the project is a competition's submission"""
        from compete.models import Submission
        return Submission.objects.filter(free_project=self).exists()

    def submission(self):
        """Returns the project's competition submission if exists"""
        from compete.models import Submission
        return Submission.objects.filter(free_project=self).first()

    def can_invite_cocreator_profile(self, profile) -> bool:
        """Returns True if the profile can be invited to the project as cocreator."""
        return self.can_invite_profile(profile)


class FreeRepository(models.Model):
    """
    One to one linked repository record for Quick (Free) projects
    """
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    free_project = models.OneToOneField(FreeProject, on_delete=models.CASCADE)
    """free_project (ForiegnKey<FreeProject>): The free (quick) project this repository is linked to"""
    repo_id = models.IntegerField()
    """repo_id (IntegerField): The repository's ID provided by github."""

    def gh_repo(self) -> Repository:
        """Returns the Github API repository instance of linked repository."""
        try:
            cacheKey = f"gh_repo_data_{self.repo_id}"
            data = cache.get(cacheKey)
            if not data:
                api = self.free_project.creator.gh_api()
                if not api:
                    api = Github
                data = api.get_repo(int(self.repo_id))
                if data:
                    cache.set(cacheKey, data, settings.CACHE_LONG)
            return data
        except Exception as e:
            return None

    @property
    def reponame(self) -> str:
        """Returns the repository's name"""
        data = self.gh_repo()
        if data:
            return data.name
        return None

    @property
    def repolink(self) -> str:
        """Returns the repository's link"""
        data = self.gh_repo()
        if data:
            return data.html_url
        return None

    def has_installed_app(self) -> bool:
        """Returns True if the repository has installed the knotters github app"""
        return AppRepository.objects.filter(free_repo=self).exists()

    def installed_app(self) -> "AppRepository":
        """Returns the repository's installed app record"""
        return AppRepository.objects.filter(free_repo=self).first()


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
    """The model for relation between a project and a tag."""
    class Meta:
        unique_together = ('project', 'tag')

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    project = models.ForeignKey(
        BaseProject, on_delete=models.CASCADE, null=True, blank=True)
    """project (ForeignKey<BaseProject>): The project in this relation."""
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE,
                            related_name='project_tag')
    """tag (ForeignKey<Tag>): The tag in this relation."""
                            


class ProjectTopic(models.Model):
    """The model for relation between a project and a topic."""
    class Meta:
        unique_together = ('project', 'topic')

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    project = models.ForeignKey(
        BaseProject, on_delete=models.CASCADE, null=True, blank=True)
    """project (ForeignKey<BaseProject>): The project in this relation."""
    topic = models.ForeignKey(f'{PEOPLE}.Topic', on_delete=models.CASCADE,
                              null=True, blank=True, related_name='project_topic')
    """topic (ForeignKey<Topic>): The topic in this relation."""


class ProjectSocial(models.Model):
    """The model for social site of a project."""
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    project = models.ForeignKey(BaseProject, on_delete=models.CASCADE)
    """project (ForeignKey<BaseProject>): The project."""
    site = models.URLField(max_length=800)
    """site (URLField): The URL of the social site."""


class CoreProject(BaseProject):
    """
    A core project's model
    """
    codename = models.CharField(
        max_length=500, unique=True, null=False, blank=False)
    """codename (CharField): The project's codename."""
    repo_id = models.IntegerField(default=0, null=True, blank=True)
    """repo_id (IntegerField): The project's repository's ID., provided by github."""
    budget = models.FloatField(default=0)
    """budget (FloatField): The project's budget."""
    mentor = models.ForeignKey(f"{PEOPLE}.Profile", on_delete=models.SET_NULL,
                               related_name='core_project_mentor', null=True, blank=True)
    """mentor (ForeignKey<Profile>): The project's mentor."""
    status = models.CharField(choices=project.PROJECTSTATESCHOICES, max_length=maxLengthInList(
        project.PROJECTSTATES), default=Code.MODERATION)
    """status (CharField): The project's status."""
    approvedOn = models.DateTimeField(auto_now=False, blank=True, null=True)
    """approvedOn (DateTimeField): The project's approval date."""
    verified = False
    core = True

    @property
    def CACHE_KEYS(self):
        class CKEYS():
            gh_repo_data =  f"gh_repo_data_{self.repo_id}"
            gh_team_data = f"gh_team_data_{self.codename}"
            base_project = f"baseproject_of_coreproject_{self.id}"
        return CKEYS()

    def editProfileLink(self):
        """The link to the edit project profile, to be used by creators via POST."""
        return f"{url.getRoot(APPNAME)}{url.projects.profileEdit(projectID=self.getID(),section=project.PALLETE)}"

    def getLink(self, success: str = '', error: str = '', alert: str = '') -> str:
        """The link to the project's profile."""
        try:
            if self.status != Code.APPROVED:
                return (Moderation.objects.filter(coreproject=self, type=CORE_PROJECT, status__in=[Code.REJECTED, Code.MODERATION]).order_by('-requestOn', '-respondOn').first()).getLink(alert=alert, error=error, success=success)
            return f"{url.getRoot(APPNAME)}{url.projects.profileCore(codename=self.codename)}{url.getMessageQuery(alert,error,success)}"
        except:
            return f"{url.getRoot(APPNAME)}{url.getMessageQuery(alert,error,success)}"

    def isApproved(self) -> bool:
        """Returns True if the project is approved."""
        return self.status == Code.APPROVED

    def isLive(self) -> bool:
        """Returns True if the project is live (Approved)."""
        return self.isApproved()

    def rejected(self) -> bool:
        """Returns True if the project is rejected."""
        return self.status == Code.REJECTED

    def underModeration(self) -> bool:
        """Returns True if the project is under moderation."""
        return self.status == Code.MODERATION

    def gh_repo(self) -> Repository:
        """Returns the github API repository object."""
        try:
            if self.repo_id:
                cacheKey = self.CACHE_KEYS.gh_repo_data
                repo = cache.get(cacheKey, None)
                if not repo:
                    repo = GithubKnotters.get_repo(self.codename)
                    cache.set(cacheKey, repo, settings.CACHE_LONG)
                return repo
            else:
                repo = GithubKnotters.get_repo(self.codename)
                self.repo_id = repo.id
                self.save()
                cache.set(cacheKey, repo, settings.CACHE_LONG)
                return repo
        except Exception as e:
            if not GithubKnotters:
                return None
            errorLog(e)
            return None

    def gh_repo_link(self) -> str:
        """Returns the github repository link."""
        repo = self.gh_repo()
        if not repo:
            return self.getLink(alert=Message.GH_REPO_NOT_SETUP)
        return repo.html_url

    def getRepoLink(self) -> str:
        """Returns the github repository link."""
        return self.gh_repo_link()

    @property
    def gh_team_name(self):
        """Returns the github team name."""
        return f'team-{self.codename}'

    def gh_team(self) -> Team:
        """Returns the github API team object."""
        try:
            if not self.isApproved():
                return None
            cachekey = self.CACHE_KEYS.gh_team_data
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
        cacheKey = self.CACHE_KEYS.base_project
        projectbase = cache.get(cacheKey, None)
        if projectbase is None:
            projectbase = BaseProject.objects.get(id=self.id)
            cache.set(cacheKey, projectbase, settings.CACHE_LONG)
        return projectbase

    @property
    def moderation(self) -> Moderation:
        return Moderation.objects.filter(coreproject=self, type=CORE_PROJECT).order_by('-requestOn', '-respondOn').first()

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

        return (profile not in [self.creator, self.moderator, self.mentor]) and not (
            self.moderator.isBlockedProfile(profile) or self.creator.isBlockedProfile(
                profile) or (self.mentor and self.mentor.isBlockedProfile(profile))
        )

    def can_invite_mod_profile(self, profile):
        return self.can_invite_mod() and self.can_invite_profile(profile)

    def cancel_moderation_invitation(self):
        return CoreModerationTransferInvitation.objects.filter(coreproject=self).delete()

    def transfer_moderation_to(self, newmoderator):
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
                self.gh_repo().add_to_collaborators(newmoderator.ghID, permission='maintain')
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
            cpvr = CoreProjectVerificationRequest.objects.get(
                coreproject=self, resolved=True)
            if not cpvr.verifiedproject.isApproved():
                return False
            Snapshot.objects.filter(base_project=self.base()).update(
                base_project=cpvr.verifiedproject.base())
            ProjectSocial.objects.filter(project=self.base()).update(
                project=cpvr.verifiedproject.base())
            cpvr.verifiedproject.admirers.set(self.admirers.all())
            self.gh_repo().edit(private=False)
            self.delete()
            return True
        except:
            return False

    def can_invite_cocreator_profile(self, profile):
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

    ALL_CACHE_KEY = "legal_docs_all"

    def __str__(self) -> str:
        return self.pseudonym or self.name

    def doc_cache_key(pseudonym, *args):
        return f"legal_doc_{pseudonym}"

    @property
    def CACHE_KEYS(self):
        class CKEYS():
            legaldoc_self = f"legaldoc_self_{self.id}"
        return CKEYS()

    def save(self, *args, **kwargs):
        if LegalDoc.objects.filter(id=self.id).exists():
            if self.content != (LegalDoc.objects.get(id=self.id)).content:
                self.lastUpdate = timezone.now()
                if self.notify_all:
                    from management.mailers import alertLegalUpdate
                    alertLegalUpdate(self.name, self.get_link)
        self.notify_all = False
        super(LegalDoc, self).save(*args, **kwargs)
        self.reset_all_cache()

    def getLink(self):
        return f"{url.getRoot(DOCS)}{url.docs.type(self.pseudonym)}"

    @property
    def get_link(self):
        return self.getLink()

    def get_doc(pseudonym: str) -> "LegalDoc":
        cacheKey = LegalDoc.doc_cache_key(pseudonym)
        legaldoc = cache.get(cacheKey, None)
        if not legaldoc:
            legaldoc = LegalDoc.objects.get(pseudonym=pseudonym)
            cache.set(cacheKey, legaldoc, settings.CACHE_ETERNAL)
        return legaldoc

    def get_all(*args) -> models.QuerySet:
        cacheKey = LegalDoc.ALL_CACHE_KEY
        legaldocs = cache.get(cacheKey, None)
        if not legaldocs:
            legaldocs = LegalDoc.objects.all()
            cache.set(cacheKey, legaldocs, settings.CACHE_ETERNAL)
        return legaldocs

    def reset_cache(self) -> "LegalDoc":
        cacheKey = self.CACHE_KEYS.legaldoc_self
        cache.delete(cacheKey)
        cache.delete(self.doc_cache_key(self.pseudonym))
        cache.set(cacheKey, self, settings.CACHE_ETERNAL)
        cache.set(self.doc_cache_key(self.pseudonym),
                  self, settings.CACHE_ETERNAL)
        return self

    def reset_all_cache(*args) -> models.QuerySet:
        cacheKey = LegalDoc.ALL_CACHE_KEY
        cache.delete(cacheKey)
        legaldocs = LegalDoc.objects.all()
        cache.set(cacheKey, legaldocs, settings.CACHE_ETERNAL)
        for ldoc in legaldocs:
            ldoc.reset_cache()
        return legaldocs


class ProjectHookRecord(HookRecord):
    """
    Github Webhook event record to avoid redelivery misuse.
    """
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name='hook_record_project')


class BotHookRecord(HookRecord):
    """
    Github Webhook event record to avoid redelivery misuse.
    """
    ghmarketapp = models.ForeignKey(
        GhMarketApp, on_delete=models.CASCADE, related_name='hook_record_ghmarketapp')
    baseproject = models.ForeignKey(BaseProject, on_delete=models.CASCADE,
                                    null=True, blank=True, related_name='bot_hook_record_baseproject')


class CoreProjectHookRecord(HookRecord):
    """
    Github Webhook event record to avoid redelivery misuse.
    """
    coreproject = models.ForeignKey(
        CoreProject, on_delete=models.CASCADE, related_name='hook_record_project')


def snapMediaPath(instance, filename):
    fileparts = filename.split('.')
    return f"{APPNAME}/snapshots/{str(instance.get_id)}-{str(uuid4().hex)}.{fileparts[len(fileparts)-1]}"


class Snapshot(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    base_project = models.ForeignKey(
        BaseProject, on_delete=models.CASCADE, related_name='base_project_snapshot')
    text = models.CharField(max_length=6000, null=True, blank=True)
    image = models.ImageField(upload_to=snapMediaPath,
                              max_length=500, null=True, blank=True)
    video = models.FileField(upload_to=snapMediaPath,
                             max_length=500, null=True, blank=True)
    creator = models.ForeignKey(
        f"{PEOPLE}.Profile", on_delete=models.CASCADE, related_name='project_snapshot_creator')
    created_on = models.DateTimeField(auto_now=False, default=timezone.now)
    modified_on = models.DateTimeField(auto_now=False, default=timezone.now)
    admirers = models.ManyToManyField(f"{PEOPLE}.Profile", through='SnapshotAdmirer', default=[
    ], related_name='snapshot_admirer')
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
            isadm = SnapshotAdmirer.objects.filter(
                snapshot=self, profile=profile).exists()
            cache.set(cacheKey, isadm, settings.CACHE_LONG)
        return isadm


class ReportedProject(models.Model):
    class Meta:
        unique_together = ('profile', 'baseproject', 'category')

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    profile = models.ForeignKey(
        f'{PEOPLE}.Profile', on_delete=models.CASCADE, related_name='project_reporter_profile')
    baseproject = models.ForeignKey(
        BaseProject, on_delete=models.CASCADE, related_name='reported_baseproject')
    category = models.ForeignKey(
        ReportCategory, on_delete=models.PROTECT, related_name='reported_project_category')


class ReportedSnapshot(models.Model):
    class Meta:
        unique_together = ('profile', 'snapshot', 'category')

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    profile = models.ForeignKey(
        f'{PEOPLE}.Profile', on_delete=models.CASCADE, related_name='snapshot_reporter_profile')
    snapshot = models.ForeignKey(
        Snapshot, on_delete=models.CASCADE, related_name='reported_snapshot')
    category = models.ForeignKey(
        ReportCategory, on_delete=models.PROTECT, related_name='reported_snapshot_category')


class ProjectAdmirer(models.Model):
    class Meta:
        unique_together = ('profile', 'base_project')

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    profile = models.ForeignKey(
        f'{PEOPLE}.Profile', on_delete=models.CASCADE, related_name='project_admirer_profile')
    base_project = models.ForeignKey(
        BaseProject, on_delete=models.CASCADE, related_name='admired_baseproject')


class SnapshotAdmirer(models.Model):
    class Meta:
        unique_together = ('profile', 'snapshot')

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    profile = models.ForeignKey(
        f'{PEOPLE}.Profile', on_delete=models.CASCADE, related_name='snapshot_admirer_profile')
    snapshot = models.ForeignKey(
        Snapshot, on_delete=models.CASCADE, related_name='admired_snapshot')


class FileExtension(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    extension = models.CharField(max_length=50, unique=True)
    description = models.CharField(max_length=500, null=True, blank=True)
    topics = models.ManyToManyField(f'{PEOPLE}.Topic', through='TopicFileExtension', default=[
    ], related_name='file_extension_topics')

    def __str__(self):
        return str(self.extension)

    def getTags(self):
        tags = []
        for topic in self.topics.all():
            tags = tags + list(topic.getTags())
        return tags

    def getTopics(self):
        topics = cache.get(f"file_ext_topics_{self.id}", [])
        if not len(topics):
            topics = self.topics.all()
            if len(topics):
                cache.set(f"file_ext_topics_{self.id}",
                          topics, settings.CACHE_INSTANT)
        return topics


class TopicFileExtension(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    topic = models.ForeignKey(
        f'{PEOPLE}.Topic', on_delete=models.CASCADE, related_name='topic_file_extension_topic')
    file_extension = models.ForeignKey(
        FileExtension, on_delete=models.CASCADE, related_name='topic_file_extension_extension')


class ProjectTransferInvitation(Invitation):
    baseproject = models.OneToOneField(
        BaseProject, on_delete=models.CASCADE, related_name='invitation_baseproject')
    sender = models.ForeignKey(
        f'{PEOPLE}.Profile', on_delete=models.CASCADE, related_name='transfer_invitation_sender')
    receiver = models.ForeignKey(
        f'{PEOPLE}.Profile', on_delete=models.CASCADE, related_name='transfer_invitation_receiver')

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
        if self.expired:
            return False
        if self.resolved:
            return False
        done = self.baseproject.transfer_to(self.receiver)
        if not done:
            return done
        self.resolve()
        return done

    def decline(self):
        return super(ProjectTransferInvitation, self).decline()


class CoreModerationTransferInvitation(Invitation):
    coreproject = models.OneToOneField(
        CoreProject, on_delete=models.CASCADE, related_name='mod_invitation_coreproject')
    sender = models.ForeignKey(f'{PEOPLE}.Profile', on_delete=models.CASCADE,
                               related_name='mod_coretransfer_invitation_sender')
    receiver = models.ForeignKey(
        f'{PEOPLE}.Profile', on_delete=models.CASCADE, related_name='mod_coretransfer_invitation_receiver')

    class Meta:
        unique_together = ('sender', 'receiver', 'coreproject')

    def getLink(self, success: str = '', error: str = '', alert: str = '') -> str:
        return f"{url.getRoot(APPNAME)}{url.projects.coreModTransInvite(self.get_id)}{url.getMessageQuery(alert,error,success)}"

    @property
    def get_link(self):
        return self.getLink()

    @property
    def get_act_link(self):
        return f"{url.getRoot(APPNAME)}{url.projects.coreModTransInviteAct(self.get_id)}"

    def accept(self):
        if self.expired:
            return False
        if self.resolved:
            return False
        self.resolve()
        done = self.coreproject.transfer_moderation_to(self.receiver)
        if not done:
            self.unresolve()
        return done

    def decline(self):
        return super(CoreModerationTransferInvitation, self).decline()


class ProjectModerationTransferInvitation(Invitation):
    project = models.OneToOneField(
        Project, on_delete=models.CASCADE, related_name='mod_invitation_verifiedproject')
    sender = models.ForeignKey(f'{PEOPLE}.Profile', on_delete=models.CASCADE,
                               related_name='mod_verifiedtransfer_invitation_sender')
    receiver = models.ForeignKey(f'{PEOPLE}.Profile', on_delete=models.CASCADE,
                                 related_name='mod_verifiedtransfer_invitation_receiver')

    class Meta:
        unique_together = ('sender', 'receiver', 'project')

    def getLink(self, success: str = '', error: str = '', alert: str = '') -> str:
        return f"{url.getRoot(APPNAME)}{url.projects.verifiedModTransInvite(self.get_id)}{url.getMessageQuery(alert,error,success)}"

    @property
    def get_link(self):
        return self.getLink()

    @property
    def get_act_link(self):
        return f"{url.getRoot(APPNAME)}{url.projects.verifiedModTransInviteAct(self.get_id)}"

    def accept(self):
        if self.expired:
            return False
        if self.resolved:
            return False
        self.resolve()
        done = self.project.transfer_moderation_to(self.receiver)
        if not done:
            self.unresolve()
        return done

    def decline(self):
        return super(ProjectModerationTransferInvitation, self).decline()


class VerProjectDeletionRequest(Invitation):
    project = models.OneToOneField(
        Project, on_delete=models.CASCADE, related_name='deletion_request_project')
    sender = models.ForeignKey(
        f'{PEOPLE}.Profile', on_delete=models.CASCADE, related_name='deletion_request_sender')
    receiver = models.ForeignKey(
        f'{PEOPLE}.Profile', on_delete=models.CASCADE, related_name='deletion_request_receiver')

    class Meta:
        unique_together = ('sender', 'receiver', 'project')

    def getLink(self, success: str = '', error: str = '', alert: str = '') -> str:
        return f"{url.getRoot(APPNAME)}{url.projects.verDeletionRequest(self.get_id)}{url.getMessageQuery(alert,error,success)}"

    @property
    def get_link(self):
        return self.getLink()

    @property
    def get_act_link(self):
        return f"{url.getRoot(APPNAME)}{url.projects.verDeletionRequestAct(self.get_id)}"

    def accept(self):
        if self.expired:
            return False
        if self.resolved:
            return False
        self.resolve()
        done = self.project.moveToTrash()
        if not done:
            self.unresolve()
        return done

    def decline(self):
        self.delete()
        return True


class CoreProjectDeletionRequest(Invitation):
    coreproject = models.OneToOneField(
        CoreProject, on_delete=models.CASCADE, related_name='deletion_request_coreproject')
    sender = models.ForeignKey(f'{PEOPLE}.Profile', on_delete=models.CASCADE,
                               related_name='deletion_coreproject_request_sender')
    receiver = models.ForeignKey(f'{PEOPLE}.Profile', on_delete=models.CASCADE,
                                 related_name='deletion_coreproject_request_receiver')

    class Meta:
        unique_together = ('sender', 'receiver', 'coreproject')

    def getLink(self, success: str = '', error: str = '', alert: str = '') -> str:
        return f"{url.getRoot(APPNAME)}{url.projects.coreDeletionRequest(self.get_id)}{url.getMessageQuery(alert,error,success)}"

    @property
    def get_link(self):
        return self.getLink()

    @property
    def get_act_link(self):
        return f"{url.getRoot(APPNAME)}{url.projects.coreDeletionRequestAct(self.get_id)}"

    def accept(self):
        if self.expired:
            return False
        if self.resolved:
            return False
        self.resolve()
        done = self.coreproject.moveToTrash()
        if not done:
            self.unresolve()
        return done

    def decline(self):
        self.delete()
        return True


class FreeProjectVerificationRequest(Invitation):

    freeproject = models.OneToOneField(
        FreeProject, on_delete=models.CASCADE, related_name='free_under_verification_freeproject')
    """freeproject (OneToOneField<FreeProject>): The free project that is under verification"""
    verifiedproject = models.OneToOneField(
        Project, on_delete=models.CASCADE, related_name='free_under_verification_verifiedproject')
    from_free = True
    from_core = False

    class Meta:
        unique_together = ('freeproject', 'verifiedproject')

    def accept(self):
        if self.expired:
            return False
        if self.resolved:
            return False
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

    coreproject = models.OneToOneField(
        CoreProject, on_delete=models.CASCADE, related_name='core_under_verification_coreproject')
    verifiedproject = models.OneToOneField(
        Project, on_delete=models.CASCADE, related_name='core_under_verification_verifiedproject')
    from_free = False
    from_core = True

    class Meta:
        unique_together = ('coreproject', 'verifiedproject')

    def accept(self):
        if self.expired:
            return False
        if self.resolved:
            return False
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
