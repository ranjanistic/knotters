import uuid
from people.models import Profile
from django.db import models
from django.utils import timezone
from main.strings import PEOPLE, url
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

    resultDeclared = models.BooleanField(default=False)

    judges = models.ManyToManyField(Profile, through='JudgePanel')

    def __str__(self) -> str:
        return self.title

    def getBanner(self) -> str:
        return f"{MEDIA_URL}{str(self.banner)}"

    def getLink(self, error='', success='', alert='') -> str:
        """
        Link to competition profile page
        """
        if error:
            error = f"?e={error}"
        elif alert:
            success = f"?a={alert}"
        elif success:
            success = f"?s={success}"
        return f"/{url.COMPETE}{self.id}{success}{error}"

    def isActive(self) -> bool:
        """
        Whether the competition is active or not, depending on endAt time.
        """
        return self.endAt > timezone.now()

    def secondsLeft(self) -> int:
        time = timezone.now()
        if time > self.endAt:
            return 0
        diff = self.endAt - time
        return diff.seconds

    def isJudge(self,profile:Profile) -> bool:
        if not self.judges: return False
        if profile in self.judges.all(): return True
        return False


class JudgePanel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    competition = models.ForeignKey(Competition, related_name='judging_competition', on_delete=models.CASCADE)
    judge = models.ForeignKey(Profile, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return self.competition.title
    class Meta:
        unique_together = ("competition", "judge")


class Submission(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    competition = models.ForeignKey(Competition, on_delete=models.PROTECT)
    members = models.ManyToManyField(
        Profile, through='Relation', related_name='submission_members')
    repo = models.URLField(max_length=1000, blank=True, null=True)
    submitted = models.BooleanField(default=False)
    createdOn = models.DateTimeField(auto_now=False, default=timezone.now)
    modifiedOn = models.DateTimeField(auto_now=False, default=timezone.now)
    submitOn = models.DateTimeField(auto_now=False, blank=True, null=True)
    valid = models.BooleanField(default=True)
    late = models.BooleanField(default=False)

    def __str__(self) -> str:
        return f"{self.competition.title} - {self.id}"

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

        return len(self.getMembers())

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

    def canInvite(self) -> bool:
        return self.totalMembers() < 5 and not self.submitted

    def getRepo(self) -> bool:
        return self.repo if self.repo else ''

    def lateSubmission(self) -> bool:
        return not self.competition.isActive() and not self.submitted


class Result(models.Model):
    class Meta:
        unique_together = (("competition", "rank"),
                           ("competition", "submission"))

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    competition = models.ForeignKey(Competition, on_delete=models.PROTECT)
    submission = models.OneToOneField(Submission, on_delete=models.PROTECT)
    rank = models.IntegerField()

    def rankSuptext(self) -> str:
        rank = self.rank
        rankstr = str(rank)
        if rank == 1:
            return 'st'
        elif rank == 2:
            return 'nd'
        elif rank == 3:
            return 'rd'
        else:
            if rank > 9:
                if rankstr[len(rankstr) - 2] == "1":
                    return "th"
                return self.rankSuptext(int(rankstr[rankstr.length - 1]))
            else:
                return "th"


class Relation(models.Model):
    class Meta:
        unique_together = (("profile", "submission"))
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profile = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name='submission_profile')
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE)
    confirmed = models.BooleanField(default=False)
