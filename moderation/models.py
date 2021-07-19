from django.db import models
from uuid import uuid4
from main.strings import Code, url, PROJECTS, PEOPLE, COMPETE, moderation, message
from main.methods import maxLengthInList
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
        if self.type == PEOPLE:
            return self.profile.getName()
        if self.type == COMPETE:
            return self.competition.title
        return self.getID()

    def getID(self) -> str:
        return self.id.hex

    def approve(self) -> bool:
        now = timezone.now()
        self.status = Code.APPROVED
        self.respondOn = now
        if self.type == PROJECTS:
            self.project.status = Code.APPROVED
            self.project.approvedOn = now
            self.project.save()
        self.resolved = True
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

    def getLink(self, alert:str='', error:str='') -> str:
        return f"{url.getRoot(APPNAME)}{url.moderation.modID(modID=self.getID())}{url.getMessageQuery(alert,error)}"

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


class LocalStorage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    key = models.CharField(max_length=100, blank=False, null=False)
    value = models.CharField(max_length=5000, blank=False, null=False)

    def __str__(self):
        return self.key
