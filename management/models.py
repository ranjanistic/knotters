from datetime import datetime, timedelta
from uuid import UUID, uuid4
from django.core.files.base import File
from auth2.models import Address, PhoneNumber
from django.conf import settings
from django.core.cache import cache
from django.db import models
from django.utils import timezone
from github.Organization import Organization
from main.strings import PEOPLE, Code, Message, Profile, url

from .apps import APPNAME


class Report(models.Model):
    """Report model
    """
    id: UUID = models.UUIDField(
        primary_key=True, default=uuid4, editable=False)
    reporter = models.ForeignKey(f"{PEOPLE}.Profile", on_delete=models.CASCADE,
                                 related_name='reporter_profile', null=True, blank=True)
    summary: str = models.TextField(max_length=1000)
    detail: str = models.TextField(max_length=100000)
    response: str = models.TextField(max_length=1000000, null=True, blank=True)
    resolved: bool = models.BooleanField(default=False)
    createdOn: datetime = models.DateTimeField(
        auto_now=False, default=timezone.now)
    updatedOn: datetime = models.DateTimeField(
        auto_now=False, default=timezone.now)

    def save(self, *args, **kwargs):
        if not self.id:
            self.createdOn = timezone.now()
        self.updatedOn = timezone.now()
        return super(Report, self).save(*args, **kwargs)

    @property
    def get_id(self) -> str:
        return self.id.hex

    @property
    def is_anonymous(self) -> bool:
        return True if not self.reporter else False

    @property
    def author(self) -> str:
        return self.reporter.getName() if not self.is_anonymous else 'Anonymous'

    @property
    def reportfeed_type(self) -> str:
        return Code.REPORTS

    @property
    def getLink(self) -> str:
        return f"{url.getRoot(APPNAME)}{url.management.reportfeedTypeID(self.reportfeed_type,self.get_id)}"


class Feedback(models.Model):
    """Feedback model
    """
    id: UUID = models.UUIDField(
        primary_key=True, default=uuid4, editable=False)
    feedbacker = models.ForeignKey(f"{PEOPLE}.Profile", on_delete=models.CASCADE,
                                   related_name='feedbacker_profile', null=True, blank=True)
    detail: str = models.TextField(max_length=100000)
    response: str = models.TextField(max_length=1000000, null=True, blank=True)
    createdOn: datetime = models.DateTimeField(
        auto_now=False, default=timezone.now)
    updatedOn: datetime = models.DateTimeField(
        auto_now=False, default=timezone.now)

    def save(self, *args, **kwargs):
        if not self.id:
            self.createdOn = timezone.now()
        self.updatedOn = timezone.now()
        return super(Feedback, self).save(*args, **kwargs)

    @property
    def get_id(self) -> str:
        return self.id.hex

    @property
    def reportfeed_type(self) -> str:
        return Code.FEEDBACKS

    @property
    def is_anonymous(self) -> bool:
        return True if not self.feedbacker else False

    @property
    def author(self) -> str:
        return self.feedbacker.getName() if not self.is_anonymous else 'Anonymous'

    @property
    def getLink(self) -> str:
        return f"{url.getRoot(APPNAME)}{url.management.reportfeedTypeID(self.reportfeed_type,self.get_id)}"


class ReportCategory(models.Model):
    """Report category model
    """
    id: UUID = models.UUIDField(
        primary_key=True, default=uuid4, editable=False)
    name: str = models.CharField(max_length=1000)

    ALL_CACHE_KEY = f"report_categories_all"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        super(ReportCategory, self).save(*args, **kwargs)
        self.reset_all_cache()

    def get_all(*args) -> models.QuerySet:
        """Get all report categories, preferably from cache
        """
        cache_key = ReportCategory.ALL_CACHE_KEY
        categories = cache.get(cache_key, None)
        if categories is None:
            categories = ReportCategory.objects.all()
            cache.set(cache_key, categories, settings.CACHE_ETERNAL)
        return categories

    def get_cache_one(*args, id: UUID) -> "ReportCategory":
        """Get one report category by id, preferably from cache

        Raises:
            ObjectDoesNotExist: if no record with the given id exists
        """
        return ReportCategory.get_all().get(id=id)

    def reset_all_cache(*args) -> models.QuerySet:
        """Reset all cache. Can be used when adding/updating ReportCategory objects.
        """
        cache.delete(ReportCategory.ALL_CACHE_KEY)
        cats = ReportCategory.objects.all()
        cache.set(ReportCategory.ALL_CACHE_KEY, cats, settings.CACHE_ETERNAL)
        return cats


