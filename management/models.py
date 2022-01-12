from datetime import timedelta
from django.utils import timezone
from django.db import models
import uuid
from main.strings import url, Code, PEOPLE
from .apps import APPNAME

class Report(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reporter = models.ForeignKey(f"{PEOPLE}.Profile", on_delete=models.CASCADE, related_name='reporter_profile', null=True, blank=True)
    summary = models.CharField(max_length=1000)
    detail = models.CharField(max_length=100000)
    response = models.CharField(max_length=1000000,null=True,blank=True)
    resolved = models.BooleanField(default=False)
    createdOn = models.DateTimeField(auto_now=False, default=timezone.now)
    updatedOn = models.DateTimeField(auto_now=False, default=timezone.now)

    def save(self, *args, **kwargs):
        if not self.id:
            self.createdOn = timezone.now()
        self.updatedOn = timezone.now()
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

class Feedback(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    feedbacker = models.ForeignKey(f"{PEOPLE}.Profile", on_delete=models.CASCADE, related_name='feedbacker_profile', null=True, blank=True)
    detail = models.CharField(max_length=100000)
    response = models.CharField(max_length=1000000,null=True,blank=True)
    createdOn = models.DateTimeField(auto_now=False, default=timezone.now)
    updatedOn = models.DateTimeField(auto_now=False, default=timezone.now)

    def save(self, *args, **kwargs):
        if not self.id:
            self.createdOn = timezone.now()
        self.updatedOn = timezone.now()
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

class ReportCategory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=1000)

    def __str__(self):
        return self.name

class HookRecord(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    hookID = models.CharField(max_length=60)
    success = models.BooleanField(default=False)
    
    def __str__(self):
        return self.hookID

    @property
    def get_id(self):
        return self.id.hex

class ActivityRecord(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(f'{PEOPLE}.User', on_delete=models.CASCADE)
    view_name = models.CharField(max_length=500)
    request_get = models.CharField(max_length=60000)
    request_post = models.CharField(max_length=60000)
    response_status = models.IntegerField(default=200)

    @property
    def get_id(self):
        return self.id.hex

    def __str__(self):
        return self.get_id

class Management(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profile = models.OneToOneField(f'{PEOPLE}.Profile', on_delete=models.CASCADE, related_name='management_profile')
    people = models.ManyToManyField(f'{PEOPLE}.Profile', through="ManagementPerson", related_name='management_people', default=[])
    createdOn = models.DateTimeField(auto_now=False, default=timezone.now)
    updatedOn = models.DateTimeField(auto_now=False, default=timezone.now)

    def save(self, *args, **kwargs):
        self.modifiedOn = timezone.now()
        return super(Management, self).save(*args, **kwargs)

    @property
    def get_accountid(self):
        return self.profile.get_userid

    def getName(self):
        return self.profile.getName()
    
    @property
    def get_name(self):
        return self.getName()

    @property
    def get_id(self):
        return self.id.hex

    def getLink(self, success='', error='', message=''):
        return self.profile.getLink(success=success, error=error, alert=message)

    @property
    def get_link(self):
        return self.getLink()

    def __str__(self):
        return self.profile.getName()

    @property
    def has_invitations(self):
        return ManagementInvitation.objects.filter(management=self, resolved=False).exists()

    def current_invitations(self):
        return ManagementInvitation.objects.filter(management=self, resolved=False)

    def getPeople(self):
        return self.people.all()
    
    @property
    def total_moderators(self):
        return self.people.filter(is_moderator=True, is_active=True, to_be_zombie=False, suspended=False).count()

    @property
    def moderators(self):
        return self.people.filter(is_moderator=True, is_active=True, to_be_zombie=False, suspended=False)

    @property
    def total_moderators_abs(self):
        return self.people.filter(is_moderator=True, to_be_zombie=False).count()

    @property
    def moderators_abs(self):
        return self.people.filter(is_moderator=True, to_be_zombie=False)

    @property
    def total_mentors(self):
        return self.people.filter(is_mentor=True, is_active=True, to_be_zombie=False, suspended=False).count()

    @property
    def mentors(self):
        return self.people.filter(is_mentor=True, is_active=True, to_be_zombie=False, suspended=False)

    @property
    def total_mentors_abs(self):
        return self.people.filter(is_mentor=True, to_be_zombie=False).count()

    @property
    def mentors_abs(self):
        return self.people.filter(is_mentor=True, to_be_zombie=False)
        
class ManagementPerson(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    person = models.ForeignKey(f'{PEOPLE}.Profile', on_delete=models.CASCADE, related_name='management_person_profile')
    management = models.ForeignKey(Management, on_delete=models.CASCADE, related_name='management_person_mgm')
    createdOn = models.DateTimeField(auto_now=False, default=timezone.now)
    updatedOn = models.DateTimeField(auto_now=False, default=timezone.now)

    class Meta:
        unique_together = ('person', 'management')

    def save(self, *args, **kwargs):
        self.modifiedOn = timezone.now()
        return super(Management, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.person.getName()} at {self.management}"
    

class Invitation(models.Model):
    """
    Base class for all invitations
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    expiresOn = models.DateTimeField(auto_now=False, default=timezone.now()+timedelta(days=1))
    resolved = models.BooleanField(default=False)
    createdOn = models.DateTimeField(auto_now=False, default=timezone.now)
    updatedOn = models.DateTimeField(auto_now=False, default=timezone.now)

    def save(self, *args, **kwargs):
        self.modifiedOn = timezone.now()
        return super(Invitation, self).save(*args, **kwargs)

    @property
    def get_id(self):
        return self.id.hex

    @property
    def get_link(self):
        return f"{url.getRoot(APPNAME)}{url.management.invitationID(self.get_id)}"

    def __str__(self):
        return self.get_id

    @property
    def is_active(self):
        return self.expiresOn > timezone.now()
    
    def resolve(self):
        self.resolved = True
        self.expiresOn = timezone.now()
        self.save()
    
    @property
    def expired(self):
        return self.expiresOn <= timezone.now()

class ManagementInvitation(Invitation):
    sender = models.ForeignKey(f'{PEOPLE}.Profile', on_delete=models.CASCADE, related_name='people_invitation_sender')
    receiver = models.ForeignKey(f'{PEOPLE}.Profile', on_delete=models.CASCADE, related_name='people_invitation_receiver')
    management = models.ForeignKey(Management, on_delete=models.CASCADE, related_name='invitation_management')

    class Meta:
        unique_together = ('receiver', 'management')

    def getLink(self, success: str = '', error: str = '', alert: str = '') -> str:
        return f"{url.getRoot(APPNAME)}{url.management.peopleMGMInvite(self.get_id)}{url.getMessageQuery(alert,error,success)}"

    @property
    def get_link(self):
        return self.getLink()

    @property
    def get_act_link(self):
        return f"{url.getRoot(APPNAME)}{url.management.peopleMGMInviteAct(self.get_id)}"

    def accept(self):
        if self.expired: return False
        if self.resolved: return False
        if self.sender.is_blocked(self.receiver.user): return False
        done = self.receiver.addToManagement(self.management.id)
        if not done: return done
        self.resolve()
        return done

    def decline(self):
        if self.expired: return False
        if self.resolved: return False
        if self.sender.is_blocked(self.receiver.user): return False
        self.delete()
        return True


class GhMarketApp(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    gh_id = models.CharField(max_length=100, unique=True)
    gh_name = models.CharField(max_length=100, unique=True)
    gh_url = models.URLField(max_length=200, unique=True)

class GhMarketPlan(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    gh_id = models.CharField(max_length=100, unique=True)
    is_free = models.BooleanField(default=True)
    gh_app = models.ForeignKey(GhMarketApp, on_delete=models.CASCADE)
    gh_url = models.URLField(max_length=200, unique=True)

class APIKey(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    key = models.CharField(max_length=100, unique=True, help_text="Random string at least 32 chars")
    name = models.CharField(max_length=100, null=True,blank=True)
    is_internal = models.BooleanField(default=False)
    creator = models.ForeignKey(f'{PEOPLE}.Profile', related_name='apikey_creator_profile', on_delete=models.CASCADE, null=True)
    created_on = models.DateTimeField(auto_now=False, default=timezone.now)

    def save(self, *args, **kwargs):
        if not str(self.key).startswith("knot_"):
            self.key = f"knot_{self.key}"
        if(len(self.key.replace("knot_",''))<32): return False
        super(APIKey, self).save(*args, **kwargs)

    @property
    def get_id(self):
        return self.id.hex

    def __str__(self):
        return self.name or self.get_id
