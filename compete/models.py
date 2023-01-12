from datetime import datetime
from re import sub as re_sub
from uuid import UUID, uuid4

from django.conf import settings
from django.core.cache import cache
from django.core.files.base import File
from djongo import models
from django.db.models import Sum
from django.utils import timezone
from main.env import SITE
from main.methods import errorLog, filterNickname, getNumberSuffix
from main.strings import MANAGEMENT, Message, url
from management.models import Invitation
from people.models import Profile, Topic
from projects.models import FreeProject

from .apps import APPNAME


def competeBannerPath(instance: "Competition", rawFilename: str) -> str:
    """Returns the path for the competition banner.

    Args:
        instance (Competition): The competition instance
        filename (str): The raw of filname of the banner, with extension

    Returns:
        str: The unique path for the competition banner
    """
    fileparts = rawFilename.split('.')
    ext = fileparts[-1]
    if not (ext in ['jpg', 'png', 'jpeg']):
        ext = 'png'
    return f"{APPNAME}/banners/{instance.get_id}_{uuid4().hex}.{ext}"


def competeAssociatePath(instance: "Competition", rawFilename: str) -> str:
    """Returns the path for the competition associate banner.

    Args:
        instance (Competition): The competition instance
        rawFilename (str): The raw filname of the banner, with extension

    Returns:
        str: The unique path for the competition associate banner
    """
    fileparts = rawFilename.split('.')
    ext = fileparts[-1]
    if not (ext in ['jpg', 'png', 'jpeg']):
        ext = 'png'
    return f"{APPNAME}/associates/{instance.get_id}_{uuid4().hex}.{ext}"


def defaultBannerPath() -> str:
    """Returns the path for the default banner.

    Returns:
        str: The path for the default banner
    """
    return f"{APPNAME}/default.png"


class Event(models.Model):
    """The event model.
    """

    id: UUID = models.UUIDField(
        primary_key=True, default=uuid4, editable=False)
    name: str = models.CharField(max_length=100)
    """name (CharField): The name of the event"""
    pseudonym: str = models.CharField(max_length=50)
    """pseudonym (CharField): The pseudonym of the event"""
    description: str = models.TextField(max_length=500)
    """description (TextField): The description of the event"""
    detail: str = models.TextField(max_length=2000)
    """detail (TextField): The detail of the event"""
    start_date: datetime = models.DateTimeField(auto_now=False)
    """start_date (DateTimeField): The start date of the event"""
    end_date: datetime = models.DateTimeField(auto_now=False)
    """end_date (DateTimeField): The end date of the event"""
    banner: File = models.ImageField(
        upload_to=competeBannerPath, null=True, blank=True)
    """banner (ImageField): The banner of the event"""
    primary_color: str = models.CharField(max_length=7, null=True, blank=True)
    """primary_color (CharField): The primary color of the event"""
    secondary_color: str = models.CharField(
        max_length=7, null=True, blank=True)
    """secondary_color (CharField): The secondary color of the event"""
    associate: File = models.ImageField(
        upload_to=competeAssociatePath, null=True, blank=True)
    """associate (ImageField): The associate banner of the event"""
    is_active: bool = models.BooleanField(default=False)
    """is_active (BooleanField): Whether the event is active or not"""
    is_public: bool = models.BooleanField(default=False)
    """is_public (BooleanField): Whether the event is public or not"""
    created_at: datetime = models.DateTimeField(
        auto_now=False, default=timezone.now)
    """created_at (DateTimeField): The date and time the event was created"""
    updated_at: datetime = models.DateTimeField(
        auto_now=False, default=timezone.now)
    """updated_at (DateTimeField): The date and time the event was updated"""
    creator: Profile = models.ForeignKey(
        Profile, on_delete=models.PROTECT, related_name="event_creator")
    """creator (ForeignKey<Profile>): The creator of the event"""
    competitions = models.ManyToManyField(
        'Competition', through="EventCompetition", related_name="event_competitions", default=[])
    """competitions (ManyToManyField<Competition>): The competitions in the event"""

    @property
    def get_id(self):
        """Returns the hex id of the event.

        Returns:
            str: The hex id of the event
        """
        return self.id.hex

    def getID(self):
        return self.get_id

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """
        Updates the updated_at field and calls the superclass save method.
        """
        self.updated_at = timezone.now()
        super(Event, self).save(*args, **kwargs)


class EventCompetition(models.Model):
    """
    The model for many to many relationship between events and competitions.

    """
    id: UUID = models.UUIDField(
        primary_key=True, default=uuid4, editable=False)

    event: Event = models.ForeignKey(
        Event, on_delete=models.CASCADE, related_name="event_competition_eve")
    """event (ForeignKey<Event>): The event"""
    competition: "Competition" = models.ForeignKey(
        'Competition', on_delete=models.CASCADE, related_name="event_competition_comp")
    """competition (ForeignKey<Competition>): The competition"""

    class Meta:
        unique_together = ('event', 'competition')