class HookRecord(models.Model):
    """Hook record model
    """
    id: UUID = models.UUIDField(
        primary_key=True, default=uuid4, editable=False)
    hookID: str = models.CharField(max_length=60)
    success: bool = models.BooleanField(default=False)

    def __str__(self):
        return self.hookID

    @property
    def get_id(self):
        return self.id.hex


class ActivityRecord(models.Model):
    """TODO: Activity record model
    """
    id: UUID = models.UUIDField(
        primary_key=True, default=uuid4, editable=False)
    user = models.ForeignKey(f'{PEOPLE}.User', on_delete=models.CASCADE)
    view_name: str = models.CharField(max_length=500)
    request_get: str = models.TextField(max_length=60000)
    request_post: str = models.TextField(max_length=60000)
    response_status: int = models.IntegerField(default=200)

    @property
    def get_id(self):
        return self.id.hex

    def __str__(self):
        return self.get_id


class Management(models.Model):
    """Management model, or organization model
    """
    id: UUID = models.UUIDField(
        primary_key=True, default=uuid4, editable=False)
    profile = models.OneToOneField(
        f'{PEOPLE}.Profile', on_delete=models.CASCADE, related_name='management_profile')
    """profile (ForeignKey<Profile>): profile of the management"""
    people = models.ManyToManyField(
        f'{PEOPLE}.Profile', through="ManagementPerson", related_name='management_people', default=[])
    """people (ManyToManyField<Profile>): people in the management"""
    createdOn: datetime = models.DateTimeField(
        auto_now=False, default=timezone.now)
    """createdOn (DateTimeField): created on date"""
    updatedOn: datetime = models.DateTimeField(
        auto_now=False, default=timezone.now)
    """updatedOn (DateTimeField): updated on date"""
    githubOrgID: str = models.CharField(max_length=100, null=True, blank=True)
    """githubOrgID (CharField): linked github organization id"""

    def save(self, *args, **kwargs):
        self.modifiedOn = timezone.now()
        return super(Management, self).save(*args, **kwargs)

    def get_accountid(self) -> str:
        """User id linked with this management
        """
        return self.profile.get_userid

    def getName(self) -> str:
        return self.profile.getName()

    @property
    def get_name(self) -> str:
        return self.getName()

    @property
    def get_id(self) -> str:
        return self.id.hex

    def getLink(self, success='', error='', message='') -> str:
        return self.profile.getLink(success=success, error=error, alert=message)

    @property
    def get_link(self) -> str:
        return self.getLink()

    def __str__(self):
        return self.profile.getName()

    def get_ghorg(self) -> Organization:
        """Get github organization linked with this management

        Returns:
            Organization: Github organization linked with this management
        """
        try:
            if self.githubOrgID:
                return list(filter(lambda ghorg: str(ghorg.id) == self.githubOrgID, self.profile.get_ghOrgs()))[0]
            return None
        except:
            return None

    def get_ghorgUrl(self) -> str:
        """Get github organization url linked with this management

        Returns:
            str: Github organization url linked with this management, or knotters profile link if github organization is not linked
        """
        try:
            return self.get_ghorg().url.replace('api.', '')
        except:
            return self.getLink(message=Message.GH_ORG_NOT_LINKED)

    def get_ghorgName(self) -> str:
        """Get github organization name linked with this management

        Returns:
            str: Github organization name linked with this management, or None if github organization is not linked
        """
        try:
            return list(filter(lambda idn: str(idn['id']) == self.githubOrgID, self.profile.get_ghOrgsIDName()))[0]['name']
        except Exception as e:
            return None

    def has_invitations(self) -> bool:
        """Check if this management has invitations

        Returns:
            bool: True if this management has invitations, False otherwise
        """
        return ManagementInvitation.objects.filter(management=self, resolved=False).exists()

    def current_invitations(self) -> models.QuerySet:
        """Get current unresolved invitations in this management

        Returns:
            models.QuerySet<ManagementInvitation>: Current unresolved invitations in this management
        """
        return ManagementInvitation.objects.filter(management=self, resolved=False)

    def getPeople(self) -> models.QuerySet:
        """Get people linked with this management

        Returns:
            models.QuerySet<Profile>: People linked with this management
        """
        return self.people.all()

    def total_moderators(self) -> int:
        """Get total number of moderators in this management

        Returns:
            int: Total number of moderators in this management
        """
        return self.people.filter(is_moderator=True, is_active=True, to_be_zombie=False, suspended=False).count()

    def moderators(self) -> models.QuerySet:
        """Get moderators in this management

        Returns:
            models.QuerySet<Profile>: Moderators in this management
        """
        return self.people.filter(is_moderator=True, is_active=True, to_be_zombie=False, suspended=False)

    def total_moderators_abs(self) -> int:
        """Get total number of moderators in this management (active and inactive)

        Returns:
            int: Total number of moderators in this management (active and inactive)
        """
        return self.people.filter(is_moderator=True, to_be_zombie=False).count()

    def moderators_abs(self) -> models.QuerySet:
        """Get moderators in this management (active and inactive)

        Returns:
            models.QuerySet<Profile>: Moderators in this management (active and inactive)
        """
        return self.people.filter(is_moderator=True, to_be_zombie=False)

    def total_mentors(self) -> int:
        """Get total number of mentors in this management

        Returns:
            int: Total number of mentors in this management
        """
        return self.people.filter(is_mentor=True, is_active=True, to_be_zombie=False, suspended=False).count()

    def mentors(self) -> models.QuerySet:
        """Get mentors in this management

        Returns:
            models.QuerySet<Profile>: Mentors in this management
        """
        return self.people.filter(is_mentor=True, is_active=True, to_be_zombie=False, suspended=False)

    def total_mentors_abs(self) -> int:
        """Get total number of mentors in this management (active and inactive)

        Returns:
            int: Total number of mentors in this management (active and inactive)
        """
        return self.people.filter(is_mentor=True, to_be_zombie=False).count()

    def mentors_abs(self) -> models.QuerySet:
        """Get mentors in this management (active and inactive)

        Returns:
            models.QuerySet<Profile>: Mentors in this management (active and inactive)
        """
        return self.people.filter(is_mentor=True, to_be_zombie=False)
    
    def has_member(self, profile: Profile) -> bool:
        """ Returns whether given profile is part of management or not"""
        return self.people.filter(id=profile.id).exists()


