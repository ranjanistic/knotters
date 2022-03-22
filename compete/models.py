import re
import uuid
from django.core.cache import cache
from django.db import models
from django.db.models import Sum
from people.models import Profile
from django.conf import settings
from django.utils import timezone
from people.models import Topic
from projects.models import FreeProject
from moderation.models import Moderation
from management.models import Invitation
from main.strings import url, MANAGEMENT
from main.methods import errorLog, getNumberSuffix
from main.env import BOTMAIL, SITE
from .apps import APPNAME


def competeBannerPath(instance, filename):
    fileparts = filename.split('.')
    ext = fileparts[len(fileparts)-1]
    if not (ext in ['jpg', 'png', 'jpeg']):
        ext = 'png'
    return f"{APPNAME}/banners/{instance.get_id}_{uuid.uuid4().hex}.{ext}"

def competeAssociatePath(instance, filename):
    fileparts = filename.split('.')
    ext = fileparts[len(fileparts)-1]
    if not (ext in ['jpg', 'png', 'jpeg']):
        ext = 'png'
    return f"{APPNAME}/associates/{instance.get_id}_{uuid.uuid4().hex}.{ext}"


def defaultBannerPath():
    return f"{APPNAME}/default.png"

class Event(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    pseudonym = models.CharField(max_length=50)
    description = models.TextField(max_length=500)
    detail = models.TextField(max_length=2000)
    start_date = models.DateTimeField(auto_now=False)
    end_date = models.DateTimeField(auto_now=False)
    banner = models.ImageField(upload_to=competeBannerPath, null=True,blank=True)
    primary_color = models.CharField(max_length=7, null=True, blank=True)
    secondary_color = models.CharField(max_length=7, null=True, blank=True)
    associate = models.ImageField(upload_to=competeAssociatePath, null=True,blank=True)
    is_active = models.BooleanField(default=False)
    is_public = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now=False, default=timezone.now)
    updated_at = models.DateTimeField(auto_now=False, default=timezone.now)
    creator = models.ForeignKey(Profile, on_delete=models.PROTECT, related_name="event_creator")
    competitions = models.ManyToManyField('Competition', through="EventCompetition", related_name="event_competitions", default=[])

    @property
    def get_id(self):
        return self.id.hex

    def getID(self):
        return self.get_id

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
       self.updated_at = timezone.now()
       super(Event, self).save(*args, **kwargs) # Call the real save() method

class EventCompetition(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="event_competition_eve")
    competition = models.ForeignKey('Competition', on_delete=models.CASCADE, related_name="event_competition_comp")

    class Meta:
        unique_together = ('event', 'competition')

