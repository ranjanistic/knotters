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
    endAt = models.DateTimeField(auto_now=False)

    def __str__(self) -> str:
        return self.title

    def getBanner(self) -> str:
        return f"{MEDIA_URL}{str(self.banner)}"

    def getLink(self, error='', success='') -> str:
        """
        Link to competition profile page
        """
        if error:
            error = f"?e={error}"
        elif success:
            success = f"?s={success}"
        return f"/{APPNAME}/{self.id}{success}{error}"
    
    def isActive(self)-> bool:
        """
        Whether the competition is active or not, depending on endAt time.
        """
        return self.endAt > timezone.now()


class Submission(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    competition = models.ForeignKey(Competition, on_delete=models.PROTECT)
    members = models.ManyToManyField(
        Profile, through='Relation', related_name='submission_members')
    repo = models.URLField(max_length=1000, blank=True, null=True)
    submitted = models.BooleanField(default=False)
    createdOn = models.DateTimeField(auto_now=False, default=timezone.now)
    modifiedOn = models.DateTimeField(auto_now=False, default=timezone.now)
    modifiedBy = models.ForeignKey(Profile, on_delete=models.PROTECT, related_name="modifiedBy")
    submitOn = models.DateTimeField(auto_now=False, blank=True, null=True)
    valid = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if not self.id:
            self.createdOn = timezone.now()
        self.modifiedOn = timezone.now()
        return super(Submission, self).save(*args, **kwargs)

    def totalMembers(self) -> int:
        """
        All members count regardless of relation confirmation.
        """
        return self.members.all().count()

    def totalActiveMembers(self) -> int:
        """
        All members count with relation confirmed.
        """
        return self.getMembers().count()


    def getMembers(self) -> list:
        """
        List of members whomst relation to this submission is confirmed.
        """
        members = []
        relations = Relation.objects.filter(submission=self)
        for member in self.members.all():
            relation = relations.get(profile=member)
            if relation.confirmed:
                members.append(member)
        return members

    def getInvitees(self) -> list:
        """
        List of members whomst relation to this submission is not confirmed.
        """
        invitees = []
        relations = Relation.objects.filter(submission=self)
        for member in self.members.all():
            relation = relations.get(profile=member)
            if not relation.confirmed:
                invitees.append(member)
        return invitees


class Result(models.Model):
    class Meta:
        unique_together = (("competition", "rank"))
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    competition = models.ForeignKey(Competition, on_delete=models.PROTECT)
    submission = models.OneToOneField(Submission, on_delete=models.PROTECT)
    rank = models.IntegerField()


class Relation(models.Model):
    class Meta:
        unique_together = (("profile", "submission"))
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profile = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name='submission_profile')
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE)
    confirmed = models.BooleanField(default=False)