class Competition(models.Model):
    """
    A competition.
    """
    id: UUID = models.UUIDField(
        primary_key=True, default=uuid4, editable=False)
    title: str = models.CharField(max_length=1000, blank=False,
                                  null=False, help_text='The competition name.')
    """title (CharField): The competition name"""
    nickname: str = models.CharField(
        max_length=50, blank=True, null=True, help_text='The competition nickname')
    """nickname (CharField): The competition nickname"""
    tagline: str = models.CharField(max_length=2000, blank=False, null=False,
                                    help_text='This will be shown in introduction and url previews.')
    """tagline (CharField): The competition tagline"""
    shortdescription: str = models.TextField(
        max_length=5000, blank=False, null=False, help_text='This will be shown in introduction.')
    """shortdescription (CharField): The competition short description"""
    description: str = models.TextField(max_length=20000, blank=False, null=False,
                                        help_text='This will be shown in the overview, along with perks, only after the competition as started.')
    """description (CharField): The competition description"""
    banner: File = models.ImageField(
        upload_to=competeBannerPath, default=defaultBannerPath)
    """banner (ImageField): The competition banner"""

    startAt: datetime = models.DateTimeField(auto_now=False, default=timezone.now,
                                             help_text='When this competition will start accepting submissions.')
    """startAt (DateTimeField): When this competition will start accepting submissions"""
    endAt: datetime = models.DateTimeField(
        auto_now=False, help_text='When this competition will stop accepting submissions.')
    """endAt (DateTimeField): When this competition will stop accepting submissions"""

    judges = models.ManyToManyField(
        Profile, through='CompetitionJudge', default=[])
    """judges (ManyToManyField<Profile>): The judges of the competition"""

    topics = models.ManyToManyField(
        Topic, through='CompetitionTopic', default=[])
    """topics (ManyToManyField<Topic>): The topics of the competition"""

    perks: str = models.CharField(max_length=1000, null=True, blank=True,
                                  help_text='Use semi-colon (;) separated perks for each rank, starting from 1st.')
    """perks (CharField): Deprecated. Use Perks model."""

    eachTopicMaxPoint: int = models.IntegerField(
        default=10, help_text='The maximum points each judge can appoint for each topic to each submission of this competition.')
    """eachTopicMaxPoint (IntegerField): The maximum points each judge can appoint for each topic to each submission of this competition"""

    taskSummary: str = models.TextField(max_length=50000)
    """taskSummary (CharField): The task summary of the competition"""
    taskDetail: str = models.TextField(max_length=100000)
    """taskDetail (CharField): The task detail of the competition"""
    taskSample: str = models.TextField(max_length=10000)
    """taskSample (CharField): The task sample of the competition"""
    is_markdown: bool = models.BooleanField(default=True)
    """is_markdown (BooleanField): Whether the task summary and detail are in markdown format or not, should be True. False is for backwards compatibility."""

    resultDeclared: bool = models.BooleanField(
        default=False, help_text='Whether the results have been declared or not. Strictly restricted to be edited via server.')
    """resultDeclared (BooleanField): Whether the results have been declared or not"""

    resultDeclaredOn: datetime = models.DateTimeField(
        auto_now=False, null=True, blank=True)
    """resultDeclaredOn (DateTimeField): When the results were declared"""

    creator: Profile = models.ForeignKey(
        Profile, on_delete=models.PROTECT, related_name='competition_creator')
    """creator (ForeignKey<Profile>): The creator of the competition"""

    associate: File = models.ImageField(
        upload_to=competeAssociatePath, null=True, blank=True)
    """associate (ImageField): The associate banner of the competition"""

    max_grouping: int = models.IntegerField(default=5)
    """max_grouping (IntegerField): The maximum number of members in one submission group"""

    reg_fee: float = models.FloatField(default=0)
    """reg_fee (IntegerField): Deprecated. The registration fee."""
    fee_link: str = models.URLField(max_length=1000, blank=True, null=True)
    """fee_link (URLField): The link to the registration fee payment page."""
    hidden: bool = models.BooleanField(default=False)
    """hidden (BooleanField): Whether the competition is hidden or not. Not to be used by managers."""
    is_draft: bool = models.BooleanField(default=True)
    """is_draft (BooleanField): Whether the competition is a draft or not"""
    createdOn: datetime = models.DateTimeField(
        auto_now=False, default=timezone.now)
    """createdOn (DateTimeField): When the competition was created"""
    modifiedOn: datetime = models.DateTimeField(
        auto_now=False, default=timezone.now)
    """modifiedOn (DateTimeField): When the competition was last modified"""

    qualifier: "Competition" = models.ForeignKey(f"{APPNAME}.Competition", on_delete=models.SET_NULL,
                                                 null=True, blank=True, related_name="qualifier_competition")
    """qualifier (ForeignKey<Competition>): The qualifier competition"""
    qualifier_rank: int = models.IntegerField(default=0)
    """qualifier_rank (IntegerField): The maximum required rank from the qualifier competition"""
    admirers = models.ManyToManyField(
        Profile, through="CompetitionAdmirer", related_name='competition_admirers', default=[])

    def __str__(self) -> str:
        return self.title

    def save(self, *args, **kwargs):
        self.modifiedOn = timezone.now()
        if not self.nickname:
            self.nickname = re_sub(r'[^a-zA-Z0-9\-]', "", self.title[:60])
            self.nickname = "-".join(list(filter(lambda c: c,
                                     self.nickname.split('-')))).lower()
            if Competition.objects.filter(nickname=self.nickname).exclude(id=self.id).exists():
                self.nickname = f"{self.nickname}-{self.get_id}"
        return super(Competition, self).save(*args, **kwargs)

    @property
    def get_id(self) -> str:
        return self.id.hex

    def getID(self) -> str:
        return self.get_id

    @property
    def get_banner(self) -> str:
        """Get the banner url.

        Returns:
            str: The banner url.
        """
        return f"{settings.MEDIA_URL}{str(self.banner)}"

    def getBanner(self) -> str:
        return self.get_banner

    def get_nickname(self) -> str:
        """Get the nickname. Generates if not set.

        Returns:
            str: The nickname.
        """
        if not self.nickname:
            self.nickname = filterNickname(self.title, 60)
            if Competition.objects.filter(nickname=self.nickname).exclude(id=self.id).exists():
                self.nickname = f"{self.nickname}-{self.get_id}"
                self.nickname = filterNickname(self.title, 60)
            self.save()
        return self.nickname

    @property
    def get_banner_abs(self) -> str:
        return f"{SITE}{self.get_banner}"

    def getLink(self, error: str = '', success: str = '', alert: str = '') -> str:
        """Get the competition public profile link.

        Args:
            error (str, optional): The error message. Defaults to ''.
            success (str, optional): The success message. Defaults to ''.
            alert (str, optional): The alert message. Defaults to ''.

        Returns:
            str: The competition public profile link.
        """
        return f"{url.getRoot(APPNAME)}{url.compete.compID(compID=self.get_nickname())}{url.getMessageQuery(alert,error,success)}"

    @property
    def get_link(self) -> str:
        """Get the competition public profile link."""
        return self.getLink()

    @property
    def get_abs_link(self) -> str:
        """Get the competition absolute public profile link.

        Returns:
            str: The competition absolute public profile link.
        """
        if self.get_link.startswith('http:'):
            return self.get_link
        return f"{settings.SITE}{self.get_link}"

    @property
    def CACHE_KEYS(self):
        class CKEYS():
            result_declaration_task = f"results_declaration_task_{self.get_id}"
            certificates_allotment_task = f"certificates_allotment_task_{self.get_id}"
            total_admirations = f'{self.get_id}_compete_total_admiration'
            compete_admirers = f'{self.get_id}_compete_admirers'
        return CKEYS()

    def get_cache_one(*args, nickname: str = None, compID: UUID = None, throw: bool = False) -> "Competition":
        cacheKey = f"{APPNAME}_competition_profile"
        if nickname:
            cacheKey = f"{cacheKey}_{nickname}"
        else:
            cacheKey = f"{cacheKey}_{compID}"
        compete: Competition = cache.get(cacheKey, None)
        if not compete:
            if throw:
                if nickname:
                    compete: Competition = Competition.objects.get(
                        nickname=nickname)
                else:
                    compete: Competition = Competition.objects.get(id=compID)
            else:
                if nickname:
                    compete: Competition = Competition.objects.filter(
                        nickname=nickname).first()
                else:
                    compete: Competition = Competition.objects.filter(
                        id=compID).first()
            cache.set(cacheKey, compete, settings.CACHE_SHORT)
        return compete

    def participationLink(self) -> str:
        """Get the participation link. To be used by participants for participating, via POST method.

        Returns:
            str: The participation link.
        """

        return f"{url.getRoot(APPNAME)}{url.compete.participate(compID=self.get_id)}"

    def isActive(self) -> bool:
        """Check if the competition is active, depending on the start and end dates.

        Returns:
            bool: Whether the competition is active or not.
        """
        now = timezone.now()
        if not self.endAt:
            return (self.startAt <= now) and not self.resultDeclared
        return (self.startAt <= now < self.endAt) and not self.resultDeclared

    def isUpcoming(self) -> bool:
        """Whether the competition is upcoming or not, depending on startAt.

        Returns:
            bool: Whether the competition is upcoming or not.
        """
        return self.startAt > timezone.now()

    def isHistory(self) -> bool:
        """Whether the competition is history or not, depending on endAt.

        Returns:
            bool: Whether the competition is history or not.
        """
        return self.endAt and self.endAt <= timezone.now()

    @property
    def state(self) -> str:
        """Get the competition state.

        Returns:
            str: The competition state. (live|upcoming|history)
        """
        return "upcoming" if self.isUpcoming() else "live" if self.isActive() else "history"

    def startSecondsLeft(self) -> int:
        """Total seconds left for this competition to start, from the instantaneous time this method is invoked.

        Returns:
            int: The seconds left or 0 if the competition has already started.
        """

        time = timezone.now()
        if time >= self.startAt:
            return 0
        diff = self.startAt - time
        return diff.total_seconds()

    def secondsLeft(self) -> int:
        """Total seconds left for this competition to end, from the instantaneous time this method is invoked.

        Returns:
            int: The seconds left or 0 if the competition is already over.
        """
        time = timezone.now()
        if not self.endAt:
            return 0
        if time >= self.endAt:
            return 0
        diff = self.endAt - time
        return diff.total_seconds()

    def getTopics(self) -> list:
        """Get the list of topics instances of this competition.

        Returns:
            list<Topic>: The topics of this competition.
        """

        return self.topics.all()

    def getPalleteTopics(self, limit: int = 3) -> list:
        """Topics to be displayed on palletes

        Returns:
            list<Topic>: The pallete topics of this competition.
        """

        return self.topics.filter()[:limit]

    def getPerks(self) -> list:
        """Get the list of perks instances of this competition.

        Returns:
            list<Perk>: The perks of this competition.
        """
        perks = Perk.objects.filter(competition=self).order_by('rank')
        if len(perks) < 1 and self.perks:
            perks = list(filter(lambda p: p, self.perks.split(';')))
        return perks

    def total_admirers(self) -> int:
        """Returns the total number of admirers of this competition
        """
        cacheKey = self.CACHE_KEYS.total_admirations
        count = cache.get(cacheKey, None)
        if not count:
            count = self.admirers.count()
            cache.set(cacheKey, count, settings.CACHE_INSTANT)
        return count

    def get_admirers(self) -> models.QuerySet:
        """Returns the admirers of this competition.
        """
        cacheKey = self.CACHE_KEYS.compete_admirers
        admirers = cache.get(cacheKey, [])
        if not len(admirers):
            admirers = self.admirers.all()
            cache.set(cacheKey, admirers, settings.CACHE_INSTANT)
        return admirers

    def totalTopics(self) -> int:
        """Get the total number of topics in this competition.

        Returns:
            int: The total number of topics in this competition.
        """
        return self.topics.count()

    @property
    def get_associate(self) -> str:
        """Get the associate banner path of this competition.

        Returns:
            str, None: The associate banner path of this competition or None if not set.
        """
        return None if not self.associate else f"{settings.MEDIA_URL}{str(self.associate)}"

    def moderation(self):
        """Get the moderation instance of this competition.

        Returns:
            Moderation: The moderation instance of this competition.
        """
        from moderation.models import Moderation
        return Moderation.objects.filter(type=APPNAME, competition=self).order_by('-requestOn', '-respondOn').first()

    def moderator(self) -> Profile:
        """ Get the moderator profile instance of this competition.

        Returns:
            Profile: The moderator profile instance of this competition.
        """
        try:
            return self.moderation().moderator
        except AttributeError:
            pass
        except Exception as e:
            errorLog(e)
            pass
        return None

    def isModerator(self, profile: Profile) -> bool:
        """Check if the profile is the moderator of this competition.

        Args:
            profile (Profile): The profile to check.

        Returns:
            bool: Whether the profile is the moderator of this competition.
        """
        return profile and self.moderator() == profile

    def getModerator(self) -> Profile:
        """Get the moderator profile instance of this competition.

        Returns:
            Profile: The moderator profile instance of this competition.
        """
        return self.moderator()

    def moderated(self) -> bool:
        """Whether this competition has been moderated by moderator or not.
        Being moderated indicates that the valid submissions in this competition are ready to be marked.

        Returns:
            bool: Whether this competition has been moderated by moderator or not.
        """
        from moderation.models import Moderation
        return Moderation.objects.filter(type=APPNAME, competition=self, resolved=True).exists()

    def isJudge(self, profile: Profile) -> bool:
        """Check if the profile is the judge of this competition.

        Args:
            profile (Profile): The profile to check.

        Returns:
            bool: Whether the profile is the judge of this competition.
        """
        return self.judges.count() and self.judges.filter(user=profile.user).exists()

    def getJudges(self) -> list:
        """Get the list of Profile instances of judges of this competition.

        Returns:
            list: The list of Profile instances of judges of this competition.
        """
        return self.judges.all()

    def totalJudges(self) -> int:
        """Get the total number of judges in this competition.

        Returns:
            int: The total number of judges in this competition.
        """
        return self.judges.count()

    def getJudgementLink(self, error: str = '', alert: str = '', success: str = "") -> str:
        """Get the judgement link of this competition. To be used by the judge or moderator to render the judgement/moderation page.

        Args:
            error (str): The error message to display.
            alert (str): The alert message to display.
            success (str): The success message to display.

        Returns:
            str: The judgement/moderation page link of this competition.
        """
        try:
            return self.moderation().getLink(error=error, alert=alert, success=success)
        except AttributeError:
            pass
        except Exception as e:
            errorLog(e)
            pass
        return self.getLink(error=Message.INVALID_REQUEST)

    def isAllowedToParticipate(self, profile: Profile, checkqualifier=True) -> bool:
        """Check if the profile is allowed to participate in this competition.

        Args:
            profile (Profile): The profile to check.
            checkqualifier (bool): Whether to check the through the qualifier competition as well or not. Defaults to True.

        Returns:
            bool: Whether the profile is allowed to participate in this competition.
        """
        allowed = not (self.creator == profile or self.isModerator(
            profile) or self.isJudge(profile) or profile.is_manager())

        if checkqualifier and allowed:
            if self.qualifier:
                if not self.qualifier.resultDeclared:
                    allowed = False
                elif self.qualifier_rank > 0:
                    allowed = Result.objects.filter(
                        competition=self.qualifier, rank__lte=self.qualifier_rank, submission__members=profile).exists()
        return allowed

    def isNotAllowedToParticipate(self, profile: Profile, checkqualifier=True) -> bool:
        """Check if the profile is not allowed to participate in this competition.

        Args:
            profile (Profile): The profile to check.
            checkqualifier (bool, optional): Whether to check the through the qualifier competition as well or not. Defaults to True.

        Returns:
            bool: Whether the profile is not allowed to participate in this competition.
        """
        return not self.isAllowedToParticipate(profile, checkqualifier)

    def isParticipant(self, profile: Profile) -> bool:
        """Check if the profile is a participant of this competition, regardless of participation confirmation.

        Args:
            profile (Profile): The profile to check.

        Returns:
            bool: Whether the profile is a participant of this competition.
        """
        return Submission.objects.filter(competition=self, members=profile).exists()

    def getMaxScore(self) -> int:
        """Calculated maximum points allowed in this competition for each submission, which depends on topics, eachTopicMaxPoint, topics, and judges.

        Returns:
            int: The maximum points allowed in this competition for each submission.
        """
        return self.eachTopicMaxPoint * self.totalTopics() * self.totalJudges()

    def getSubmissions(self) -> models.QuerySet:
        """Get the list of submissions instances of this competition, ordered by submission time.

        Returns:
            list<Submission>: The list of submissions instances of this competition.
        """
        return Submission.objects.filter(competition=self).order_by('-submitOn')

    def getParticipants(self) -> list:
        """Get the list of confirmed participant Profile instances of this competition, ordered by submission time.

        Returns:
            list<Profile>: The list of confirmed participant Profile instances of this competition.
        """
        return list(map(lambda x: x.profile, SubmissionParticipant.objects.filter(submission__competition=self, confirmed=True).only('profile')))

    def totalParticipants(self) -> int:
        """Get the total number of confirmed participants profiles of this competition.

        Returns:
            int: The total number of confirmed participants profiles of this competition.
        """
        return SubmissionParticipant.objects.filter(submission__competition=self, confirmed=True).count()

    def getValidSubmissionParticipants(self) -> list:
        """Get the list of confirmed participant Profile instances of this competition with valid submissions, ordered by submission time.

        Returns:
            list<Profile>: The list of confirmed participant Profile instances of this competition with valid submissions.
        """
        return list(map(lambda x: x.profile, SubmissionParticipant.objects.filter(submission__competition=self, confirmed=True, submission__valid=True).only('profile')))

    def totalValidSubmissionParticipants(self) -> int:
        """Get the total number of confirmed participants profiles of this competition with valid submissions.

        Returns:
            int: The total number of confirmed participants profiles of this competition with valid submissions.
        """
        return SubmissionParticipant.objects.filter(submission__competition=self, confirmed=True, submission__valid=True).count()

    def getAllParticipants(self) -> list:
        """Get the list of participant Profile instances of this competition.

        Returns:
            list<Profile>: The list of participant Profile instances of this competition.
        """
        return list(map(lambda x: x.profile, SubmissionParticipant.objects.filter(submission__competition=self).only('profile')))

    def totalAllParticipants(self) -> int:
        """Get the total number of participant profiles of this competition, including unconfirmed participants.

        Returns:
            int: The total number of participant profiles of this competition, including unconfirmed participants.
        """
        return SubmissionParticipant.objects.filter(submission__competition=self).count()

    def totalSubmissions(self) -> int:
        """Get the total number of submissions of this competition, including invalid submissions and unsubmitted submissions.

        Returns:
            int: The total number of submissions of this competition, including invalid submissions and unsubmitted submissions.
        """
        return Submission.objects.filter(competition=self).count()

    def totalSubmittedSubmissions(self) -> int:
        """Get the total number of submitted submissions of this competition, including invalid submissions.

        Returns:
            int: The total number of submitted submissions of this competition, including invalid submissions.
        """
        return Submission.objects.filter(competition=self, submitted=True).count()

    def canBeEdited(self) -> bool:
        """Check if this competition can be edited by its creator.

        Returns:
            bool: Whether this competition can be edited by its creator.
        """
        return self.isUpcoming() or self.totalSubmittedSubmissions() == 0

    def canChangeModerator(self) -> bool:
        """Check if the moderator of this competition can be changed by its creator.
        Useful when moderator is being re-assigned.

        Returns:
            bool: Whether the moderator of this competition can be changed by its creator.
        """
        return not self.moderated()

    def canChangeJudges(self) -> bool:
        """Check if the judges of this competition can be changed by its creator.
        Useful when judges are being re-assigned.

        Returns:
            bool: Whether the judges of this competition can be changed by its creator.
        """
        return not self.allSubmissionsMarked()

    def canBeDeleted(self) -> bool:
        """Check if this competition can be deleted by its creator.

        Returns:
            bool: Whether this competition can be deleted by its creator.
        """
        return self.isUpcoming() or self.totalSubmissions() == 0

    def canBeSetToDraft(self) -> bool:
        """Check if this competition can be set to draft by its creator.

        Returns:
            bool: Whether this competition can be set to draft by its creator.
        """
        return not self.is_draft and (self.isUpcoming() or (self.totalSubmissions() == 0))

    def getValidSubmissions(self) -> models.QuerySet:
        """Get the list of valid submission instances of this competition, ordered by submission time.

        Returns:
            list<Submission>: The list of valid submission instances of this competition.
        """
        return Submission.objects.filter(competition=self, valid=True).order_by('submitOn')

    def totalValidSubmissions(self) -> int:
        """Get the total number of valid submissions of this competition.

        Returns:
            int: The total number of valid submissions of this competition.
        """
        return Submission.objects.filter(competition=self, valid=True).count()

    def submissionPointsLink(self) -> str:
        """Get the link to submit the points of submissions of this competition, to be used by any judge via POST.

        Returns:
            str: The link to submit the points of submissions of this competition.
        """
        return f"{url.getRoot(APPNAME)}{url.compete.submitPoints(compID=self.get_id)}"

    def allSubmissionsMarkedByJudge(self, judge: Profile) -> bool:
        """Check if all submissions of this competition are marked by the given judge.

        Args:
            judge (Profile): The judge to check.

        Returns:
            bool: Whether all submissions of this competition are marked by the given judge.
        """
        try:
            subslist = self.getValidSubmissions()
            judgeTopicPointsCount = SubmissionTopicPoint.objects.filter(
                submission__in=subslist, judge=judge).count()
            return (len(subslist) > 0) and judgeTopicPointsCount == (len(subslist)*self.totalTopics())
        except Exception as e:
            errorLog(e)
            return False

    def allSubmissionsMarked(self) -> bool:
        """Check if all submissions of this competition are marked.

        Returns:
            bool: Whether all submissions of this competition are marked.
        """
        try:
            subslist = self.getValidSubmissions()
            topicPointsCount = SubmissionTopicPoint.objects.filter(
                submission__competition=self,
                submission__in=subslist).count()
            return (len(subslist) > 0) and topicPointsCount == (len(subslist)*self.totalTopics()*self.totalJudges())
        except Exception as e:
            errorLog(e)
            return False

    def judgesWhoMarkedSubmissions(self) -> list:
        """Get the list of judge profile instances who marked submissions of this competition.

        Returns:
            list<Profile>: The list of judge profile instances who marked submissions of this competition.
        """
        return list(filter(lambda j: self.allSubmissionsMarkedByJudge(j), self.getJudges()))

    def judgesWhoNotMarkedSubmissions(self) -> list:
        """Get the list of judge profile instances who did not mark submissions of this competition.

        Returns:
            list<Profile>: The list of judge profile instances who did not mark submissions of this competition.
        """
        return list(filter(lambda j: not self.allSubmissionsMarkedByJudge(j), self.getJudges()))

    def countJudgesWhoMarkedSubmissions(self) -> int:
        """Get the number of judges who marked submissions of this competition.

        Returns:
            int: The number of judges who marked submissions of this competition.
        """
        return len(self.judgesWhoMarkedSubmissions())

    def countJudgesWhoNotMarkedSubmissions(self) -> int:
        """Get the number of judges who did not mark submissions of this competition.

        Returns:
            int: The number of judges who did not mark submissions of this competition.
        """
        return len(self.judgesWhoNotMarkedSubmissions())

    def declareResultsLink(self) -> str:
        """Get the link to declare the results of this competition, to be used by the creator via POST.

        Returns:
            str: The link to declare the results of this competition.
        """
        return f"{url.getRoot(APPNAME)}{url.compete.declareResults(compID=self.getID())}"

    def declareResults(self) -> bool:
        """Declares results by aggregating each valid submission's topic point and calculates final score to create Result instance for each valid submission.
        Also sets resultDeclared = True
        Invoking this method should be considered as final step of a competition cycle.

        Returns:
            bool: Whether the results were declared successfully.
        """
        try:
            if self.resultDeclared:
                raise Exception(
                    f"Cannot declare results of {self.title}, already declared", self)
            if not self.allSubmissionsMarked():
                raise Exception(
                    f"Cannot declare results of {self.title} unless all valid submissions have been marked.", self)
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
                        f"Results declaration: Submission not found (valid) but submission points found! subID: {submissionpoint['submission']}", submissionpoint, self)
            Result.objects.bulk_create(resultsList)
            self.resultDeclared = True
            self.resultDeclaredOn = timezone.now()
            self.save()
            if not self.allResultsDeclared():
                raise Exception(
                    'Results declaration: All results not declared!', self)
            return self
        except Exception as e:
            errorLog(e)
            return False

    def getResults(self) -> models.QuerySet:
        """Get the list of result instances of this competition.

        Returns:
            list<Result>: The result instances of this competition.
        """
        return Result.objects.filter(competition=self)

    def totalResults(self) -> int:
        """Get the total number of results of this competition.

        Returns:
            int: The total number of results of this competition.
        """
        return Result.objects.filter(competition=self).count()

    def allResultsDeclared(self) -> bool:
        """Check if all valid submissions got their results declared.

        Returns:
            bool: Whether all valid submissions got their results declared.
        """
        return self.totalResults() == self.totalValidSubmissions()

    def getManagementLink(self, error: str = '', alert: str = '', success: str = '') -> str:
        """Get the link to the management view of this competition, to be used by the creator.

        Args:
            error (str): The error message to display. Default is empty.
            alert (str): The alert message to display. Default is empty.
            success (str): The success message to display. Default is empty.

        Returns:
            str: The link to the management view of this competition.
        """
        return f"{url.getRoot(MANAGEMENT)}{url.management.competition(compID=self.getID())}{url.getMessageQuery(error=error, alert=alert, success=success)}"

    def generateCertificatesLink(self) -> str:
        """Get the link to generate certificates of this competition, to be used by the creator via POST.

        Returns:
            str: The link to generate certificates of this competition.
        """
        return f"{url.getRoot(APPNAME)}{url.compete.generateCert(compID=self.getID())}"

    def totalParticipantCertificates(self) -> int:
        """Get the total number of participant certificates of this competition.

        Returns:
            int: The total number of participant certificates of this competition.
        """
        return ParticipantCertificate.objects.filter(result__competition=self).count()

    def totalAppreciateCertificates(self) -> int:
        """Get the total number of appreciation certificates of this competition.

        Returns:
            int: The total number of appreciation certificates of this competition.
        """
        return AppreciationCertificate.objects.filter(competition=self).count()

    def totalCertificates(self) -> int:
        """Get the total number of certificates of this competition.

        Returns:
            int: The total number of certificates of this competition.
        """
        return self.totalParticipantCertificates() + self.totalAppreciateCertificates()

    def certificatesGenerated(self) -> bool:
        """Check if all certificates of this competition were generated.

        Returns:
            bool: Whether all certificates of this competition were generated.
        """
        return (self.totalValidSubmissionParticipants() + self.totalJudges() + 1) == self.totalCertificates()

    @property
    def getModCertLink(self) -> str:
        """Get the link to the view page of certificate of the moderator of this competition.

        Returns:
            str: The link to the view page of certificate of the moderator of this competition.
        """
        return f"{url.getRoot(APPNAME)}{url.compete.apprCertificate(compID=self.getID(),userID=self.moderator().get_userid)}"

    @property
    def getJudgeCertLink(self) -> str:
        """Get the link to the view page of certificate of the judge of this competition. 
        Link path contains empty (*) for judge userID to be filled by the invoker.

        Returns:
            str: The link to the view page of certificate of the judge of this competition.
        """
        return f"{url.getRoot(APPNAME)}{url.compete.apprCertificate(compID=self.getID(),userID='*')}"

    def latest_competition() -> "Competition":
        cacheKey = "latest_competition"
        competition = cache.get(cacheKey, None)
        if not competition:
            competition = Competition.objects.filter(endAt__gt=timezone.now(),
                                                     is_draft=False, resultDeclared=False).order_by("-startAt").first()
            cache.set(cacheKey, competition, settings.CACHE_MINI)
        return competition