class ManagementPerson(models.Model):
    """
    The model that for relationship between management and a person (member).
    """
    id: UUID = models.UUIDField(
        primary_key=True, default=uuid4, editable=False)
    person = models.ForeignKey(
        f'{PEOPLE}.Profile', on_delete=models.CASCADE, related_name='management_person_profile')
    """person (ForeignKey<Profile>): person in this relationship"""
    management: Management = models.ForeignKey(
        Management, on_delete=models.CASCADE, related_name='management_person_mgm')
    """management (ForeignKey<Management>): management in this relationship"""
    createdOn: datetime = models.DateTimeField(
        auto_now=False, default=timezone.now)
    """createdOn (DateTimeField): date and time of creation"""
    updatedOn: datetime = models.DateTimeField(
        auto_now=False, default=timezone.now)
    """updatedOn (DateTimeField): date and time of last update"""

    class Meta:
        unique_together = ('person', 'management')

    def save(self, *args, **kwargs):
        self.modifiedOn = timezone.now()
        return super(Management, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.person.getName()} at {self.management}"


class Invitation(models.Model):
    """
    Base class for all invitations. The subclasses need to specify their own sender and receiver attributes.
    """
    id: UUID = models.UUIDField(
        primary_key=True, default=uuid4, editable=False)
    expiresOn: datetime = models.DateTimeField(
        auto_now=False, default=timezone.now()+timedelta(days=2))
    """expiresOn (DateTimeField): date and time of expiration"""
    resolved: bool = models.BooleanField(default=False)
    """resolved (BooleanField): True if invitation is resolved, False otherwise"""
    createdOn: datetime = models.DateTimeField(
        auto_now=False, default=timezone.now)
    """createdOn (DateTimeField): date and time of creation"""
    updatedOn: datetime = models.DateTimeField(
        auto_now=False, default=timezone.now)
    """updatedOn (DateTimeField): date and time of last update"""

    def save(self, *args, **kwargs):
        self.modifiedOn = timezone.now()
        return super(Invitation, self).save(*args, **kwargs)

    @property
    def get_id(self):
        return self.id.hex

    def getLink(self) -> str:
        """Default link is management invitation link, should be overridden in subclasses"""
        return f"{url.getRoot(APPNAME)}{url.management.invitationID(self.get_id)}"

    @property
    def get_link(self) -> str:
        return self.getLink()

    def __str__(self):
        return self.get_id

    @property
    def is_active(self) -> bool:
        """Check if this invitation is active
        """
        return self.expiresOn > timezone.now()

    def resolve(self) -> bool:
        """Resolve this invitation
        """
        self.resolved = True
        self.expiresOn = timezone.now()
        self.save()
        return self.resolved

    def unresolve(self) -> bool:
        """Unresolve this invitation
        """
        self.resolved = False
        self.expiresOn = self.createdOn+timedelta(days=2)
        self.save()
        return self.resolved

    @property
    def expired(self) -> bool:
        """Check if this invitation is expired
        """
        return self.expiresOn <= timezone.now()

    def decline(self) -> bool:
        """Decline this invitation. This does not delete the invitation record,
            but resolves it. This method should be overridden in subclasses for specific behavior.

        Returns:
            bool: True if invitation is resolved (declined), False otherwise
        """
        if self.expired:
            return False
        if self.resolved:
            return False
        self.resolve()
        self.save()
        return True


