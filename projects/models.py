import uuid
from django.db import models
from django.utils import timezone
from main.strings import code, PEOPLE, project
from main.methods import maxLengthInList
from main.strings import MODERATION
from main.settings import MEDIA_URL
from .apps import APPNAME

def projectImagePath(instance, filename):
    return f'{APPNAME}/{instance.id}/{filename}'

def defaultImagePath():
    return f'/{APPNAME}/default.png'


class Tag(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=1000, null=False, blank=False,unique=True)

    def __str__(self):
        return self.name


class Category(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=1000, null=False, blank=False,unique=True)

    def __str__(self):
        return self.name

class Project(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50, null=False, blank=False)
    url = models.CharField(max_length=500, null=True, blank=True)
    image = models.FileField(upload_to=projectImagePath,
                             max_length=500, default=defaultImagePath)
    reponame = models.CharField(
        max_length=500, unique=True, null=False, blank=False)
    description = models.CharField(max_length=5000, null=False, blank=False)
    tags = models.ManyToManyField(Tag,through='Relation',default=[])
    status = models.CharField(choices=project.PROJECTSTATESCHOICE, max_length=maxLengthInList(project.PROJECTSTATES), default=code.MODERATION)
    createdOn = models.DateTimeField(auto_now=False, default=timezone.now)
    approvedOn = models.DateTimeField(auto_now=False, blank=True,null=True)
    modifiedOn = models.DateTimeField(auto_now=False, default=timezone.now)
    creator = models.ForeignKey(f"{PEOPLE}.User", on_delete=models.PROTECT)
    category = models.ForeignKey(Category, on_delete=models.PROTECT)

    def __str__(self):
        return self.name
    
    def getLink(self, success='', error=''):
        if error:
            error = f"?e={error}"
        elif success:
            success = f"?s={success}"
        if self.status == code.REJECTED:
            return f"/{MODERATION}/{APPNAME}/{self.id}{error}{success}"
        return f"/{APPNAME}/profile/{self.reponame}{error}{success}"

    def getDP(self):
        return f"{MEDIA_URL}{str(self.image)}"

class Relation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('project','tag')

    def __str__(self) -> str:
        return f"{self.project.name} + {self.tag.name}"