class Perk(models.Model):
    """
    Prize of a competition
    """
    class Meta:
        unique_together = ("competition", "rank")

    id: UUID = models.UUIDField(
        primary_key=True, default=uuid4, editable=False)
    competition: Competition = models.ForeignKey(
        Competition, related_name='perk_competition', on_delete=models.CASCADE)
    """competition (ForeignKey<Competition>): The competition this perk belongs to."""
    rank: int = models.IntegerField(default=1)
    """rank (IntegerField): The rank of this perk."""
    name: str = models.CharField(max_length=1000)
    """name (CharField): The name of this perk."""


class CompetitionJudge(models.Model):
    """
    The model for many to many relationship between Competition and Judge.

    """
    id: UUID = models.UUIDField(
        primary_key=True, default=uuid4, editable=False)
    competition: Competition = models.ForeignKey(
        Competition, related_name='judging_competition', on_delete=models.PROTECT)
    """competition (ForeignKey<Competition>): The competition of this relation."""
    judge: Profile = models.ForeignKey(Profile, on_delete=models.PROTECT)
    """judge (ForeignKey<Profile>): The judge of this relation."""

    class Meta:
        unique_together = ("competition", "judge")

    def __str__(self) -> str:
        return self.competition.title

    @property
    def get_cert_link(self) -> str:
        """Get the link to the view page of certificate of this judge for the associated competition.

        Returns:
            str: The link to the view page of certificate of this judge for the associated competition.
        """
        return f"{url.getRoot(APPNAME)}{url.compete.apprCertificate(self.competition.get_id,self.judge.get_userid)}"