class ManagementInvitation(Invitation):
    """The model for invitation to join a management
    """
    sender = models.ForeignKey(
        f'{PEOPLE}.Profile', on_delete=models.CASCADE, related_name='people_invitation_sender')
    """sender (ForeignKey<Profile>): sender of this invitation"""
    receiver = models.ForeignKey(
        f'{PEOPLE}.Profile', on_delete=models.CASCADE, related_name='people_invitation_receiver')
    """receiver (ForeignKey<Profile>): receiver of this invitation"""
    management: Management = models.ForeignKey(
        Management, on_delete=models.CASCADE, related_name='invitation_management')
    """management (ForeignKey<Management>): management for which this invitation is created"""

    class Meta:
        unique_together = ('receiver', 'management')

    def getLink(self, success: str = '', error: str = '', alert: str = '') -> str:
        """Get link to this invitation view
        """
        return f"{url.getRoot(APPNAME)}{url.management.peopleMGMInvite(self.get_id)}{url.getMessageQuery(alert,error,success)}"

    @property
    def get_link(self) -> str:
        return self.getLink()

    @property
    def get_act_link(self) -> str:
        """Get link to act on this invitation. Should be used in invitation view by the receiver via POST request.

        Returns:
            str: Link to act on this invitation
        """
        return f"{url.getRoot(APPNAME)}{url.management.peopleMGMInviteAct(self.get_id)}"

    def accept(self) -> bool:
        """Accept this invitation. This does not delete the invitation record,
        but resolves it and adds the receiver to the management

        Returns:
            bool: True if invitation is resolved (accepted) successfully, False otherwise
        """
        if self.expired:
            return False
        if self.resolved:
            return False
        if self.sender.is_blocked(self.receiver.user):
            return False
        done = self.receiver.addToManagement(self.management.id)
        if not done:
            return done
        self.resolve()
        return done

    def decline(self) -> bool:
        """Decline this invitation. This deletes the invitation record,
        if the invitation is still valid.
        """
        if self.expired:
            return False
        if self.resolved:
            return False
        if self.sender.is_blocked(self.receiver.user):
            return False
        self.delete()
        return True


