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
    image = models.FileField(upload_to=projectImagePath,max_length=500, default='/projects/default.png')
    reponame = models.CharField(max_length=500,unique=True,null=False,blank=False)
    description = models.CharField(max_length=5000,null=False,blank=False)
    tags = models.ManyToManyField(Tag)
    creator = models.ForeignKey("people.User", on_delete=models.CASCADE)
    def __str__(self):
        return self.name