class CompetitionTopic(models.Model):
    """
    The model for many to many relationship between Competition and Topic.
    """
    class Meta:
        unique_together = ("competition", "topic")
    id: UUID = models.UUIDField(
        primary_key=True, default=uuid4, editable=False)
    competition: Competition = models.ForeignKey(
        Competition, on_delete=models.CASCADE, related_name='competition_topic')
    """competition (ForeignKey<Competition>): The competition of this relation."""
    topic: Topic = models.ForeignKey(
        Topic, on_delete=models.CASCADE, related_name='topic_competition')
    """topic (ForeignKey<Topic>): The topic of this relation."""

    def __str__(self) -> str:
        return self.competition.title


class Submission(models.Model):
    """
    Submission of a competition, including participant(s).
    """
    id: UUID = models.UUIDField(
        primary_key=True, default=uuid4, editable=False)
    competition: Competition = models.ForeignKey(
        Competition, on_delete=models.PROTECT)
    """competition (ForeignKey<Competition>): The competition of this submission."""
    members = models.ManyToManyField(
        Profile, through='SubmissionParticipant', related_name='submission_participants')
    """members (ManyToManyField<Profile>): The participants of this submission."""
    repo: str = models.URLField(max_length=1000, blank=True, null=True)
    """repo (URLField): Deprecated. Use free_project only."""
    free_project: FreeProject = models.ForeignKey(
        FreeProject, on_delete=models.SET_NULL, null=True, blank=True)
    """free_project (ForeignKey<FreeProject>): The free project of this submission."""
    submitted: bool = models.BooleanField(default=False)
    """submitted (BooleanField): Whether this submission is submitted."""
    createdOn: datetime = models.DateTimeField(
        auto_now=False, default=timezone.now)
    """createdOn (DateTimeField): The time this submission was created."""
    modifiedOn: datetime = models.DateTimeField(
        auto_now=False, default=timezone.now)
    """modifiedOn (DateTimeField): The time this submission was last modified."""
    submitOn: datetime = models.DateTimeField(
        auto_now=False, blank=True, null=True)
    """submitOn (DateTimeField): The time this submission was submitted."""
    valid: bool = models.BooleanField(default=True)
    """valid (BooleanField): Whether this submission is valid."""
    late: bool = models.BooleanField(default=False)
    """late (BooleanField): Whether this submission is late."""

    def __str__(self) -> str:
        return f"{self.competition.title} - {self.getID()}"

    @property
    def get_id(self) -> str:
        return self.id.hex

    def getID(self) -> str:
        return self.get_id

    @property
    def get_compid(self) -> str:
        return self.competition.get_id

    def getCompID(self) -> str:
        return self.get_compid

    def save(self, *args, **kwargs):
        self.modifiedOn = timezone.now()
        return super(Submission, self).save(*args, **kwargs)

    def saveLink(self) -> str:
        """Get the link to save the submission, to be used by members via POST.

        Returns:
            str: The link to save the submission.
        """

        return f"{url.getRoot(APPNAME)}{url.compete.save(compID=self.getCompID(),subID=self.getID())}"

    def totalMembers(self) -> int:
        """Get the total number of members in this submission, regardless of confirmation

        Returns:
            int: The total number of members in this submission, regardless of confirmation.
        """
        return self.members.count()

    def isMember(self, profile: Profile) -> bool:
        """Check if the given profile is a confirmed member of this submission.

        Args:
            profile (Profile): The profile to check.

        Returns:
            bool: Whether the given profile is a confirmed member of this submission.
        """
        try:
            SubmissionParticipant.objects.get(
                submission=self, profile=profile, confirmed=True)
            return True
        except:
            return False

    def getMembers(self) -> list:
        """Get the list of confirmed member Profile instances in this submission.

        Returns:
            list<Profile>: The list of confirmed member Profile instances in this submission.
        """
        return list(map(lambda x: x.profile, SubmissionParticipant.objects.filter(submission=self, confirmed=True)))

    def getMembersEmail(self) -> list:
        """Get the list of confirmed member email addresses in this submission.

        Returns:
            list<str>: The list of confirmed member email addresses in this submission.
        """
        return list(map(lambda x: x.profile.getEmail(), SubmissionParticipant.objects.filter(submission=self, confirmed=True)))

    def totalActiveMembers(self) -> int:
        """Get the total number of confirmed members in this submission.

        Returns:
            int: The total number of confirmed members in this submission.
        """
        return SubmissionParticipant.objects.filter(submission=self, confirmed=True).count()

    def memberOrMembers(self) -> str:
        """Get the string to describe the number of members in this submission."""
        return 'member' if self.totalActiveMembers() == 1 else 'members'

    def isInvitee(self, profile: Profile) -> bool:
        """Check if the given profile is an invitee of this submission.

        Args:
            profile (Profile): The profile to check.

        Returns:
            bool: Whether the given profile is an invitee of this submission.
        """
        try:
            SubmissionParticipant.objects.get(
                submission=self, profile=profile, confirmed=False)
            return True
        except:
            return False

    def getInvitees(self) -> list:
        """Get the list of invitee Profile instances in this submission.

        Returns:
            list<Profile>: The list of invitee Profile instances in this submission.
        """
        invitees = []
        relations = SubmissionParticipant.objects.filter(
            submission=self, confirmed=False)
        for relation in relations:
            invitees.append(relation.profile)
        return invitees

    def canInvite(self) -> bool:
        """Whether this submission can invite more members or not, depending on current totalmembers, submission status & competition status.

        Returns:
            bool: Whether this submission can invite more members or not.
        """
        return (self.totalMembers() < self.competition.max_grouping) and not self.submitted and self.competition.isActive()

    def getRepo(self) -> str:
        """Get the submitted project's url.

        Returns:
            str: The submitted project's url.
        """
        if self.free_project:
            return self.free_project.get_link
        return self.repo if self.repo else ''

    def submittingLate(self) -> bool:
        """Submitting late or not.
        NOTE: This method only represents 'late' status of submission before it has been submitted.
        After submission, the response of this method must not be considered reliable, instead the 'late' field should be used.

        Returns:
            bool: Whether this submission is submitting late or not.
        """
        return self.competition.isHistory() and not self.submitted

    def pointedTopicsByJudge(self, judge: Profile) -> int:
        """Get the number of pointed topics by the given judge.

        Args:
            judge (Profile): The judge to check.

        Returns:
            int: The number of pointed topics by the given judge.
        """
        return SubmissionTopicPoint.objects.filter(submission=self, judge=judge).count()

    def is_winner(self) -> bool:
        """Check if this submission is the winner.

        Returns:
            bool: Whether this submission is the winner.
        """
        return Result.objects.filter(submission=self, competition=self.competition, rank=1).exists()