class GhMarketApp(models.Model):
    """The model for Knotters GitHub Marketplace app"""
    id: UUID = models.UUIDField(
        primary_key=True, default=uuid4, editable=False)
    gh_id: str = models.CharField(max_length=100, unique=True)
    """gh_id (CharField): GitHub Marketplace app ID"""
    gh_name: str = models.CharField(max_length=100, unique=True)
    """gh_name (CharField): GitHub Marketplace app name"""
    gh_url: str = models.URLField(max_length=200, unique=True)
    """gh_url (URLField): GitHub Marketplace app URL"""

    ALL_CACHE_KEY = f"gh_market_apps"

    def __str__(self) -> str:
        return f'{self.gh_id} {self.gh_name}'

    def save(self, *args, **kwargs):
        super(GhMarketApp, self).save(*args, **kwargs)
        self.reset_all_cache()

    def get_all(*args) -> models.QuerySet:
        """Get all GhMarketApp objects, preferably from cache

        Returns:
            QuerySet: all GhMarketApp objects
        """
        apps = cache.get(GhMarketApp.ALL_CACHE_KEY, [])
        if not len(apps):
            apps = GhMarketApp.objects.filter().order_by('gh_name')
            cache.set(GhMarketApp.ALL_CACHE_KEY, apps, settings.CACHE_ETERNAL)
        return apps

    def reset_all_cache(*args) -> models.QuerySet:
        """Reset all cache. Can be used when adding/updating GhMarketApp objects.
        """
        cache.delete(GhMarketApp.ALL_CACHE_KEY)
        apps = GhMarketApp.objects.filter().order_by('gh_name')
        cache.set(GhMarketApp.ALL_CACHE_KEY, apps, settings.CACHE_ETERNAL)
        return apps


class GhMarketPlan(models.Model):
    """The model for Knotters GitHub Marketplace Apps' plan"""
    id: UUID = models.UUIDField(
        primary_key=True, default=uuid4, editable=False)
    gh_id: str = models.CharField(max_length=100, unique=True)
    """gh_id (CharField): GitHub Marketplace plan ID"""
    is_free: bool = models.BooleanField(default=True)
    """is_free (BooleanField): True if this plan is free, False otherwise"""
    gh_app: GhMarketApp = models.ForeignKey(
        GhMarketApp, on_delete=models.CASCADE)
    """gh_app (ForeignKey<GhMarketApp>): GitHub Marketplace app"""
    gh_url: str = models.URLField(max_length=200, unique=True)
    """gh_url (URLField): GitHub Marketplace plan URL"""

    def __str__(self) -> str:
        return f'{self.gh_app} {self.gh_id}'


