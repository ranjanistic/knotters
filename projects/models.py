import uuid
from django.db import models
from django.utils import timezone
from main.env import PUBNAME
from main.settings import MEDIA_URL
from main.methods import maxLengthInList
from main.strings import Code, url, PEOPLE, project
from moderation.models import Moderation
from .apps import APPNAME


def projectImagePath(instance, filename):
    fileparts = filename.split('.')
    return f"{APPNAME}/avatars/{str(instance.getID())}.{fileparts[len(fileparts)-1]}"


def defaultImagePath():
    return f"{APPNAME}/default.png"


class Tag(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=1000, null=False,
                            blank=False, unique=True)

    def __str__(self):
        return self.name


class Category(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=1000, null=False,
                            blank=False, unique=True)
    tags = models.ManyToManyField(Tag, through='CategoryTag', default=[])

    def __str__(self):
        return self.name

    def getID(self) -> str:
        return self.id.hex


class CategoryTag(models.Model):
    class Meta:
        unique_together = ('category', 'tag')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)

class License(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50)
    description = models.CharField(max_length=1000)
    url = models.URLField(max_length=500, null=True, blank=True)
    content = models.CharField(max_length=300000, null=True, blank=True)
    public = models.BooleanField(default=False)
    default = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    def getID(self):
        return self.id.hex


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

    def getID(self) -> str:
        return self.id.hex

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

    def getTrashLink(self)->str:
        return url.projects.trash(self.getID())

    def moveToTrash(self) -> bool:
        if not self.isApproved():
            self.trashed = True
            self.creator.decreaseXP(by=2)
            self.save()
            return self.trashed
        return self.trashed


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
