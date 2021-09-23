from django.utils import timezone
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
    createdOn = models.DateTimeField(auto_now=False, default=timezone.now)
    updatedOn = models.DateTimeField(auto_now=False, default=timezone.now)

    def save(self, *args, **kwargs):
        if not self.id:
            self.createdOn = timezone.now()
        self.modifiedOn = timezone.now()
        return super(Report, self).save(*args, **kwargs)

    @property
    def get_id(self):
        return self.id.hex

    @property
    def is_anonymous(self):
        return True if not self.reporter else False

    @property
    def author(self):
        return self.reporter.getName() if not self.is_anonymous else 'Anonymous'

    @property
    def reportfeed_type(self):
        return Code.REPORTS

    @property
    def getLink(self):
        return f"{url.getRoot(APPNAME)}{url.management.reportfeedTypeID(self.reportfeed_type,self.get_id)}"

class ProfileReport(Report):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='reported_profile', null=True, blank=True)

class Feedback(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    feedbacker = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='feedbacker_profile', null=True, blank=True)
    detail = models.CharField(max_length=100000)
    response = models.CharField(max_length=1000000,null=True,blank=True)
    createdOn = models.DateTimeField(auto_now=False, default=timezone.now)
    updatedOn = models.DateTimeField(auto_now=False, default=timezone.now)

    def save(self, *args, **kwargs):
        if not self.id:
            self.createdOn = timezone.now()
        self.modifiedOn = timezone.now()
        return super(Feedback, self).save(*args, **kwargs)

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
    def author(self):
        return self.feedbacker.getName() if not self.is_anonymous else 'Anonymous'

    @property
    def getLink(self):
        return f"{url.getRoot(APPNAME)}{url.management.reportfeedTypeID(self.reportfeed_type,self.get_id)}"
