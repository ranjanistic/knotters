import uuid
from django.db import models
from django.utils import timezone
from main.env import PUBNAME
from main.settings import MEDIA_URL
from main.methods import maxLengthInList
from main.strings import Code, url, PEOPLE, project, message
from moderation.models import Moderation
from .apps import APPNAME


def projectImagePath(instance, filename):
    fileparts = filename.split('.')
    return f"{APPNAME}/avatars/{str(instance.id).replace('-','')}.{fileparts[len(fileparts)-1]}"


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
    tags = models.ManyToManyField(Tag, through='Relation', default=[])

    def __str__(self):
        return self.name

    def getID(self) -> str:
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
    tags = models.ManyToManyField(Tag, through='Relation', default=[])
    status = models.CharField(choices=project.PROJECTSTATESCHOICES, max_length=maxLengthInList(
        project.PROJECTSTATES), default=Code.MODERATION)
    createdOn = models.DateTimeField(auto_now=False, default=timezone.now)
    approvedOn = models.DateTimeField(auto_now=False, blank=True, null=True)
    modifiedOn = models.DateTimeField(auto_now=False, default=timezone.now)
    creator = models.ForeignKey(f"{PEOPLE}.Profile", on_delete=models.PROTECT)
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    migrated = models.BooleanField(
        default=False, help_text='Indicates whether this project was created by someone whose account was deleted.')
    acceptedTerms = models.BooleanField(default=True)

    trashed = models.BooleanField(
        default=False, help_text="Deleted for creator, used when rejected.")

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
        if error and message.isValid(error):
            error = f"?e={error}"
        elif alert and message.isValid(alert):
            alert = f"?a={alert}"
        elif success and message.isValid(success):
            success = f"?s={success}"
        if self.status != Code.APPROVED:
            return (Moderation.objects.filter(project=self, type=APPNAME, status__in=[
                Code.REJECTED, Code.MODERATION]).order_by('-respondOn').first()).getLink(alert=alert, error=error)
        return f"{url.getRoot(APPNAME)}{url.projects.profile(reponame=self.reponame)}{url.getMessageQuery(alert,error,success)}"

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
        return (Moderation.objects.filter(project=self, type=APPNAME).order_by('requestOn').first()).getLink()

    def moderationRetriesLeft(self) -> int:
        if self.status != Code.APPROVED:
            try:
                mods = Moderation.objects.filter(
                    type=APPNAME, project=self).count()
                return 3 - mods
            except:
                return 3
        return 0

    def canRetryModeration(self) -> bool:
        try:
            return self.moderationRetriesLeft() > 0
        except:
            return True


class Relation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, null=True, blank=True)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE,
                            related_name='project_tag')
    topic = models.ForeignKey(f'{PEOPLE}.Topic', on_delete=models.CASCADE,
                              null=True, blank=True, related_name='project_topic')
    category = models.ForeignKey(Category, on_delete=models.CASCADE,
                                 null=True, blank=True, related_name='project_category')

    class Meta:
        unique_together = (('project', 'tag'),
                           ('topic', 'tag'), ('category', 'tag'))
