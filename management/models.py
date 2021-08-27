from django.db import models
import uuid
from main.strings import url, Code
from people.models import Profile
from .apps import APPNAME

class Report(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reporter = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='reporter_profile', null=True, blank=True)
    summary = models.CharField(max_length=1000)
    detail = models.CharField(max_length=100000)
    response = models.CharField(max_length=1000000,null=True,blank=True)
    resolved = models.BooleanField(default=False)

    @property
    def get_id(self):
        return self.id.hex

    @property
    def is_anonymous(self):
        return True if not self.reporter else False

    @property
    def reportfeed_type(self):
        return Code.REPORTS

    @property
    def getLink(self):
        return f"{url.getRoot(APPNAME)}{url.management.reportfeedTypeID(self.reportfeed_type,self.get_id)}"

class Feedback(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    feedbacker = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='feedbacker_profile', null=True, blank=True)
    detail = models.CharField(max_length=100000)
    response = models.CharField(max_length=1000000,null=True,blank=True)

    @property
    def get_id(self):
        return self.id.hex

    @property
    def reportfeed_type(self):
        return Code.FEEDBACKS

    @property
    def is_anonymous(self):
        return True if not self.feedbacker else False

    @property
    def getLink(self):
        return f"{url.getRoot(APPNAME)}{url.management.reportfeedTypeID(self.reportfeed_type,self.get_id)}"