class Competition(models.Model):
    """
    A competition.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=1000, blank=False,
                             null=False, help_text='The competition name.')
    nickname = models.CharField(max_length=50, blank=True,null=True, help_text='The competition nickname')
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
    is_markdown = models.BooleanField(default=True)

    resultDeclared = models.BooleanField(
        default=False, help_text='Whether the results have been declared or not. Strictly restricted to be edited via server.')
    
    resultDeclaredOn = models.DateTimeField(auto_now=False,null=True,blank=True)

    creator = models.ForeignKey(
        Profile, on_delete=models.PROTECT, related_name='competition_creator')

    associate = models.ImageField(upload_to=competeAssociatePath,null=True,blank=True)
    max_grouping = models.IntegerField(default=5)

    reg_fee = models.IntegerField(default=0)
    fee_link = models.URLField(max_length=1000, blank=True, null=True)
    hidden = models.BooleanField(default=False)
    is_draft = models.BooleanField(default=False)
    createdOn = models.DateTimeField(auto_now=False, default=timezone.now)
    modifiedOn = models.DateTimeField(auto_now=False, default=timezone.now)

    qualifier = models.ForeignKey(f"{APPNAME}.Competition", on_delete=models.SET_NULL, null=True, blank=True, related_name="qualifier_competition")
    qualifier_rank = models.IntegerField(default=0)

    def __str__(self) -> str:
        return self.title

    def save(self, *args, **kwargs):
        self.modifiedOn = timezone.now()
        if not self.nickname:
            self.nickname = re.sub(r'[^a-zA-Z0-9-]', '', self.title.strip().replace(' ', '-'))[:50].strip('-').lower()
        return super(Competition, self).save(*args, **kwargs)

    @property
    def get_id(self) -> str:
        return self.id.hex

    def getID(self) -> str:
        return self.get_id

    @property
    def get_banner(self) -> str:
        return f"{settings.MEDIA_URL}{str(self.banner)}"

    def getBanner(self) -> str:
        return self.get_banner

    def get_nickname(self):
        if not self.nickname:
            nickname = re.sub(r'[^a-zA-Z0-9-]', '', self.title.strip().replace(' ', '-'))[:60].strip('-').lower()
            if Competition.objects.filter(nickname=nickname).exists():
                nickname = f"{nickname}-{self.id.hex}"
            self.nickname = nickname
            self.save()
        return self.nickname
        
    @property
    def get_banner_abs(self) -> str:
        return f"{SITE}{self.get_banner}"

    def getLink(self, error: str = '', success: str = '', alert: str = '') -> str:
        """
        Link to competition profile page
        """
        return f"{url.getRoot(APPNAME)}{url.compete.compID(compID=self.get_nickname())}{url.getMessageQuery(alert,error,success)}"

    @property
    def get_link(self) -> str:
        return self.getLink()

    @property
    def get_abs_link(self) -> str:
        if self.get_link.startswith('http:'):
            return self.get_link
        return f"{settings.SITE}{self.get_link}"

    def participationLink(self) -> str:
        return f"{url.getRoot(APPNAME)}{url.compete.participate(compID=self.getID())}"

    def isActive(self) -> bool:
        """
        Whether the competition is active or not, depending on startAt & endAt.
        """
        now = timezone.now()
        if not self.endAt:
            return (self.startAt <= now) and not self.resultDeclared
        return (self.startAt <= now < self.endAt) and not self.resultDeclared

    def isUpcoming(self) -> bool:
        """
        Whether the competition is upcoming or not, depending on startAt.
        """
        return self.startAt > timezone.now()

    def isHistory(self) -> bool:
        """
        Whether the competition is history or not, depending on endAt.
        """
        return self.endAt and self.endAt <= timezone.now()

    @property
    def state(self):
        return "upcoming" if self.isUpcoming() else "live" if self.isActive() else "history"

    def startSecondsLeft(self) -> int:
        """
        Total seconds left in this competition from the instantaneous time this method is invoked.
        """
        time = timezone.now()
        if time >= self.startAt:
            return 0
        diff = self.startAt - time
        return diff.total_seconds()

    def secondsLeft(self) -> int:
        """
        Total seconds left in this competition from the instantaneous time this method is invoked.
        """
        if not self.endAt:
            return 0
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

    def getPalleteTopics(self) -> list:
        """
        Topics to be displayed on palletes
        """
        return self.topics.filter()[:3]

    def getPerks(self) -> list:
        perks = Perk.objects.filter(competition=self).order_by('rank')
        if perks.count() < 1:
            perks = []
            for p in str(self.perks).split(';'):
                if p and p != '' and p != 'None':
                    perks.append(p)
        return perks

    def totalTopics(self) -> list:
        """
        Count total topics of this competition
        """
        return self.topics.count()

    @property
    def get_associate(self):
        return None if not self.associate else f"{settings.MEDIA_URL}{str(self.associate)}"

    @property
    def moderator(self)->Profile:
        mod = Moderation.objects.filter(type=APPNAME, competition=self).order_by('-requestOn','-respondOn').first()
        return None if not mod else mod.moderator

    
    def moderation(self)-> Moderation:
        return Moderation.objects.filter(type=APPNAME, competition=self).order_by('-requestOn','-respondOn').first()
            

    def isModerator(self, profile: Profile) -> bool:
        """
        Whether the given profile is assigned as moderator of this competition or not.
        """
        return profile and self.moderator == profile

    def getModerator(self) -> Profile:
        return self.moderator

    def moderated(self) -> bool:
        """
        Whether this competition has been moderated by moderator or not.
        Being moderated indicates that the valid submissions in this competition are ready to be marked.
        """
        return True if Moderation.objects.filter(
            type=APPNAME, competition=self, resolved=True).order_by('-requestOn','-respondOn').first() else False

    def isJudge(self, profile: Profile) -> bool:
        """
        Whether the given profile is a judge in this comopetition or not.
        """
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
        return self.judges.count()

    def getJudgementLink(self, error: str = '', alert: str = '') -> str:
        try:
            return (Moderation.objects.filter(
                type=APPNAME, competition=self).order_by("-requestOn").first()).getLink(error=error, alert=alert)
        except Exception as e:
            errorLog(e)
            return self.getLink()

    def isAllowedToParticipate(self, profile:Profile, checkqualifier=True) -> bool:    
        allowed = not (self.creator == profile or self.moderator == profile or self.isJudge(profile) or profile.is_manager() or profile.getEmail() == BOTMAIL)
        
        if allowed and checkqualifier:
            if self.qualifier:
                if not self.qualifier.resultDeclared:
                    allowed = False
                elif self.qualifier_rank > 0:
                    allowed = Result.objects.filter(competition=self.qualifier, rank__lte=self.qualifier_rank, submission__members=profile).exists()
        return allowed


    def isNotAllowedToParticipate(self, profile:Profile, checkqualifier=True) -> bool:
        return not self.isAllowedToParticipate(profile, checkqualifier)
        
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
        Calculated maximum points allowed in this competition for each submission, which depends on topics, eachTopicMaxPoint, topics, and judges.
        """
        return self.eachTopicMaxPoint * self.totalTopics() * self.totalJudges()

    def getSubmissions(self) -> list:
        """
        Returns a list of all submissions of this competition irrespective of validity.
        """
        return Submission.objects.filter(competition=self).order_by('-submitOn')

    def getParticipants(self):
        """
        All confirmed participants
        """
        parts = SubmissionParticipant.objects.filter(
            submission__competition=self, confirmed=True).only('profile')
        profiles = []
        for part in parts:
            profiles.append(part.profile)
        return profiles

    def totalParticipants(self):
        """
        Total confirmed participants
        """
        return SubmissionParticipant.objects.filter(submission__competition=self, confirmed=True).count()

    def getValidSubmissionParticipants(self):
        """
        All confirmed participants with valid submissions
        """
        parts = SubmissionParticipant.objects.filter(
            submission__competition=self, confirmed=True, submission__valid=True).only('profile')
        profiles = []
        for part in parts:
            profiles.append(part.profile)
        return profiles

    def totalValidSubmissionParticipants(self):
        """
        Total confirmed participants with valid submissions
        """
        return SubmissionParticipant.objects.filter(submission__competition=self, confirmed=True, submission__valid=True).count()

    def getAllParticipants(self) -> list:
        """
        All participants + invitees
        """
        parts = SubmissionParticipant.objects.filter(
            submission__competition=self).only('profile')
        profiles = list()
        for part in parts:
            profiles.append(part.profile)
        return profiles

    def totalAllParticipants(self):
        """
        Total participants + invitees
        """
        return SubmissionParticipant.objects.filter(submission__competition=self).count()

    def totalSubmissions(self) -> int:
        """
        Count all submissions irrespective of their validity.
        """
        return Submission.objects.filter(competition=self).count()

    def totalSubmittedSubmissions(self) -> int:
        """
        Count all submitted submissions irrespective of their validity.
        """
        return Submission.objects.filter(competition=self,submitted=True).count()

    def canBeEdited(self):
        return self.isUpcoming() or self.totalSubmittedSubmissions() == 0

    def canChangeModerator(self):
        return not self.moderated()

    def canChangeJudges(self):
        return not self.allSubmissionsMarked()

    def canBeDeleted(self):
        return self.isUpcoming() or self.totalSubmissions() == 0

    def canBeSetToDraft(self):
        
        return not self.is_draft and (self.isUpcoming() or (self.totalSubmissions() == 0))

    def getValidSubmissions(self) -> list:
        """
        Returns a list of valid submissions of this competition.
        """
        return Submission.objects.filter(competition=self, valid=True).order_by('submitOn')

    def totalValidSubmissions(self) -> int:
        """
        Count submissions with valid = True. By default all submissions are valid, unless marked invalid by the assigned competition moderator.
        """
        return Submission.objects.filter(competition=self, valid=True).count()

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
            return len(subslist) > 0 and judgeTopicPointsCount == len(subslist)*self.totalTopics()
        except Exception as e:
            errorLog(e)
            return False

    def allSubmissionsMarked(self) -> bool:
        """
        Whether all valid submissions of this competitions have been marked (topic point) by all judges or not.
        """
        try:
            subslist = self.getValidSubmissions()
            topicPointsCount = SubmissionTopicPoint.objects.filter(
                submission__competition=self,
                submission__in=subslist).count()
            return len(subslist) > 0 and topicPointsCount == len(subslist)*self.totalTopics()*self.totalJudges()
        except Exception as e:
            errorLog(e)
            return False

    def countJudgesWhoMarkedSubmissions(self) -> int:
        """
        Count judges of this competition who have submitted topic points of all valid submissions.
        """
        judges = self.getJudges()
        count = 0
        for judge in judges:
            if self.allSubmissionsMarkedByJudge(judge):
                count = count+1
        return count

    def countJudgesWhoNotMarkedSubmissions(self) -> int:
        """
        Count judges of this competition who have submitted topic points of all valid submissions.
        """
        return self.totalJudges() - self.countJudgesWhoMarkedSubmissions()

    def judgesWhoMarkedSubmissions(self):
        """
        Judges of this competition who have submitted topic points of all valid submissions.
        """
        judges = self.getJudges()
        markedJudges = []
        for judge in judges:
            if self.allSubmissionsMarkedByJudge(judge):
                markedJudges.append(judge)
        return markedJudges

    def judgesWhoNotMarkedSubmissions(self):
        """
        Judges of this competition who have not submitted topic points of all valid submissions.
        """
        judges = self.getJudges()
        unmarkedJudges = []
        for judge in judges:
            if not self.allSubmissionsMarkedByJudge(judge):
                unmarkedJudges.append(judge)
        return unmarkedJudges

    def declareResultsLink(self) -> str:
        return f"{url.getRoot(APPNAME)}{url.compete.declareResults(compID=self.getID())}"

    def declareResults(self) -> bool:
        """
        Declares results by aggregating each valid submission's topic point and calculates final score to create Result for each submission.
        Also sets resultDeclared = True
        Invoking this method should be considered as final step of a competition cycle.
        """
        try:
            if self.resultDeclared:
                raise Exception(f"Cannot declare results of {self.title}, already declared")
            if not self.allSubmissionsMarked():
                raise Exception(
                    f"Cannot declare results of {self.title} unless all valid submissions have been marked.")
            subs = self.getValidSubmissions()
            submissionPoints = SubmissionTopicPoint.objects.filter(submission__in=subs).values('submission', 'submission__submitOn').annotate(
                totalPoints=Sum('points')).order_by('-totalPoints', 'submission__submitOn')

            resultsList = []

            rank = 1
            for submissionpoint in submissionPoints:
                subm = None
                for sub in subs:
                    if str(sub.id) == str(submissionpoint['submission']):
                        subm = sub
                        break
                if subm:
                    resultsList.append(
                        Result(
                            competition=self,
                            submission=subm,
                            points=submissionpoint['totalPoints'],
                            rank=rank
                        )
                    )
                    rank = rank + 1
                else:
                    raise Exception(
                        f"Results declaration: Submission not found (valid) but submission points found! subID: {submissionpoint['submission']}")
            Result.objects.bulk_create(resultsList)
            self.resultDeclared = True
            self.resultDeclaredOn = timezone.now()
            self.save()
            if not self.allResultsDeclared():
                raise Exception(
                    'Results declaration: All results not declared!')
            return self
        except Exception as e:
            errorLog(e)
            return False

    def getResults(self) -> models.QuerySet:
        return Result.objects.filter(competition=self)

    def totalResults(self) -> int:
        return Result.objects.filter(competition=self).count()

    def allResultsDeclared(self) -> bool:
        return self.totalResults() == self.totalValidSubmissions()

    def getManagementLink(self, error: str = '', alert: str = '') -> str:
        return f"{url.getRoot(MANAGEMENT)}{url.management.competition(compID=self.getID())}{url.getMessageQuery(error=error, alert=alert)}"

    def generateCertificatesLink(self) -> str:
        return f"{url.getRoot(APPNAME)}{url.compete.generateCert(compID=self.getID())}"

    def totalParticipantCertificates(self) -> int:
        return ParticipantCertificate.objects.filter(result__competition=self).count()

    def totalAppreciateCertificates(self) -> int:
        return AppreciationCertificate.objects.filter(competition=self).count()

    def totalCertificates(self) -> int:
        return self.totalParticipantCertificates() + self.totalAppreciateCertificates()

    def certificatesGenerated(self) -> bool:
        return (self.totalValidSubmissionParticipants() + self.totalJudges() + 1) == self.totalCertificates()

    @property
    def getModCertLink(self):
        return f"{url.getRoot(APPNAME)}{url.compete.apprCertificate(compID=self.getID(),userID=self.moderator.getUserID())}"

    @property
    def getJudgeCertLink(self):
        return f"{url.getRoot(APPNAME)}{url.compete.apprCertificate(compID=self.getID(),userID='*')}"

