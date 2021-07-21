import uuid
from django.db import models
from django.db.models import Sum
from people.models import Profile
from django.utils import timezone
from people.models import Topic
from moderation.models import Moderation
from main.strings import url
from main.settings import MEDIA_URL
from .apps import APPNAME


def competeBannerPath(instance, filename):
    fileparts = filename.split('.')
    return f"{APPNAME}/banners/{instance.id}.{fileparts[len(fileparts)-1]}"


def defaultBannerPath():
    return f"{APPNAME}/default.png"


class Competition(models.Model):
    """
    A competition.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=1000, blank=False,
                             null=False, help_text='The competition name.')
    tagline = models.CharField(max_length=2000, blank=False, null=False,
                               help_text='This will be shown in introduction and url previews.')
    shortdescription = models.CharField(
        max_length=5000, blank=False, null=False, help_text='This will be shown in introduction.')
    description = models.CharField(max_length=20000, blank=False, null=False,
                                   help_text='This will be shown in the overview, along with perks, only after the competition as started.')
    banner = models.ImageField(
        upload_to=competeBannerPath, default=defaultBannerPath)

    startAt = models.DateTimeField(auto_now=False, default=timezone.now,
                                   help_text='When this competition will start accepting submissions.')
    endAt = models.DateTimeField(
        auto_now=False, help_text='When this competition will stop accepting submissions.')

    judges = models.ManyToManyField(
        Profile, through='CompetitionJudge', default=[])

    topics = models.ManyToManyField(
        Topic, through='CompetitionTopic', default=[])

    perks = models.CharField(max_length=1000, null=True, blank=True,
                             help_text='Use semi-colon (;) separated perks for each rank, starting from 1st.')
    eachTopicMaxPoint = models.IntegerField(
        default=10, help_text='The maximum points each judge can appoint for each topic to each submission of this competition.')

    taskSummary = models.CharField(max_length=50000)
    taskDetail = models.CharField(max_length=100000)
    taskSample = models.CharField(max_length=10000)

    resultDeclared = models.BooleanField(
        default=False, help_text='Whether the results have been declared or not. Strictly restricted to be edited via server.')

    def __str__(self) -> str:
        return self.title

    def getID(self) -> str:
        return self.id.hex

    def getBanner(self) -> str:
        return f"{MEDIA_URL}{str(self.banner)}"

    def getLink(self, error: str = '', success: str = '', alert: str = '') -> str:
        """
        Link to competition profile page
        """
        return f"{url.getRoot(APPNAME)}{url.compete.compID(compID=self.getID())}{url.getMessageQuery(alert,error,success)}"

    def participationLink(self) -> str:
        return f"{url.getRoot(APPNAME)}{url.compete.participate(compID=self.getID())}"

    def isActive(self) -> bool:
        """
        Whether the competition is active or not, depending on startAt & endAt.
        """
        now = timezone.now()
        return self.startAt <= now < self.endAt and not self.resultDeclared

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
        return diff.total_seconds()

    def getTopics(self) -> list:
        """
        List of topics of this competition
        """
        return self.topics.all()

    def getPerks(self) -> list:
        perks = []
        for p in str(self.perks).split(';'):
            if p:
                perks.append(p)
        return perks

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

    def getModerator(self) -> Profile:
        try:
            mod = Moderation.objects.filter(type=APPNAME, competition=self).order_by(
                "-requestOn").only('moderator')[0]
            return mod.moderator
        except:
            return None

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

    def getJudgementLink(self, error: str = '', alert: str = '') -> str:
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
            return Submission.objects.filter(competition=self).count()
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
            return Submission.objects.filter(competition=self, valid=True).count()
        except:
            return 0

    def submissionPointsLink(self) -> str:
        return f"{url.getRoot(APPNAME)}{url.compete.submitPoints(compID=self.getID())}"

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
        return f"{url.getRoot(APPNAME)}{url.compete.declareResults(compID=self.getID())}"

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
                rank += 1
            obj = Result.objects.bulk_create(resultsList)
            if not obj:
                return False
            self.resultDeclared = True
            self.save()
            return self
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
        Profile, through='SubmissionParticipant', related_name='submission_participants')
    repo = models.URLField(max_length=1000, blank=True, null=True)
    submitted = models.BooleanField(default=False)
    createdOn = models.DateTimeField(auto_now=False, default=timezone.now)
    modifiedOn = models.DateTimeField(auto_now=False, default=timezone.now)
    submitOn = models.DateTimeField(auto_now=False, blank=True, null=True)
    valid = models.BooleanField(default=True)
    late = models.BooleanField(default=False)

    def __str__(self) -> str:
        return f"{self.competition.title} - {self.getID()}"

    def getID(self) -> str:
        return self.id.hex

    def getCompID(self) -> str:
        return self.competition.getID()

    def save(self, *args, **kwargs):
        self.modifiedOn = timezone.now()
        return super(Submission, self).save(*args, **kwargs)

    def saveLink(self) -> str:
        """
        URL endpoint to save repo field value.
        """
        return f"{url.getRoot(APPNAME)}{url.compete.save(compID=self.getCompID(),subID=self.getID())}"

    def totalMembers(self) -> int:
        """
        All members count, regardless of membership confirmation.
        """
        return self.members.count()

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
        submps = SubmissionParticipant.objects.filter(
            submission=self, profile__in=self.members.all(), confirmed=True)

        for submp in submps:
            members.append(submp.profile)
        return members

    def getMembersEmail(self) -> list:
        members = self.getMembers()
        emails = []
        for member in members:
            emails.append(member.getEmail())
        return emails

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
        relations = SubmissionParticipant.objects.filter(
            submission=self, confirmed=False)
        for relation in relations:
            invitees.append(relation.profile)
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
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE)
    profile = models.ForeignKey(
        Profile, on_delete=models.PROTECT, related_name='participant_profile')
    confirmed = models.BooleanField(default=False)

    class Meta:
        unique_together = ("profile", "submission")


class SubmissionTopicPoint(models.Model):
    """
    For each topic, points marked by each judge for each submission in a competition.
    """
    class Meta:
        unique_together = (("submission", "topic"), ("submission", "judge"))

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

    def __str__(self) -> str:
        return f"{self.competition} - {self.rank}{self.rankSuptext()}"

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
