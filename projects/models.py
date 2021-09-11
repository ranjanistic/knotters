import uuid
from deprecated import deprecated
from django.db import models
from django.utils import timezone
from main.env import BOTMAIL, MAILUSER, PUBNAME
from main.settings import MEDIA_URL
# from people.models import Profile
from main.methods import addMethodToAsyncQueue, maxLengthInList
from main.strings import Code, url, PEOPLE, project, MANAGEMENT, DOCS
from moderation.models import Moderation
from .apps import APPNAME


class Tag(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=1000, null=False,
                            blank=False, unique=True)

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
        return Project.objects.filter(tags=self).count()

    @property
    def getProjects(self):
        return Project.objects.filter(tags=self)

    @property
    def totalCategories(self):
        return Category.objects.filter(tags=self).count()

    @property
    def getCategories(self):
        return Category.objects.filter(tags=self)


class Category(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=1000, null=False,
                            blank=False, unique=True)
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
    def totalTags(self):
        return self.tags.count()

    @property
    def getTags(self):
        return self.tags.all()

    @property
    def totalProjects(self):
        return Project.objects.filter(category=self).count()

    @property
    def getProjects(self):
        return Project.objects.filter(category=self)

    @property
    def getProjectsLimited(self):
        return Project.objects.filter(category=self)[0:50]

    @property
    def isDeletable(self):
        return self.totalProjects == 0


class CategoryTag(models.Model):
    class Meta:
        unique_together = ('category', 'tag')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)


class License(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50)
    keyword = models.CharField(max_length=80, null=True, blank=True,
                               help_text='The license keyword, refer https://docs.github.com/en/github/creating-cloning-and-archiving-repositories/creating-a-repository-on-github/licensing-a-repository#searching-github-by-license-type')
    description = models.CharField(max_length=1000)
    content = models.CharField(max_length=300000, null=True, blank=True)
    public = models.BooleanField(default=False)
    default = models.BooleanField(default=False)
    creator = models.ForeignKey(f"{PEOPLE}.Profile", on_delete=models.PROTECT)

    def __str__(self):
        return self.name

    def getID(self):
        return self.id.hex

    def getLink(self):
        return f'{url.getRoot(APPNAME)}{url.projects.license(id=self.getID())}'

    def isCustom(self):
        return self.creator.getEmail() != BOTMAIL

def projectImagePath(instance, filename):
    fileparts = filename.split('.')
    return f"{APPNAME}/avatars/{str(instance.getID())}.{fileparts[len(fileparts)-1]}"

def defaultImagePath():
    return f"{APPNAME}/default.png"