class Perk(models.Model):
    """
    Prize of a competition
    """
    class Meta:
        unique_together = ("competition", "rank")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    competition = competition = models.ForeignKey(Competition, related_name='perk_competition', on_delete=models.CASCADE)
    rank = models.IntegerField(default=1)
    name = models.CharField(max_length=1000)

class CompetitionJudge(models.Model):
    """
    Judge of a competition
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    competition = models.ForeignKey(
        Competition, related_name='judging_competition', on_delete=models.PROTECT)
    judge = models.ForeignKey(Profile, on_delete=models.PROTECT)

    class Meta:
        unique_together = ("competition", "judge")

    def __str__(self) -> str:
        return self.competition.title

    @property
    def get_cert_link(self):
        return f"{url.getRoot(APPNAME)}{url.compete.apprCertificate(self.competition.get_id,self.judge.get_userid)}"



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
    free_project = models.ForeignKey(FreeProject, on_delete=models.SET_NULL,null=True,blank=True)
    submitted = models.BooleanField(default=False)
    createdOn = models.DateTimeField(auto_now=False, default=timezone.now)
    modifiedOn = models.DateTimeField(auto_now=False, default=timezone.now)
    submitOn = models.DateTimeField(auto_now=False, blank=True, null=True)
    valid = models.BooleanField(default=True)
    late = models.BooleanField(default=False)

    def __str__(self) -> str:
        return f"{self.competition.title} - {self.getID()}"

    @property
    def get_id(self) -> str:
        return self.id.hex

    def getID(self) -> str:
        return self.get_id

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
        Checks if provided profile object is a confirmed member or not.

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
        return (self.totalMembers() < self.competition.max_grouping) and not self.submitted and self.competition.isActive()

    def getRepo(self) -> bool:
        """
        Repo or submission link.
        """
        if self.free_project:
            return self.free_project.get_link
        return self.repo if self.repo else ''

    def submittingLate(self) -> bool:
        """
        Submitting late or not.
        NOTE: This method only represents 'late' status of submission before it has been submitted. After submission, the response of this method must not be considered reliable, instead the 'late' field should be used.
        """
        return self.competition.isHistory() and not self.submitted

    def pointedTopicsByJudge(self, judge: Profile) -> int:
        """
        Count of topics pointed by given judge for this submission.
        """
        return SubmissionTopicPoint.objects.filter(submission=self, judge=judge).count()

    def is_winner(self):
        return Result.objects.filter(submission=self, competition=self.competition, rank=1).exists()

class SubmissionParticipant(models.Model):
    """
    For participant member in a submission in a competition.
    """
    class Meta:
        unique_together = ("profile", "submission")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    submission = models.ForeignKey(
        Submission, on_delete=models.CASCADE, related_name='participant_submission')
    profile = models.ForeignKey(
        Profile, on_delete=models.PROTECT, related_name='participant_profile')
    confirmed = models.BooleanField(default=False)
    confirmed_on = models.DateTimeField(auto_now=False, null=True,blank=True)

    def save(self, *args, **kwargs):
        if self.confirmed:
            if SubmissionParticipant.objects.filter(id=self.id,confirmed=False).exists():
                self.confirmed_on = timezone.now()
        super(SubmissionParticipant, self).save(*args, **kwargs) # Call the real save() method


class SubmissionTopicPoint(models.Model):
    """
    For each topic, points marked by each judge for each submission in a competition.
    """
    class Meta:
        unique_together = (("submission", "judge", "topic"))

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    submission = models.ForeignKey(Submission, on_delete=models.PROTECT)
    topic = models.ForeignKey(Topic, on_delete=models.PROTECT)
    judge = models.ForeignKey(Profile, on_delete=models.PROTECT)
    points = models.IntegerField(default=0)

    def __str__(self) -> str:
        return self.submission.getID()


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
    xpclaimers = models.ManyToManyField(
        Profile, through='ResultXPClaimer', related_name='result_xpclaimers', default=[])
    certificates = models.ManyToManyField(
        Profile, through='ParticipantCertificate', related_name='result_certificates', default=[])

    def __str__(self) -> str:
        return f"{self.competition} - {self.rank}{self.rankSuptext()}"

    @property
    def get_id(self):
        return self.id.hex

    def getID(self):
        return self.get_id

    def submitOn(self):
        return self.submission.submitOn

    def rankSuptext(self, rnk=0) -> str:
        rank = self.rank if rnk == 0 else rnk
        return getNumberSuffix(int(rank))

    def getRank(self, rnk=0) -> str:
        return f"{self.rank}{self.rankSuptext(rnk=rnk)}"

    def hasClaimedXP(self, profile: Profile) -> bool:
        return profile in self.xpclaimers.all()
    
    def getClaimXPLink(self) -> str:
        return f"{url.getRoot(APPNAME)}{url.compete.claimXP(self.competition.get_id,self.submission.get_id)}"

    def allXPClaimed(self) -> bool:
        return self.submission.totalMembers() == self.xpclaimers.count

    def getCertLink(self):
        return f"{url.getRoot(APPNAME)}{url.compete.certificate(resID=self.get_id,userID='*')}"

    def getCertDownloadLink(self):
        return f"{url.getRoot(APPNAME)}{url.compete.certificateDownload(resID=self.get_id,userID='*')}"

    def getMembers(self):
        return self.submission.getMembers()
    
    @property
    def topic_points(self):
        topicscore = cache.get(f"submission_topic_score_result_{self.id}",None)
        if not topicscore:
            topicscore = SubmissionTopicPoint.objects.filter(submission=self.submission).values('topic__id','topic__name').annotate(score=Sum('points'))
            cache.set(f"submission_topic_score_result_{self.id}", topicscore, settings.CACHE_MAX)
        return topicscore


class ResultXPClaimer(models.Model):
    class Meta:
        unique_together = ("result", "profile")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    result = models.ForeignKey(
        Result, on_delete=models.PROTECT, related_name='xpclaimer_result')
    profile = models.ForeignKey(
        Profile, on_delete=models.PROTECT, related_name='xpclaimer_profile')


class ParticipantCertificate(models.Model):
    class Meta:
        unique_together = ("result", "profile")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    result = models.ForeignKey(
        Result, on_delete=models.PROTECT, related_name='participant_certificate_result')
    profile = models.ForeignKey(
        Profile, on_delete=models.PROTECT, related_name='participant_certificate_profile')
    certificate = models.CharField(default='', null=True, blank=True,max_length=1000)

    @property
    def certficateImage(self):
        return f"{str(self.certificate).replace('.pdf','.jpg')}" if self.certificate else None

    @property
    def get_id(self):
        return self.id.hex

    @property
    def get_link(self):
        return f"{url.getRoot(APPNAME)}{url.compete.certificate(resID=self.result.getID(),userID=self.profile.getUserID())}"

    @property
    def getCertImage(self):
        return f"{settings.MEDIA_URL}{str(self.certificate).replace('.pdf','.jpg')}"

    @property
    def getCert(self):
        return f"{settings.MEDIA_URL}{str(self.certificate)}"

    def getCertificate(self):
        return f"{settings.MEDIA_URL}{str(self.certificate)}"

class AppreciationCertificate(models.Model):
    class Meta:
        unique_together = ("competition", "appreciatee")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    competition = models.ForeignKey(Competition, on_delete=models.PROTECT, related_name='appreciation_certificate_competition')
    appreciatee = models.ForeignKey(Profile, on_delete=models.PROTECT, related_name='appreciation_certificate_profile')
    certificate = models.CharField(default='', null=True, blank=True,max_length=1000)

    @property
    def certficateImage(self):
        return f"{str(self.certificate).replace('.pdf','.jpg')}" if self.certificate else None

    @property
    def get_id(self):
        return self.id.hex

    @property
    def get_link(self):
        return f"{url.getRoot(APPNAME)}{url.compete.apprCertificate(compID=self.competition.getID(),userID=self.appreciatee.getUserID())}"

    @property
    def get_download_link(self):
        return f"{url.getRoot(APPNAME)}{url.compete.apprCertificateDownload(compID=self.competition.getID(),userID=self.appreciatee.getUserID())}"

    @property
    def getCertImage(self):
        return f"{settings.MEDIA_URL}{str(self.certificate).replace('.pdf','.jpg')}"

    @property
    def getCertificate(self):
        return f"{settings.MEDIA_URL}{str(self.certificate)}"

class SubmissionTeamInvitation(Invitation):
    sender = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='team_invitation_sender')
    receiver = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='team_invitation_receiver')
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE, related_name='invitation_submission')

    class Meta:
        unique_together = ('sender', 'receiver', 'submission')
