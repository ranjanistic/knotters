from django.db import models
import uuid

class Service(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50,null=False,blank=False)
    url = models.CharField(max_length=500,null=False,blank=False)
    imgsrc = models.CharField(max_length=500,null=False,blank=False)
    description = models.CharField(max_length=1500,null=False,blank=False)

    def __str__(self):
        return self.name