class Project(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50, null=False, blank=False)
    url = models.CharField(max_length=500, null=True, blank=True)
    image = models.ImageField(upload_to=projectImagePath,
                              max_length=500, default=defaultImagePath, null=True, blank=True)
    reponame = models.CharField(
        max_length=500, unique=True, null=False, blank=False)
    description = models.CharField(max_length=5000, null=False, blank=False)
    status = models.CharField(choices=project.PROJECTSTATESCHOICES, max_length=maxLengthInList(
        project.PROJECTSTATES), default=Code.MODERATION)
    createdOn = models.DateTimeField(auto_now=False, default=timezone.now)
    approvedOn = models.DateTimeField(auto_now=False, blank=True, null=True)
    modifiedOn = models.DateTimeField(auto_now=False, default=timezone.now)
    creator = models.ForeignKey(f"{PEOPLE}.Profile", on_delete=models.PROTECT)
    migrated = models.BooleanField(
        default=False, help_text='Indicates whether this project was created by someone whose account was deleted.')
    acceptedTerms = models.BooleanField(default=True)
    license = models.ForeignKey(License, on_delete=models.PROTECT)
    trashed = models.BooleanField(
        default=False, help_text="Deleted for creator, can be used when rejected.")

    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    tags = models.ManyToManyField(Tag, through='ProjectTag', default=[])
    topics = models.ManyToManyField(
        f'{PEOPLE}.Topic', through='ProjectTopic', default=[])

    def __str__(self):
        return self.name

    @property
    def get_id(self) -> str:
        return self.id.hex

    def getID(self) -> str:
        return self.get_id

    def save(self, *args, **kwargs):
        try:
            previous = Project.objects.get(id=self.id)
            if previous.image != self.image:
                if previous.image != defaultImagePath():
                    previous.image.delete(False)
        except:
            pass
        super(Project, self).save(*args, **kwargs)

    def getLink(self, success: str = '', error: str = '', alert: str = '') -> str:
        try:
            if self.status != Code.APPROVED:
                return (Moderation.objects.filter(project=self, type=APPNAME, status__in=[Code.REJECTED, Code.MODERATION]).order_by('-requestOn').first()).getLink(alert=alert, error=error)
            return f"{url.getRoot(APPNAME)}{url.projects.profile(reponame=self.reponame)}{url.getMessageQuery(alert,error,success)}"
        except:
            return f"{url.getRoot(APPNAME)}{url.getMessageQuery(alert,error,success)}"

    def getDP(self) -> str:
        return f"{MEDIA_URL}{str(self.image)}"

    def isApproved(self) -> bool:
        return self.status == Code.APPROVED

    def isLive(self) -> bool:
        return self.isApproved()

    def rejected(self) -> bool:
        return self.status == Code.REJECTED

    def underModeration(self) -> bool:
        return self.status == Code.MODERATION

    def getRepoLink(self) -> str:
        return f"https://github.com/{PUBNAME}/{self.reponame}"

    @property
    def moderator(self):
        mod = Moderation.objects.filter(project=self, type=APPNAME, status__in=[
                                        Code.APPROVED, Code.MODERATION]).order_by('-requestOn').first()
        return None if not mod else mod.moderator

    def getModerator(self) -> models.Model:
        if not self.isApproved():
            return None
        mod = Moderation.objects.filter(
            project=self, type=APPNAME, status=Code.APPROVED, resolved=True).order_by('-respondOn').first()
        return None if not mod else mod.moderator

    def getModLink(self) -> str:
        try:
            return (Moderation.objects.filter(project=self, type=APPNAME).order_by('requestOn').first()).getLink()
        except:
            return str()

    def moderationRetriesLeft(self) -> int:
        if self.status != Code.APPROVED:
            return 3 - Moderation.objects.filter(type=APPNAME, project=self).count()
        return 0

    def canRetryModeration(self) -> bool:
        return self.status != Code.APPROVED and self.moderationRetriesLeft() > 0 and not self.trashed

    def getTrashLink(self) -> str:
        return url.projects.trash(self.getID())

    def moveToTrash(self) -> bool:
        if not self.isApproved():
            self.trashed = True
            self.creator.decreaseXP(by=2)
            self.save()
            return self.trashed
        return self.trashed

    def getTopics(self) -> list:
        return self.topics.all()

    def getTopicsData(self):
        return ProjectTopic.objects.filter(project=self)

    def totalTopics(self):
        return self.topics.count()

    def totalTags(self):
        return self.tags.count()

    def editProfileLink(self):
        return f"{url.getRoot(APPNAME)}{url.projects.profileEdit(projectID=self.getID(),section=project.PALLETE)}"
    
    @property
    def assets(self):
        return Asset.objects.filter(project=self)

    @property
    def total_assets(self):
        return Asset.objects.filter(project=self).count()

    @property
    def public_assets(self):
        return Asset.objects.filter(project=self,public=True)

    @property
    def total_public_assets(self):
        return Asset.objects.filter(project=self,public=True).count()



def assetFilePath(instance, filename):
    fileparts = filename.split('.')
    return f"{APPNAME}/assets/{str(instance.project.get_id)}-{str(instance.get_id)}.{fileparts[len(fileparts)-1]}"

class Asset(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project,on_delete=models.CASCADE)
    name = models.CharField(max_length=250, null=False, blank=False)
    file = models.FileField(upload_to=assetFilePath,max_length=500)
    public = models.BooleanField(default=False)

    @property
    def get_id(self):
        return self.id.hex


class ProjectTag(models.Model):
    class Meta:
        unique_together = ('project', 'tag')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, null=True, blank=True)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE,
                            related_name='project_tag')


class ProjectTopic(models.Model):
    class Meta:
        unique_together = ('project', 'topic')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, null=True, blank=True)
    topic = models.ForeignKey(f'{PEOPLE}.Topic', on_delete=models.CASCADE,
                              null=True, blank=True, related_name='project_topic')



class LegalDoc(models.Model):
    class Meta:
        unique_together = ('name', 'pseudonym')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=1000)
    pseudonym = models.CharField(max_length=1000, unique=True)
    about = models.CharField(max_length=100, null=True, blank=True)
    content = models.CharField(max_length=100000)
    icon = models.CharField(max_length=20, default='policy')
    contactmail = models.CharField(max_length=30, default=BOTMAIL)
    lastUpdate = models.DateTimeField(
        auto_now=False, default=timezone.now, editable=False)
    effectiveDate = models.DateTimeField(auto_now=False, default=timezone.now)

    def save(self, *args, **kwargs):
        if self.id:
            if LegalDoc.objects.filter(id=self.id).exists():
                if self.content != (LegalDoc.objects.get(id=self.id)).content:
                    self.lastUpdate = timezone.now()
                    addMethodToAsyncQueue(f"{MANAGEMENT}.mailers.alertLegalUpdate", self.name, self.getLink())
        super(LegalDoc, self).save(*args, **kwargs)

    def getLink(self):
        return f"{url.getRoot(DOCS)}{url.docs.type(self.pseudonym)}"
