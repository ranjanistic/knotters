from .apps import APPNAME
from django.db.models import Sum
import uuid
from people.models import Profile
from django.db import models
from django.utils import timezone
from people.models import Topic
from moderation.models import Moderation
from main.strings import url
from main.settings import MEDIA_URL


def competeBannerPath(instance, filename):
    fileparts = filename.split('.')
    return f"{url.COMPETE}banners/{instance.id}.{fileparts[len(fileparts)-1]}"


def defaultBannerPath():
    return f"{url.COMPETE}default.png"


class Competition(models.Model):
    """
    A competition.
    """
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

    judges = models.ManyToManyField(
        Profile, through='CompetitionJudge', default=[])

    topics = models.ManyToManyField(Topic, through='CompetitionTopic', default=[])

    eachTopicMaxPoint = models.IntegerField(default=10)

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

    def participationLink(self) -> str:
        return f"/{url.COMPETE}participate/{self.id}"

    def isActive(self) -> bool:
        """
        Whether the competition is active or not, depending on startAt & endAt.
        """
        now = timezone.now()
        return self.startAt <= now < self.endAt

    def isUpcoming(self) -> bool:
        """
        Whether the competition is upcoming or not, depending on startAt.
        """
        return self.startAt > timezone.now()

    def isHistory(self) -> bool:
        """
        Whether the competition is history or not, depending on endAt.
        """
        return self.endAt <= timezone.now()

    def secondsLeft(self) -> int:
        """
        Total seconds left in this competition from the instantaneous time this method is invoked.
        """
        time = timezone.now()
        if time >= self.endAt:
            return 0
        diff = self.endAt - time
        return diff.seconds

    def getTopics(self) -> list:
        """
        List of topics of this competition
        """
        return self.topics.all()

    def totalTopics(self) -> list:
        """
        Count total topics of this competition
        """
        return len(self.topics.all())

    def isModerator(self, profile: Profile) -> bool:
        """
        Whether the given profile is assigned as moderator of this competition or not.
        """
        try:
            Moderation.objects.filter(
                type=APPNAME, competition=self, moderator=profile).order_by("-requestOn")[0]
            return True
        except:
            return False

    def moderated(self) -> bool:
        """
        Whether this competition has been moderated by moderator or not.
        Being moderated indicates that the valid submissions in this competition are ready to be marked.
        """
        try:
            Moderation.objects.filter(
                type=APPNAME, competition=self, resolved=True).order_by("-requestOn")[0]
            return True
        except:
            return False

    def isJudge(self, profile: Profile) -> bool:
        """
        Whether the given profile is a judge in this comopetition or not.
        """
        if not self.judges:
            return False
        if profile in self.judges.all():
            return True
        return False

    def getJudges(self) -> list:
        """
        List of judges in this competition
        """
        return [] if not self.judges else self.judges.all()

    def totalJudges(self) -> int:
        """
        Total judges in this competition
        """
        return len(self.getJudges())

    def getJudgementLink(self, error='', alert='') -> str:
        try:
            return (Moderation.objects.filter(
                type=APPNAME, competition=self).order_by("-requestOn").first()).getLink(error=error, alert=alert)
        except:
            return ''

    def isParticipant(self, profile: Profile) -> bool:
        """
        Checks whether the given profile is a participant (confirmed or unconfirmed) in this competition or not.
        """
        try:
            Submission.objects.get(competition=self, members=profile)
            return True
        except:
            return False

    def getMaxScore(self) -> int:
        """
        Calculated maximum points allowed in this competition for each submission, which depends on topics, eachTopicMaxPoint, and judges.
        """
        return self.topics.count() * self.eachTopicMaxPoint * self.totalJudges()

    def getSubmissions(self) -> list:
        """
        Returns a list of all submissions of this competition irrespective of validity.
        """
        try:
            return Submission.objects.filter(competition=self).order_by('submitOn')
        except:
            return []

    def totalSubmissions(self) -> int:
        """
        Count all submissions irrespective of their validity.
        """
        try:
            return len(self.getSubmissions())
        except:
            return 0

    def getValidSubmissions(self) -> list:
        """
        Returns a list of valid submissions of this competition.
        """
        try:
            return Submission.objects.filter(competition=self, valid=True).order_by('submitOn')
        except:
            return []

    def totalValidSubmissions(self) -> int:
        """
        Count submissions with valid = True. By default all submissions are valid, unless marked invalid by the assigned competition moderator.
        """
        try:
            return len(self.getValidSubmissions())
        except:
            return 0

    def submissionPointsLink(self) -> str:
        return f"/{url.COMPETE}submissionpoints/{self.id}"

    def allSubmissionsMarkedByJudge(self, judge: Profile) -> bool:
        """
        Whether all valid submissions of this competitions have been marked (topic point) by given judge or not.
        """
        try:
            subslist = self.getValidSubmissions()
            judgeTopicPointsCount = SubmissionTopicPoint.objects.filter(
                submission__in=subslist, judge=judge).count()
            return judgeTopicPointsCount == len(subslist)*self.totalTopics()
        except:
            return False

    def allSubmissionsMarked(self) -> bool:
        """
        Whether all valid submissions of this competitions have been marked (topic point) by all judges or not.
        """
        try:
            subslist = self.getValidSubmissions()
            topicPointsCount = SubmissionTopicPoint.objects.filter(
                submission__in=subslist).count()
            return topicPointsCount == len(subslist)*self.totalTopics()*self.totalJudges()
        except:
            return False

    def countJudgesWhoMarkedSumissions(self) -> int:
        """
        Count judges of this competition who have submitted topic points of all valid submissions.
        """
        judges = self.getJudges()
        count = 0
        for judge in judges:
            if self.allSubmissionsMarkedByJudge(judge):
                count = count+1
        return count

    def declareResultsLink(self) -> str:
        return f"/{url.COMPETE}declareresults/{self.id}"

    def declareResults(self) -> bool:
        """
        Declares results by aggregating each valid submission's topic point and calculates final score to create Result for each submission.
        Also sets resultDeclared = True
        Invoking this method should be considered as final step of a competition cycle.
        """
        try:
            if not self.allSubmissionsMarked():
                return False
            subs = self.getValidSubmissions()
            results = SubmissionTopicPoint.objects.filter(submission__in=subs).values(
                'submission').annotate(totalPoints=Sum('points')).order_by('-totalPoints')
            
            resultsList = []

            rank = 1
            for res in results:
                subm = None
                for sub in subs:
                    if str(res['submission']) == str(sub.id):
                        subm = sub
                if subm:
                    resultsList.append(
                        Result(
                            competition=self,
                            submission=subm,
                            points=res['totalPoints'],
                            rank=rank
                        )
                    )
                rank=rank+1
            obj = Result.objects.bulk_create(resultsList)
            if not obj: return False
            self.resultDeclared = True
            self.save()
            return True
        except Exception as e:
            print(e)
            return False


