from django.db import models
import uuid

def serviceImagePath(instance,filename):
    return 'service/{}/'.format(str(instance.name))+'/{}'.format(filename)

class Service(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50,null=False,blank=False)
    url = models.CharField(max_length=500,null=False,blank=False)
    image = models.FileField(upload_to=serviceImagePath,null=True,blank=True,max_length=500)
    description = models.CharField(max_length=1500,null=False,blank=False)

    def __str__(self):
        return self.name