class SubmissionParticipant(models.Model):
    """
    The model for many to many relationship between Submission and Profile.
    """
    class Meta:
        unique_together = ("profile", "submission")

    id: UUID = models.UUIDField(
        primary_key=True, default=uuid4, editable=False)
    submission: Submission = models.ForeignKey(
        Submission, on_delete=models.CASCADE, related_name='participant_submission')
    """submission (ForeignKey<Submission>): The submission in this relationship."""
    profile: Profile = models.ForeignKey(
        Profile, on_delete=models.PROTECT, related_name='participant_profile')
    """profile (ForeignKey<Profile>): The profile in this relationship."""
    confirmed: bool = models.BooleanField(default=False)
    """confirmed (BooleanField): Whether this relationship is confirmed or not."""
    confirmed_on: datetime = models.DateTimeField(
        auto_now=False, null=True, blank=True)
    """confirmed_on (DateTimeField): The time when this relationship is confirmed."""

    def save(self, *args, **kwargs):
        if self.confirmed:
            if SubmissionParticipant.objects.filter(id=self.id, confirmed=False).exists():
                self.confirmed_on = timezone.now()
        super(SubmissionParticipant, self).save(
            *args, **kwargs)


class SubmissionTopicPoint(models.Model):
    """
    For each topic, points marked by each judge for each submission in a competition.
    """
    class Meta:
        unique_together = (("submission", "judge", "topic"))

    id: UUID = models.UUIDField(
        primary_key=True, default=uuid4, editable=False)
    submission: Submission = models.ForeignKey(
        Submission, on_delete=models.PROTECT)
    """submission (ForeignKey<Submission>): The submission in this relationship."""
    topic: Topic = models.ForeignKey(Topic, on_delete=models.PROTECT)
    """topic (ForeignKey<Topic>): The topic in this relationship."""
    judge: Profile = models.ForeignKey(Profile, on_delete=models.PROTECT)
    """judge (ForeignKey<Profile>): The judge in this relationship."""
    points: int = models.IntegerField(default=0)
    """points (IntegerField): The points assigned by the judge in and for this relationship."""

    def __str__(self) -> str:
        return self.submission.getID()


