from django.db import models
from uuid import uuid4
from main.strings import PROJECT, PEOPLE, COMPETE, DIVISIONS
from main.methods import maxLengthInList


class Moderation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    project = models.ForeignKey(
        f"{PROJECT}.Project", on_delete=models.CASCADE, blank=True)
    user = models.ForeignKey(f"{PEOPLE}.User", blank=True,
                             on_delete=models.CASCADE, related_name="moderation4user")
    competition = models.ForeignKey(
        f"{COMPETE}.Competition", blank=True, on_delete=models.CASCADE)
    type = models.CharField(choices=[(PROJECT, PROJECT.capitalize()), (PEOPLE, PEOPLE.capitalize(
    )), (COMPETE, COMPETE.capitalize())], max_length=maxLengthInList(DIVISIONS))
    moderator = models.ForeignKey(
        f"{PEOPLE}.User", on_delete=models.CASCADE, related_name="moderator")
    request = models.CharField(max_length=100000)
    response = models.CharField(max_length=100000, blank=True)
    status = models.CharField(choices=(["pending", "Pending"], ["approved", "Approved"], [
                              "rejected", "Rejected"]), max_length=50, default="moderation")

    def __str__(self):
        return f"{self.project.name} by {self.moderator.getName}"

    def approve(self):
        self.status = "approved"
        if(self.type == PROJECT):
            self.project.status = "live"
            self.project.save()
        self.save()

    def reject(self, response):
        self.status = "rejected"
        self.response = response
        if(self.type == "project"):
            self.project.status = "rejected"
            self.project.save()
        self.save()


class LocalStorage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    key = models.CharField(max_length=100, blank=False, null=False)
    value = models.CharField(max_length=100, blank=False, null=False)

    def __str__(self):
        return self.key