class APIKey(models.Model):
    """The model for API key"""
    id: UUID = models.UUIDField(
        primary_key=True, default=uuid4, editable=False)
    key: str = models.CharField(max_length=100, unique=True,
                                help_text="Random string at least 32 chars")
    """key (CharField): API key. Usually this is auto-generated on record creation"""
    name: str = models.CharField(max_length=100, null=True, blank=True)
    """name (CharField): name of the API key"""
    is_internal: bool = models.BooleanField(default=False)
    """is_internal (BooleanField): True if this is an internal API key, False otherwise. True is meant for internal sensitive access."""
    creator = models.ForeignKey(
        f'{PEOPLE}.Profile', related_name='apikey_creator_profile', on_delete=models.CASCADE, null=True)
    """creator (ForeignKey<Profile>): creator of this API key"""
    created_on: datetime = models.DateTimeField(
        auto_now=False, default=timezone.now)
    """created_on (DateTimeField): date and time when this API key was created"""

    def save(self, *args, **kwargs):
        """Save this API key record. Also automatically generates the key if it is empty.
        """
        if not str(self.key).startswith("knot_"):
            self.key = f"knot_{self.key}"
        if(len(self.key.replace("knot_", '')) < 32):
            return False
        super(APIKey, self).save(*args, **kwargs)

    @property
    def get_id(self):
        return self.id.hex

    def __str__(self):
        return self.name or self.get_id


class ContactCategory(models.Model):
    """The model for contact category"""
    id: UUID = models.UUIDField(
        primary_key=True, default=uuid4, editable=False)
    name: str = models.CharField(max_length=100, unique=True)
    """name (CharField): name of the contact category"""
    disabled: bool = models.BooleanField(default=False)
    """disabled (BooleanField): True if this category is disabled, False otherwise"""
    created_on: datetime = models.DateTimeField(
        auto_now=False, default=timezone.now)
    """created_on (DateTimeField): date and time when this category was created"""

    ALL_CACHE_KEY = f"contact_categories"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        super(ContactCategory, self).save(*args, **kwargs)
        self.reset_all_cache()

    def get_all(*args) -> models.QuerySet:
        """Get all ContactCategory objects, preferably from cache

        Returns:
            QuerySet: all ContactCategory objects   
        """
        categories = cache.get(ContactCategory.ALL_CACHE_KEY, [])
        if not len(categories):
            categories = ContactCategory.objects.filter(disabled=False)
            cache.set(ContactCategory.ALL_CACHE_KEY,
                      categories, settings.CACHE_ETERNAL)
        return categories

    def reset_all_cache(*args) -> models.QuerySet:
        """Reset all cache. Can be used when adding/updating ContactCategory objects.

        Returns:
            QuerySet: all ContactCategory objects
        """
        cache.delete(ContactCategory.ALL_CACHE_KEY)
        categories = ContactCategory.objects.filter(disabled=False)
        cache.set(ContactCategory.ALL_CACHE_KEY,
                  categories, settings.CACHE_ETERNAL)
        return categories


class ContactRequest(models.Model):
    """The model for contact request"""
    id: UUID = models.UUIDField(
        primary_key=True, default=uuid4, editable=False)
    resolved: bool = models.BooleanField(default=False)
    """resolved (BooleanField): True if this request is resolved, False otherwise"""
    createdOn: datetime = models.DateTimeField(
        auto_now=False, default=timezone.now)
    """createdOn (DateTimeField): date and time when this request was created"""
    updatedOn: datetime = models.DateTimeField(
        auto_now=False, default=timezone.now)
    """updatedOn (DateTimeField): date and time when this request was updated"""
    senderName: str = models.CharField(max_length=100)
    """senderName (CharField): name of the sender"""
    senderEmail: str = models.EmailField(max_length=100)
    """senderEmail (EmailField): email of the sender"""
    contactCategory: ContactCategory = models.ForeignKey(
        ContactCategory, on_delete=models.CASCADE)
    """contactCategory (ForeignKey<ContactCategory>): contact category"""
    message: str = models.TextField(max_length=1000)
    """message (TextField): message of the request"""