class Result(models.Model):
    """
    Rank and total points obtained by a submission in a competition.
    """
    class Meta:
        unique_together = (("competition", "rank"),
                           ("competition", "submission"))

    id: UUID = models.UUIDField(
        primary_key=True, default=uuid4, editable=False)
    competition: Competition = models.ForeignKey(
        Competition, on_delete=models.PROTECT)
    """competition (ForeignKey<Competition>): The competition of this result."""
    submission: Submission = models.OneToOneField(
        Submission, on_delete=models.PROTECT)
    """submission (OneToOneField<Submission>): The submission of this result."""
    points: int = models.IntegerField(default=0)
    """points (IntegerField): The total points obtained by the submission."""
    rank: int = models.IntegerField()
    """rank (IntegerField): The rank of the submission."""
    xpclaimers = models.ManyToManyField(
        Profile, through='ResultXPClaimer', related_name='result_xpclaimers', default=[])
    """xpclaimers (ManyToManyField<Profile>): The profiles who have successfully claimed their XPs."""
    certificates = models.ManyToManyField(
        Profile, through='ParticipantCertificate', related_name='result_certificates', default=[])
    """certificates (ManyToManyField<Profile>): The profiles who have successfully received their certificates."""

    def __str__(self) -> str:
        return f"{self.competition} - {self.rank}{self.rankSuptext()}"

    @property
    def get_id(self) -> str:
        return self.id.hex

    def getID(self) -> str:
        return self.get_id

    def submitOn(self) -> datetime:
        return self.submission.submitOn

    def rankSuptext(self, rank: int = 0) -> str:
        """Get the rank's human readable format suffix only.

        Args:
            rank (int, optional): The rank suffix to get. Defaults to the rank suffix of this result.
        """
        return getNumberSuffix(int(rank or self.rank or 0))

    def getRank(self, rank: int = 0) -> str:
        """Get the rank in human readable format.

        Args:
            rank (int, optional): The rank to get. Defaults to the rank of this result.
        """
        return getNumberSuffix(int(rank or self.rank or 0), True)

    def hasClaimedXP(self, profile: Profile) -> bool:
        """Check if the given profile has claimed their XPs.

        Args:
            profile (Profile): The profile to check.

        Returns:
            bool: Whether the given profile has claimed their XPs.
        """
        return profile in self.xpclaimers.all()

    def getClaimXPLink(self) -> str:
        """Get the link to claim XP, to be used by participant via POST.

        Returns:
            str: The link to claim XP.
        """
        return f"{url.getRoot(APPNAME)}{url.compete.claimXP(self.competition.get_id,self.submission.get_id)}"

    def allXPClaimed(self) -> bool:
        """Check if all the participants have claimed their XPs.

        Returns:
            bool: Whether all the participants have claimed their XPs.
        """
        return self.submission.totalMembers() == self.xpclaimers.count

    def getCertLink(self) -> str:
        """Get the link to the certificate view of individual participant.
        Link path contains empty (*) for participant userID to be filled by the invoker.

        Returns:
            str: The link to the certificate view of individual participant.
        """
        return f"{url.getRoot(APPNAME)}{url.compete.certificate(resID=self.get_id,userID='*')}"

    def getCertDownloadLink(self) -> str:
        """Get the link to download the certificate of individual participant.
        Link path contains empty (*) for participant userID to be filled by the invoker.

        Returns:
            str: The link to download the certificate of individual participant.
        """
        return f"{url.getRoot(APPNAME)}{url.compete.certificateDownload(resID=self.get_id,userID='*')}"

    def getMembers(self) -> list:
        """Get the list of member Profile instances of this result, effectively the members in this submission.

        Returns:
            list<Profile>: The members of this result.
        """
        return self.submission.getMembers()

    @property
    def topic_points(self) -> dict:
        """Get the topic vs points of this result.

        Returns:
            dict: The topic vs points of this result.
        """
        cacheKey = f"submission_topic_score_result_{self.id}"
        topicscore = cache.get(cacheKey, None)
        if not topicscore:
            topicscore = SubmissionTopicPoint.objects.filter(submission=self.submission).values(
                'topic__id', 'topic__name').annotate(score=Sum('points'))
            cache.set(cacheKey, topicscore, settings.CACHE_MAX)
        return topicscore


