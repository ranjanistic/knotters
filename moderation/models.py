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
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    project = models.ForeignKey(
        f"{PROJECTS}.Project", on_delete=models.CASCADE, blank=True, null=True, related_name="moderation_project")
    coreproject = models.ForeignKey(
        f"{PROJECTS}.CoreProject", on_delete=models.CASCADE, blank=True, null=True, related_name="moderation_coreproject")

    profile = models.ForeignKey(f"{PEOPLE}.Profile", blank=True, null=True,
                                on_delete=models.CASCADE, related_name="moderation_profile")

    competition = models.ForeignKey(
        f"{COMPETE}.Competition", blank=True, null=True, on_delete=models.CASCADE, related_name="moderation_compete")

    type = models.CharField(choices=moderation.TYPECHOICES,
                            max_length=maxLengthInList(moderation.TYPES))

    moderator = models.ForeignKey(
        f"{PEOPLE}.Profile", on_delete=models.CASCADE, related_name="moderator_profile")

    request = models.CharField(max_length=100000)
    referURL = models.URLField(blank=True, null=True)
    response = models.CharField(
        max_length=100000, blank=True, null=True, default='')

    status = models.CharField(choices=moderation.MODSTATESCHOICES, max_length=maxLengthInList(
        moderation.MODSTATES), default=Code.MODERATION)

    requestOn = models.DateTimeField(auto_now=False, default=timezone.now)
    respondOn = models.DateTimeField(auto_now=False, null=True, blank=True)
    resolved = models.BooleanField(default=False)
    stale_days = models.IntegerField(default=3)
    internal_mod = models.BooleanField(default=False)

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
        if self.type in [PROJECTS, CORE_PROJECT]:
            return self.project
        elif self.type == PEOPLE:
            return self.profile
        elif self.type == COMPETE:
            return self.competition
        else:
            return None

    def getLink(self, alert: str = '', error: str = '', success: str = '') -> str:
        return f"{url.getRoot(APPNAME)}{url.moderation.modID(modID=self.get_id)}{url.getMessageQuery(alert,error,success)}"

    @property
    def is_stale(self):
        """
        No response for consecutive stale_days or 3
        """
        # return True
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
        return f"{url.getRoot(APPNAME)}{url.moderation.reapply(modID=self.getID())}"

    def approveCompeteLink(self):
        return f"{url.getRoot(APPNAME)}{url.moderation.approveCompete(modID=self.getID())}"

    @property
    def requestor(self) -> bool:
        if self.type == PROJECTS:
            return self.project.creator
        if self.type == PEOPLE:
            return self.profile
        if self.type == COMPETE:
            return self.competition.creator
        if self.type == CORE_PROJECT:
            return self.coreproject.creator

    def isRequestor(self, profile) -> bool:
        if self.type in [PROJECTS, CORE_PROJECT]:
            return profile == self.requestor
        if self.type == PEOPLE:
            return self.profile == profile
        if self.type == COMPETE:
            return self.competition.isJudge(profile) or self.requestor == profile

    def isPending(self) -> bool:
        return self.status == Code.MODERATION and not self.resolved

    def isRejected(self) -> bool:
        return self.status == Code.REJECTED and self.resolved

    def isApproved(self) -> bool:
        return self.status == Code.APPROVED and self.resolved

    def getModerateeFieldByType(self, type: str = '') -> models.Model:
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

    def getImageByType(self):
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
        self.moderator.increaseXP(by=5)
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
        self.save()
        return True

    def revertApproval(self) -> bool:
        if self.revertRespond():
            self.moderator.decreaseXP(by=5)
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
        self.save()
        return True


class LocalStorage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    key = models.CharField(max_length=100, blank=False,
                           null=False, unique=True)
    value = models.CharField(max_length=5000, blank=False, null=False)

    def __str__(self) -> str:
        return self.key


class ReportedModeration(models.Model):
    class Meta:
        unique_together = ('profile', 'moderation', 'category')

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    profile = models.ForeignKey(
        f'{PEOPLE}.Profile', on_delete=models.CASCADE, related_name='moderation_reporter_profile')
    moderation = models.ForeignKey(
        Moderation, on_delete=models.CASCADE, related_name='reported_moderation')
    category = models.ForeignKey(
        ReportCategory, on_delete=models.PROTECT, related_name='reported_moderation_category')