class ThirdPartyLicense(models.Model):
    """The model for internal application software third party license"""
    id: UUID = models.UUIDField(
        primary_key=True, default=uuid4, editable=False)
    title = models.CharField(max_length=100)
    """title (CharField): title of the license"""
    link = models.URLField(max_length=150)
    """link (URLField): link to the license"""
    license = models.TextField(max_length=300000)
    """license (TextField): license text"""

    ALL_CACHE_KEY = f"third_party_license_all"

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        super(ThirdPartyLicense, self).save(*args, **kwargs)
        self.reset_all_cache()

    def get_all(*args) -> models.QuerySet:
        """Get all third party licenses, preferably from cache.

        Returns:
            models.QuerySet: all third party licenses
        """
        cacheKey = ThirdPartyLicense.ALL_CACHE_KEY
        tpls = cache.get(cacheKey, None)
        if not tpls:
            tpls = ThirdPartyLicense.objects.filter().order_by('title')
            cache.set(cacheKey, tpls, timeout=settings.CACHE_ETERNAL)
        return tpls

    def reset_all_cache(*args) -> models.QuerySet:
        """Reset all third party licenses cache.
        Can be used when adding/updating third party licenses.

        Returns:
            models.QuerySet: all third party licenses
        """
        cacheKey = ThirdPartyLicense.ALL_CACHE_KEY
        cache.delete(cacheKey)
        tpls = ThirdPartyLicense.objects.filter().order_by('title')
        cache.set(cacheKey, tpls, timeout=settings.CACHE_ETERNAL)
        return tpls


class ThirdPartyAccount(models.Model):
    """The model for internal application (social) third party accounts"""
    id: UUID = models.UUIDField(
        primary_key=True, default=uuid4, editable=False)
    name: str = models.CharField(max_length=100)
    """name (CharField): name of the account"""
    key: str = models.CharField(max_length=60)
    """key (CharField): key of the account, used in image source."""
    link: str = models.URLField(max_length=150)
    """link (URLField): link to the account"""
    about: str = models.TextField(max_length=250, null=True, blank=True)
    """about (TextField): about the account"""
    width: int = models.IntegerField(default=22)
    """width (IntegerField): width of the account image"""
    height: int = models.IntegerField(default=22)
    """height (IntegerField): height of the account image"""
    has_dark: bool = models.BooleanField(default=False)
    """has_dark (BooleanField): True if the account image has dark variant as well Default: False"""
    handle: str = models.CharField(max_length=100)
    """handle (CharField): social handle of the account"""

    ALL_CACHE_KEY = f"knotters_socialaccounts_list"

    def __str__(self):
        return f"{self.name} {self.handle} at {self.link}"

    def save(self, *args, **kwargs):
        super(ThirdPartyAccount, self).save(*args, **kwargs)
        self.reset_all_cache()

    def get_all(*args) -> models.QuerySet:
        """Get all third party accounts, preferably from cache.

        Returns:
            models.QuerySet: all third party accounts
        """
        tpas = cache.get(ThirdPartyAccount.ALL_CACHE_KEY, None)
        if not tpas:
            tpas = ThirdPartyAccount.objects.all()
            cache.set(ThirdPartyAccount.ALL_CACHE_KEY,
                      tpas, settings.CACHE_ETERNAL)
        return tpas

    def reset_all_cache(*args) -> models.QuerySet:
        """Reset all third party accounts cache.
        Can be used when adding/updating third party accounts.

        Returns:
            models.QuerySet: all third party accounts
        """
        cache.delete(ThirdPartyAccount.ALL_CACHE_KEY)
        tpas = ThirdPartyAccount.objects.all()
        cache.set(ThirdPartyAccount.ALL_CACHE_KEY,
                  tpas, timeout=settings.CACHE_ETERNAL)
        return tpas


class Donor(models.Model):
    """
    TODO: The model for donor records.
    """
    id: UUID = models.UUIDField(
        primary_key=True, default=uuid4, editable=False)
    profile = models.OneToOneField(
        f'{PEOPLE}.Profile', on_delete=models.SET_NULL, null=True, related_name='donor_profile')
    """profile (OneToOneField<Profile>): profile of the donor, null if not set"""
    donation_amount: float = models.FloatField(default=0)
    """donation_amount (IntegerField): amount of the donation"""
    created_on: datetime = models.DateTimeField(
        auto_now=False, default=timezone.now)
    """created_on (DateTimeField): date and time when this donor was created"""
    name: str = models.CharField(max_length=100, null=True, blank=True)
    """name (CharField): name of the donor"""
    email: str = models.EmailField(max_length=100, null=True, blank=True)
    """email (EmailField): email of the donor"""
    address: Address = models.ForeignKey(
        Address, on_delete=models.SET_NULL, null=True, related_name='donor_address')
    """address (ForeignKey<Address>): address of the donor"""
    phone: PhoneNumber = models.ForeignKey(
        PhoneNumber, on_delete=models.SET_NULL, null=True, related_name='donor_address')
    """phone (ForeignKey<PhoneNumber>): phone number of the donor"""

    def __str__(self):
        return f"{self.profile} is a donor!"