class ResultXPClaimer(models.Model):
    """
    The relationship between a result and a profile who has claimed their XPs.
    """
    class Meta:
        unique_together = ("result", "profile")

    id: UUID = models.UUIDField(
        primary_key=True, default=uuid4, editable=False)
    result: Result = models.ForeignKey(
        Result, on_delete=models.PROTECT, related_name='xpclaimer_result')
    """result (ForeignKey<Result>): The result in this relationship."""
    profile: Profile = models.ForeignKey(
        Profile, on_delete=models.PROTECT, related_name='xpclaimer_profile')
    """profile (ForeignKey<Profile>): The profile in this relationship."""


class ParticipantCertificate(models.Model):
    """
    The model of certificate of a result of a particpant
    """
    class Meta:
        unique_together = ("result", "profile")

    id: UUID = models.UUIDField(
        primary_key=True, default=uuid4, editable=False)
    result: Result = models.ForeignKey(
        Result, on_delete=models.PROTECT, related_name='participant_certificate_result')
    """result (ForeignKey<Result>): The result of a competition."""
    profile: Profile = models.ForeignKey(
        Profile, on_delete=models.PROTECT, related_name='participant_certificate_profile')
    """profile (ForeignKey<Profile>): The participant profile of a competition."""
    certificate: str = models.CharField(
        default='', null=True, blank=True, max_length=1000)
    """certificate (CharField): The certificate of a participant."""

    @property
    def certficateImage(self) -> str:
        """Get the certificate path as image.

        Returns:
            str: The certificate path as image.
        """
        return f"{str(self.certificate).replace('.pdf','.jpg')}" if self.certificate else None

    @property
    def get_id(self) -> str:
        return self.id.hex

    @property
    def get_link(self) -> str:
        """Get the link to the certificate view

        Returns:
            str: The link to the certificate view.
        """
        return f"{url.getRoot(APPNAME)}{url.compete.certificate(resID=self.result.get_id,userID=self.profile.get_userid)}"

    @property
    def get_download_link(self) -> str:
        """Get the link to download the certificate

        Returns:
            str: The link to download the certificate
        """
        return f"{url.getRoot(APPNAME)}{url.compete.certificateDownload(resID=self.result.get_id,userID=self.profile.get_userid)}"

    @property
    def getCertImage(self) -> str:
        """Get the certificate image URL.

        Returns:
            str: The certificate image URL.
        """
        return f"{settings.MEDIA_URL}{str(self.certificate).replace('.pdf','.jpg')}" if self.certificate else None

    @property
    def getCert(self) -> str:
        """Get the certificate URL.

        Returns:
            str: The certificate URL.
        """
        return f"{settings.MEDIA_URL}{str(self.certificate)}"

    def getCertificate(self) -> str:
        return self.getCert


