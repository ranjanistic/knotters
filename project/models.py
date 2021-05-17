from django.db import models
import uuid

def projectImagePath(instance,filename):
    return 'projects/{}/'.format(str(instance.id))+'/{}'.format(filename)

class Tag(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=1000,null=False,blank=False)

    def __str__(self):
        return self.name

class Project(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50,null=False,blank=False)
    url = models.CharField(max_length=500,null=True,blank=True)
    image = models.FileField(upload_to=projectImagePath,null=True,blank=True,max_length=500)
    reponame = models.URLField(max_length=500,null=False,blank=False)
    githuburl = models.URLField(max_length=500,null=True,blank=True)
    description = models.CharField(max_length=5000,null=False,blank=False)
    tags = models.ManyToManyField(Tag)
    def __str__(self):
        return self.name

class Moderator(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    projects = models.ManyToManyField(Project)