class CareerType(models.Model):
    id: UUID = models.UUIDField(
        primary_key=True, default=uuid4, editable=False)
    created_on: datetime = models.DateTimeField(
        auto_now=False, default=timezone.now)
    """created_on (DateTimeField): date and time when this pos was created"""
    name: str = models.CharField(max_length=100, null=True, blank=True)
    """name (CharField): name of the pos"""

    def __str__(self):
        return f"{self.name}"


class CareerPosition(models.Model):
    id: UUID = models.UUIDField(
        primary_key=True, default=uuid4, editable=False)
    created_on: datetime = models.DateTimeField(
        auto_now=False, default=timezone.now)
    """created_on (DateTimeField): date and time when this pos was created"""
    creator = models.ForeignKey(
        f'{PEOPLE}.Profile', on_delete=models.CASCADE, related_name='position_creator')
    name: str = models.CharField(max_length=100, null=True, blank=True)
    """name (CharField): name of the pos"""
    email: str = models.EmailField(max_length=100, null=True, blank=True)
    """email (EmailField): email of the pos poster"""
    positions: int = models.IntegerField(default=1)
    opened:bool = models.BooleanField(default=True)
    location:str = models.CharField(max_length=200,default="Remote")
    about: str = models.TextField(max_length=1000)
    type: CareerType = models.ForeignKey(CareerType, on_delete=models.CASCADE, related_name='position_type')
    duration: str = models.CharField(max_length=80, null=True, blank=True)
    experience: str = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.name} {self.email}"

    def getLink(self, error: str = '', success: str = '', alert: str = '') -> str:
        return f'{url.getRoot()}{url.careers_apply(posID=self.id.hex)}{url.getMessageQuery(alert,error,success)}'

    def total_applicants(self):
        return CareerApplication.objects.filter(position=self).count()

def resumePath(instance: "CareerApplication", filename: str) -> str:
    fileparts = filename.split('.')
    return f"{APPNAME}/careers/{str(instance.id)}_{uuid4().hex}.{fileparts[len(fileparts)-1]}"

class CareerApplication(models.Model):
    id: UUID = models.UUIDField(
        primary_key=True, default=uuid4, editable=False)
    applicant = models.ForeignKey(
        f'{PEOPLE}.Profile', on_delete=models.SET_NULL, null=True, related_name='applicant_profile')
    """profile (OneToOneField<Profile>): profile of the applicant, null if not set"""
    position: CareerPosition = models.ForeignKey(
        CareerPosition, on_delete=models.CASCADE, related_name='applicant_position')
    created_on: datetime = models.DateTimeField(
        auto_now=False, default=timezone.now)
    """created_on (DateTimeField): date and time when this applicant was created"""
    name: str = models.CharField(max_length=100)
    """name (CharField): name of the applicant"""
    email: str = models.EmailField(max_length=100)
    """email (EmailField): email of the applicant"""
    phone: str = models.CharField(max_length=100)
    """phone (ForeignKey<PhoneNumber>): phone number of the applicant"""
    resume: File = models.FileField(
        upload_to=resumePath)
    experience: str = models.TextField(max_length=500)

    def __str__(self):
        return f"{self.applicant} for {self.position}"

    def get_resume(self):
        return f"{settings.MEDIA_URL}{str(self.resume)}"