class CompetitionJudge(models.Model):
    """
    Judge of a competition
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    competition = models.ForeignKey(
        Competition, related_name='judging_competition', on_delete=models.PROTECT)
    judge = models.ForeignKey(Profile, on_delete=models.PROTECT)

    def __str__(self) -> str:
        return self.competition.title

    class Meta:
        unique_together = ("competition", "judge")


class CompetitionTopic(models.Model):
    """
    Topic assigned to a compeition for topic marking of submission by judge after competition ends.
    """
    class Meta:
        unique_together = ("competition", "topic")
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    competition = models.ForeignKey(
        Competition, on_delete=models.CASCADE, related_name='competition_topic')
    topic = models.ForeignKey(
        Topic, on_delete=models.CASCADE, related_name='topic_competition')

    def __str__(self) -> str:
        return self.competition.title


class Submission(models.Model):
    """
    Submission of a competition, including participant(s).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    competition = models.ForeignKey(Competition, on_delete=models.PROTECT)
    members = models.ManyToManyField(
        Profile, through='SubmissionParticipant', related_name='submission_members')
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

    def saveLink(self) -> str:
        """
        URL endpoint to save repo field value.
        """
        return f"/{url.COMPETE}save/{self.competition.id}/{self.id}"

    def totalMembers(self) -> int:
        """
        All members count, regardless of membership confirmation.
        """
        return self.members.all().count()

    def isMember(self, profile: Profile) -> bool:
        """
        Checks if provided profile object is a confirmed memeber or not.

        :profile: The profile object to be looked for.
        """
        try:
            SubmissionParticipant.objects.get(
                submission=self, profile=profile, confirmed=True)
            return True
        except:
            return False

    def getMembers(self) -> list:
        """
        List of members whomst membership with this submission is confirmed.
        """
        members = []
        relations = SubmissionParticipant.objects.filter(submission=self)
        for member in self.members.all():
            relation = relations.get(profile=member)
            if relation.confirmed:
                members.append(member)
        return members

    def totalActiveMembers(self) -> int:
        """
        All members count with confirmed membership.
        """
        return len(self.getMembers())

    def memberOrMembers(self) -> str:
        return 'member' if self.totalActiveMembers() == 1 else 'members'

    def isInvitee(self, profile: Profile) -> bool:
        """
        Whether the given profile has been invited in this submission or not.
        """
        try:
            SubmissionParticipant.objects.get(
                submission=self, profile=profile, confirmed=False)
            return True
        except:
            return False

    def getInvitees(self) -> list:
        """
        List of members whomst relation to this submission is not confirmed.
        """
        invitees = []
        relations = SubmissionParticipant.objects.filter(submission=self)
        for member in self.members.all():
            relation = relations.get(profile=member)
            if not relation.confirmed:
                invitees.append(member)
        return invitees

    def canInvite(self) -> bool:
        """
        Whether this submission can invite more participants or not, 
        depending on current totalmembers, submission status & competition active status.
        """
        return self.totalMembers() < 5 and not self.submitted and self.competition.isActive()

    def getRepo(self) -> bool:
        """
        Repo or submission link.
        """
        return self.repo if self.repo else ''

    def submittingLate(self) -> bool:
        """
        Submitting late or not.
        NOTE: This method only represents 'late' status of submission before it has been submitted. After submission, the response of this method must not be considered reliable, instead the 'late' field should be used.
        """
        return self.competition.isHistory() and not self.submitted

    def pointedTopicsByJudge(self, judge: Profile):
        """
        Count of topics pointed by given judge for this submission.
        """
        return SubmissionTopicPoint.objects.filter(submission=self, judge=judge).count()


