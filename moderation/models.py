from datetime import timedelta
from uuid import uuid4

from django.db import models
from django.utils import timezone
from main.exceptions import IllegalModerationEntity
from main.methods import maxLengthInList
from main.strings import (COMPETE, CORE_PROJECT, PEOPLE, PROJECTS, Code,
                          moderation, url)
from management.models import ReportCategory

from .apps import APPNAME


class Moderation(models.Model):
    """The model for moderation instance.

    NOTE/TODO: Need Subclasses for each type of moderation.
        Currently using one class for all types by setting the type field and other instances attributes for other types as None.
    """
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    project = models.ForeignKey(
        f"{PROJECTS}.Project", on_delete=models.CASCADE, blank=True, null=True, related_name="moderation_project")
    """project (ForeignKey<Project>): The verified project that is being moderated."""
    coreproject = models.ForeignKey(
        f"{PROJECTS}.CoreProject", on_delete=models.CASCADE, blank=True, null=True, related_name="moderation_coreproject")
    """coreproject (ForeignKey<CoreProject>): The core project that is being moderated."""

    profile = models.ForeignKey(f"{PEOPLE}.Profile", blank=True, null=True,
                                on_delete=models.CASCADE, related_name="moderation_profile")
    """profile (ForeignKey<Profile>): The profile that is being moderated. Not of any use currently."""

    competition = models.ForeignKey(
        f"{COMPETE}.Competition", blank=True, null=True, on_delete=models.CASCADE, related_name="moderation_compete")
    """competition (ForeignKey<Competition>): The competition that is being moderated."""

    type = models.CharField(choices=moderation.TYPECHOICES,
                            max_length=maxLengthInList(moderation.TYPES))
    """type (CharField<str>): The type of moderation."""

    moderator = models.ForeignKey(
        f"{PEOPLE}.Profile", on_delete=models.CASCADE, related_name="moderator_profile")
    """moderator (ForeignKey<Profile>): The moderator who is assigned to the moderation."""

    request = models.CharField(max_length=100000)
    """request (CharField<str>): The request data for the moderation."""
    referURL = models.URLField(blank=True, null=True)
    """referURL (URLField<str>): The URL for moderator to refer to, set by requestor."""
    response = models.CharField(
        max_length=100000, blank=True, null=True, default='')
    """response (CharField<str>): The moderator's response for the moderation."""

    status = models.CharField(choices=moderation.MODSTATESCHOICES, max_length=maxLengthInList(
        moderation.MODSTATES), default=Code.MODERATION)
    """status (CharField<str>): The status of the moderation."""

    requestOn = models.DateTimeField(auto_now=False, default=timezone.now)
    """requestOn (DateTimeField<datetime>): The date and time the moderation was requested."""
    respondOn = models.DateTimeField(auto_now=False, null=True, blank=True)
    """respondOn (DateTimeField<datetime>): The date and time the moderation was last responded."""
    resolved = models.BooleanField(default=False)
    """resolved (BooleanField<bool>): Whether the moderation is resolved."""
    stale_days = models.IntegerField(default=3)
    """stale_days (IntegerField<int>): The number of days before a moderation is considered stale."""
    internal_mod = models.BooleanField(default=False)
    """internal_mod (BooleanField<bool>): Whether the moderation is internal (inside management)."""

    def __str__(self):
        if self.type == PROJECTS:
            return self.project.name
        if self.type == CORE_PROJECT:
            return self.coreproject.name
        elif self.type == PEOPLE:
            return self.profile.getName()
        elif self.type == COMPETE:
            return self.competition.title

    @property
    def get_id(self) -> str:
        return self.id.hex

    def getID(self) -> str:
        return self.get_id

    @property
    def object(self) -> models.Model:
        """Returns the object/instance that is being moderated, depending on the type of moderation.

        Returns:
            models.Model: The object/instance that is being moderated. [Project, CoreProject, Profile, Competition]
        """
        if self.type in [PROJECTS, CORE_PROJECT]:
            return self.project
        elif self.type == PEOPLE:
            return self.profile
        elif self.type == COMPETE:
            return self.competition
        else:
            return None

    def getLink(self, alert: str = '', error: str = '', success: str = '') -> str:
        """Returns the link to the moderation view
        """
        return f"{url.getRoot(APPNAME)}{url.moderation.modID(modID=self.get_id)}{url.getMessageQuery(alert,error,success)}"

    @property
    def is_stale(self) -> bool:
        """No response for consecutive stale_days or 3

        Returns:
            bool: Whether the moderation is stale.
        """
        if self.resolved:
            return False
        stale_days = self.stale_days or 3
        if not self.respondOn:
            if timezone.now() > (self.requestOn + timedelta(days=stale_days)):
                return True
        elif timezone.now() > (self.respondOn + timedelta(days=stale_days)):
            return True
        return False

    def reapplyLink(self):
        """Returns the link to reapply the moderation, primarily to be used by requestor via POST method.

        Returns:
            str: The link to reapply the moderation.
        """
        return f"{url.getRoot(APPNAME)}{url.moderation.reapply(modID=self.getID())}"

    def approveCompeteLink(self):
        """Returns the link to approve the competition, primarily to be used by moderator via POST method.

        Returns:
            str: The link to approve the competition.
        """
        return f"{url.getRoot(APPNAME)}{url.moderation.approveCompete(modID=self.getID())}"

    @property
    def requestor(self) -> bool:
        """Returns the profile instance of the moderation requestor, depending on the type of moderation.

        Returns:
            Profile: The requestor profile instance of the moderation requestor.
        """
        if self.type == PROJECTS:
            return self.project.creator
        if self.type == PEOPLE:
            return self.profile
        if self.type == COMPETE:
            return self.competition.creator
        if self.type == CORE_PROJECT:
            return self.coreproject.creator

    def isRequestor(self, profile) -> bool:
        """Returns whether the profile is the requestor of the moderation.

        Args:
            profile (Profile): The profile to check.

        Returns:
            bool: Whether the profile is the requestor of the moderation.
        """
        if self.type in [PROJECTS, CORE_PROJECT]:
            return profile == self.requestor
        if self.type == PEOPLE:
            return self.profile == profile
        if self.type == COMPETE:
            return self.competition.isJudge(profile) or self.requestor == profile

    def isPending(self) -> bool:
        """Returns whether the moderation is pending."""
        return self.status == Code.MODERATION and not self.resolved

    def isRejected(self) -> bool:
        """Returns whether the moderation is rejected."""
        return self.status == Code.REJECTED and self.resolved

    def isApproved(self) -> bool:
        """Returns whether the moderation is approved."""
        return self.status == Code.APPROVED and self.resolved

    def getModerateeFieldByType(self, type: str = '') -> models.Model:
        """Returns the object model instance of the moderation, depending on the given of moderation.

        Args:
            type (str): The type of moderation. [PROJECTS, CORE_PROJECT, PEOPLE, COMPETE]

        Raises:
            IllegalModerationEntity: If the type is not valid.

        Returns:
            models.Model: The object model instance of the moderation. [Project, CoreProject, Profile, Competition]
        """
        type = type if type else self.type
        if type == PROJECTS and self.project:
            return self.project
        elif type == CORE_PROJECT and self.coreproject:
            return self.coreproject
        elif type == COMPETE and self.competition:
            return self.competition
        elif type == PEOPLE and self.profile:
            return self.profile
        else:
            raise IllegalModerationEntity(type)

    def getImageByType(self) -> str:
        """Returns the image URL of the moderation object, depending on the type of moderation.

        Returns:
            str: The image URL of the moderation object.
        """
        if type == PROJECTS and self.project:
            return self.project.get_dp
        elif type == CORE_PROJECT and self.coreproject:
            return self.coreproject.get_dp
        elif type == COMPETE and self.competition:
            return self.competition.get_banner
        elif type == PEOPLE and self.profile:
            return self.profile.get_dp
        else:
            return None

    def approve(self) -> bool:
        """Approves the moderation.

        Returns:
            bool: Whether the moderation was approved.
        """
        now = timezone.now()
        self.status = Code.APPROVED
        self.respondOn = now
        if self.type == PROJECTS:
            self.project.status = Code.APPROVED
            self.project.approvedOn = now
            self.project.save()
        elif self.type == CORE_PROJECT:
            self.coreproject.status = Code.APPROVED
            self.coreproject.approvedOn = now
            self.coreproject.save()
        self.resolved = True
        self.moderator.increaseXP(
            by=3, reason=f'Took action on moderation {self.__str__()}')
        self.save()
        return True

    def revertRespond(self) -> bool:
        self.status = Code.MODERATION
        if self.type == PROJECTS:
            self.project.status = Code.MODERATION
            self.project.approvedOn = None
            self.project.save()
        elif self.type == CORE_PROJECT:
            self.coreproject.status = Code.MODERATION
            self.coreproject.approvedOn = None
            self.coreproject.save()
        self.resolved = False
        self.moderator.decreaseXP(by=3)
        self.save()
        return True

    def revertApproval(self) -> bool:
        if self.revertRespond():
            self.moderator.decreaseXP(by=3)
            return True
        return False

    def reject(self) -> bool:
        self.status = Code.REJECTED
        self.respondOn = timezone.now()
        if self.type == PROJECTS:
            self.project.status = Code.REJECTED
            self.project.save()
        elif self.type == CORE_PROJECT:
            self.coreproject.status = Code.REJECTED
            self.coreproject.save()
        self.resolved = True
        self.moderator.increaseXP(
            by=3, reason=f'Took action on moderation {self.__str__()}')
        self.save()
        return True


class LocalStorage(models.Model):
    """The local storage model for application usage."""
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    key = models.CharField(max_length=100, blank=False,
                           null=False, unique=True)
    """key (str): The key of the local storage."""
    value = models.CharField(max_length=5000, blank=False, null=False)
    """value (str): The value of the local storage."""

    def __str__(self) -> str:
        return self.key


class ReportedModeration(models.Model):
    """The reported moderation model."""
    class Meta:
        unique_together = ('profile', 'moderation', 'category')

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    profile = models.ForeignKey(
        f'{PEOPLE}.Profile', on_delete=models.CASCADE, related_name='moderation_reporter_profile')
    """profile (Profile): The profile who reported the moderation."""
    moderation = models.ForeignKey(
        Moderation, on_delete=models.CASCADE, related_name='reported_moderation')
    """moderation (Moderation): The reported moderation."""
    category = models.ForeignKey(
        ReportCategory, on_delete=models.PROTECT, related_name='reported_moderation_category')
    """category (ReportCategory): The category of the reported moderation."""
