from django.db import models
from uuid import uuid4
from people.models import Profile
from projects.models import Project
from compete.models import Competition
from main.strings import PROJECTS, PEOPLE, COMPETE, DIVISIONS, code
from main.methods import maxLengthInList
from django.utils import timezone
from .apps import APPNAME

class Moderation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, blank=True)
    profile = models.ForeignKey(Profile, blank=True,
                                on_delete=models.CASCADE, related_name="moderation_profile")
    competition = models.ForeignKey(
        Competition, blank=True, on_delete=models.CASCADE)
    type = models.CharField(choices=[(PROJECTS, PROJECTS.capitalize()), (PEOPLE, PEOPLE.capitalize(
    )), (COMPETE, COMPETE.capitalize())], max_length=maxLengthInList(DIVISIONS))
    moderator = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name="moderator")
    request = models.CharField(max_length=100000)
    response = models.CharField(max_length=100000, blank=True)
    status = models.CharField(choices=([code.MODERATION, code.MODERATION.capitalize()], [code.APPROVED, code.APPROVED.capitalize()], [
                              code.REJECTED, code.REJECTED.capitalize()]), max_length=50, default=code.MODERATION)
    retries = models.IntegerField(default=3)
    requestOn = models.DateTimeField(auto_now=False, default=timezone.now)
    respondOn = models.DateTimeField(auto_now=False)
    referURL = models.URLField(blank=True,null=True)
    resolved = models.BooleanField(default=False)

    def __str__(self):
        return self.project.name

    def approve(self, response):
        self.status = code.APPROVED
        self.response = response
        self.respondOn = timezone.now()
        if(self.type == PROJECTS):
            self.project.status = code.LIVE
            self.project.approvedOn = timezone.now
            self.project.save()
        self.resolved = True
        self.save()

    def reject(self, response):
        self.status = code.REJECTED
        self.response = response
        self.respondOn = timezone.now()
        if self.retries > 0:
            self.retries = self.retries - 1
        if(self.type == PROJECTS):
            self.project.status = code.REJECTED
            self.project.save()
        self.resolved = True
        self.save()

    def getLink(self, alert='', error=''):
        if error:
            error = f"?e={error}"
        elif alert:
            alert = f"?a={alert}"

        return f"/{APPNAME}/{self.id}{error}{alert}"

    def isRequestor(self, profile:Profile) -> bool:
        if self.type == PROJECTS:
            return profile == self.project.creator
        if self.type == PEOPLE:
            return self.profile.isReporter(profile)
        if self.type == COMPETE:
            return self.competition.isJudge(profile)


class LocalStorage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    key = models.CharField(max_length=100, blank=False, null=False)
    value = models.CharField(max_length=100, blank=False, null=False)

    def __str__(self):
        return self.key
