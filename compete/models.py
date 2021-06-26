import uuid
from people.models import Profile
from django.db import models
from django.utils import timezone
from main.strings import PEOPLE
from main.settings import MEDIA_URL
from .apps import APPNAME


def competeBannerPath(instance, filename):
    fileparts = filename.split('.')
    return f"{APPNAME}/banners/{instance.id}.{fileparts[len(fileparts)-1]}"


def defaultBannerPath():
    return f"{APPNAME}/default.png"


class Competition(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=1000, blank=False, null=False)
    tagline = models.CharField(max_length=2000, blank=False, null=False)
    shortdescription = models.CharField(
        max_length=5000, blank=False, null=False)
    description = models.CharField(max_length=20000, blank=False, null=False)
    banner = models.ImageField(
        upload_to=competeBannerPath, default=defaultBannerPath)

    startAt = models.DateTimeField(auto_now=False, default=timezone.now)
    endAt = models.DateTimeField(auto_now=False, default=timezone.now)
    active = models.BooleanField(default=False)

    def __str__(self) -> str:
        return self.title

    def getBanner(self) -> str:
        return f"{MEDIA_URL}{str(self.banner)}"


class Submission(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    competition = models.ForeignKey("Competition", on_delete=models.PROTECT)
    members = models.ManyToManyField(Profile, through='Relation')
    repo = models.URLField(max_length=1000, blank=False, null=False)
    submitted = models.BooleanField(default=False)
    createdOn = models.DateTimeField(auto_now=False, default=timezone.now)
    modifiedOn = models.DateTimeField(auto_now=False, default=timezone.now)
    modifiedBy = models.ForeignKey(
        f"{PEOPLE}.Profile", on_delete=models.CASCADE, related_name="modifiedBy")
    submitOn = models.DateTimeField(
        auto_now=False, default=timezone.now, blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.id:
            self.createdOn = timezone.now()
        self.modifiedOn = timezone.now()
        return super(Submission, self).save(*args, **kwargs)


class Result(models.Model):
    class Meta:
        unique_together = (("competition", "rank"))
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    competition = models.ForeignKey("Competition", on_delete=models.PROTECT)
    submission = models.OneToOneField("Submission", on_delete=models.PROTECT)
    rank = models.IntegerField()


class Relation(models.Model):
    class Meta:
        unique_together = (("profile", "submission"))
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profile = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name='submission_profile')
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE)
