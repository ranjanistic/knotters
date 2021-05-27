from project.models import User
from django.db import models
import uuid
from django.utils import timezone

def competeBannerPath(instance, filename):
    return 'competitions/{}/'.format(str(instance.id))+'/{}'.format(filename)


class Competition(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=1000, blank=False,
                             null=False, default="A new competition")
    tagline = models.CharField(
        max_length=2000, blank=False, null=False, default="The tagline")
    shortdescription = models.CharField(
        max_length=5000, blank=False, null=False, default="Short desc.")
    description = models.CharField(max_length=20000, blank=False, null=False,
                                   default="A long description for reader to read and understand what this competition is about.")
    banner = models.ImageField(
        upload_to=competeBannerPath, default="/competitions/default.png")
    
    active = models.BooleanField(default=False)


class Submission(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    competition = models.ForeignKey("Competition", on_delete=models.CASCADE)
    submitter = models.ForeignKey("project.User", on_delete=models.CASCADE)
    # members = models.ManyToManyField(User)
    repo = models.URLField(max_length=1000, blank=False,null=False)
    submitted = models.BooleanField(default=False)
    submitOn = models.DateTimeField(auto_now=False, default=timezone.now)