class AppreciationCertificate(models.Model):
    class Meta:
        unique_together = ("competition", "appreciatee")

    id: UUID = models.UUIDField(
        primary_key=True, default=uuid4, editable=False)
    competition: Competition = models.ForeignKey(
        Competition, on_delete=models.PROTECT, related_name='appreciation_certificate_competition')
    appreciatee: Profile = models.ForeignKey(
        Profile, on_delete=models.PROTECT, related_name='appreciation_certificate_profile')
    certificate: str = models.CharField(
        default='', null=True, blank=True, max_length=1000)

    @property
    def certficateImage(self) -> str:
        """Get the certificate path as image.

        Returns:
            str: The certificate path as image.
        """
        return f"{str(self.certificate).replace('.pdf','.jpg')}" if self.certificate else None

    @property
    def get_id(self) -> str:
        return self.id.hex

    @property
    def get_link(self) -> str:
        """Get the link to the certificate view

        Returns:
            str: The link to the certificate view.
        """
        return f"{url.getRoot(APPNAME)}{url.compete.apprCertificate(compID=self.competition.getID(),userID=self.appreciatee.get_userid)}"

    @property
    def get_download_link(self) -> str:
        """Get the link to download the certificate

        Returns:
            str: The link to download the certificate
        """
        return f"{url.getRoot(APPNAME)}{url.compete.apprCertificateDownload(compID=self.competition.getID(),userID=self.appreciatee.get_userid)}"

    @property
    def getCertImage(self) -> str:
        """Get the certificate image URL.

        Returns:
            str: The certificate image URL.
        """
        return f"{settings.MEDIA_URL}{str(self.certificate).replace('.pdf','.jpg')}"

    @property
    def getCertificate(self) -> str:
        """Get the certificate URL.

        Returns:
            str: The certificate URL.
        """
        return f"{settings.MEDIA_URL}{str(self.certificate)}"


class SubmissionTeamInvitation(Invitation):
    """
    The model of an invitation to join a submission team for a profile.
    """
    sender: Profile = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name='team_invitation_sender')
    """sender (ForeignKey<Profile>): The sender of the invitation."""
    receiver: Profile = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name='team_invitation_receiver')
    """receiver (ForeignKey<Profile>): The receiver of the invitation."""
    submission: Submission = models.ForeignKey(
        Submission, on_delete=models.CASCADE, related_name='invitation_submission')
    """submission (ForeignKey<Submission>): The submission for which the invitation is."""

    class Meta:
        unique_together = ('sender', 'receiver', 'submission')


class CompetitionAdmirer(models.Model):
    """The model relation between a competition and an admirer"""
    id: UUID = models.UUIDField(
        primary_key=True, default=uuid4, editable=False)
    compete: Competition = models.ForeignKey(
        Competition, on_delete=models.CASCADE, related_name='compete_admirer_competition')
    admirer: Profile = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name='compete_admirer_profile')
    createdOn: datetime = models.DateTimeField(
        auto_now=False, default=timezone.now)
