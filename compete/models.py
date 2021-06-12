from people.models import User
from django.db import models
import uuid
from django.utils import timezone
from main.strings import PEOPLE
from .methods import competeBannerPath, defaultBannerPath

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
        upload_to=competeBannerPath, default=defaultBannerPath)

    active = models.BooleanField(default=False)

    def __str__(self):
        return self.title

    def getBanner(self):
        return f"/media/{str(self.banner)}"

class Submission(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    competition = models.ForeignKey("Competition", on_delete=models.PROTECT)
    members = models.ManyToManyField(User)
    repo = models.URLField(max_length=1000, blank=False, null=False)
    submitted = models.BooleanField(default=False)
    createdOn = models.DateTimeField(auto_now=False, default=timezone.now)
    modifiedOn = models.DateTimeField(auto_now=False, default=timezone.now)
    modifiedBy = models.ForeignKey(
        f"{PEOPLE}.User", on_delete=models.CASCADE, related_name="modifiedBy")
    submitOn = models.DateTimeField(auto_now=False, default=timezone.now)

    def save(self, *args, **kwargs):
        if not self.id:
            self.createdOn = timezone.now()
        self.modifiedOn = timezone.now()
        return super(Submission, self).save(*args, **kwargs)


class Result(models.Model):
    class Meta:
        unique_together = (("competition","rank"),)
    id= models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    competition = models.ForeignKey("Competition", on_delete=models.PROTECT)
    submission = models.OneToOneField("Submission", on_delete=models.PROTECT)
    rank = models.IntegerField()