class SubmissionParticipant(models.Model):
    """
    For participant member in a submission in a competition.
    """
    class Meta:
        unique_together = (("profile", "submission"))
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profile = models.ForeignKey(
        Profile, on_delete=models.PROTECT, related_name='submission_profile')
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE)
    confirmed = models.BooleanField(default=False)


class SubmissionTopicPoint(models.Model):
    """
    For each topic, points marked by each judge for each submission in a competition.
    """
    class Meta:
        unique_together = ("submission", "topic", "judge")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    submission = models.ForeignKey(Submission, on_delete=models.PROTECT)
    topic = models.ForeignKey(Topic, on_delete=models.PROTECT)
    judge = models.ForeignKey(Profile, on_delete=models.PROTECT)
    points = models.IntegerField(default=0)

    def __str__(self) -> str:
        return f"{self.submission}"


class Result(models.Model):
    """
    Rank and total points obtained by a submission in a competition.
    """
    class Meta:
        unique_together = (("competition", "rank"),
                           ("competition", "submission"))

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    competition = models.ForeignKey(Competition, on_delete=models.PROTECT)
    submission = models.OneToOneField(Submission, on_delete=models.PROTECT)
    points = models.IntegerField(default=0)
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

    def __str__(self) -> str:
        return f"{self.competition} - {self.rank}{self.rankSuptext()}"
