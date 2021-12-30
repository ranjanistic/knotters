from django.db import models
from uuid import uuid4
from django.utils import timezone
from datetime import timedelta
from main.strings import Code, url, PROJECTS, PEOPLE, COMPETE, moderation
from main.methods import maxLengthInList
from main.exceptions import IllegalModerationEntity
from management.models import ReportCategory
from django.utils import timezone
from .apps import APPNAME


class Moderation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    project = models.ForeignKey(
        f"{PROJECTS}.Project", on_delete=models.CASCADE, blank=True, null=True, related_name="moderation_project")

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

    def __str__(self):
        if self.type == PROJECTS:
            return self.project.name
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
        if self.type == PROJECTS:
            return self.project
        elif self.type == PEOPLE:
            return self.profile
        elif self.type == COMPETE:
            return self.competition
        else: return None

    def getLink(self, alert: str = '', error: str = '', success: str = '') -> str:
        return f"{url.getRoot(APPNAME)}{url.moderation.modID(modID=self.getID())}{url.getMessageQuery(alert,error,success)}"

    @property
    def is_stale(self):
        """
        No response for 3 consecutive days
        """
        if self.resolved: return False
        stale_days = 3
        if self.project: stale_days = self.project.stale_days
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

    def isRequestor(self, profile) -> bool:
        if self.type == PROJECTS:
            return profile == self.project.creator
        if self.type == PEOPLE:
            return self.profile.isReporter(profile)
        if self.type == COMPETE:
            return self.competition.isJudge(profile)

    def isPending(self) -> bool:
        return self.status == Code.MODERATION

    def isRejected(self) -> bool:
        return self.status == Code.REJECTED

    def isApproved(self) -> bool:
        return self.status == Code.APPROVED

    def getModerateeFieldByType(self, type: str = '') -> models.Model:
        type = type if type else self.type
        if type == PROJECTS and self.project:
            return self.project
        elif type == COMPETE and self.competition:
            return self.competition
        elif type == PEOPLE and self.profile:
            return self.profile
        else:
            raise IllegalModerationEntity()

    def approve(self) -> bool:
        now = timezone.now()
        self.status = Code.APPROVED
        self.respondOn = now
        if self.type == PROJECTS:
            self.project.status = Code.APPROVED
            self.project.approvedOn = now
            self.project.save()
        self.resolved = True
        self.moderator.increaseXP(by=5)
        self.save()
        return True

    def revertApproval(self) -> bool:
        self.status = Code.MODERATION
        self.respondOn = None
        if self.type == PROJECTS:
            self.project.status = Code.MODERATION
            self.project.approvedOn = None
            self.project.save()
        self.resolved = False
        self.moderator.decreaseXP(by=5)
        self.save()
        return True

    def reject(self) -> bool:
        self.status = Code.REJECTED
        self.respondOn = timezone.now()
        if self.type == PROJECTS:
            self.project.status = Code.REJECTED
            self.project.save()
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
    profile = models.ForeignKey(f'{PEOPLE}.Profile', on_delete=models.CASCADE, related_name='moderation_reporter_profile')
    moderation = models.ForeignKey(Moderation, on_delete=models.CASCADE, related_name='reported_moderation')
    category = models.ForeignKey(ReportCategory, on_delete=models.PROTECT, related_name='reported_moderation_category')
