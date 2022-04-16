from datetime import datetime
from re import sub as re_sub
from uuid import UUID, uuid4

from allauth.account.models import EmailAddress
from allauth.socialaccount.models import SocialAccount
from allauth.socialaccount.providers.github.provider import GitHubProvider
from allauth_2fa.utils import user_has_valid_totp_device
from auth2.models import Country, PhoneNumber
from deprecated import deprecated
from django.conf import settings
from django.contrib.auth.models import (AbstractBaseUser, BaseUserManager,
                                        PermissionsMixin)
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.files.base import File
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django_otp import devices_for_user
from github.NamedUser import NamedUser
from github.Organization import Organization
from main.bots import GH_API, GHub
from main.env import BOTMAIL
from main.methods import errorLog, user_device_notify
from main.strings import MANAGEMENT, PROJECTS, Code, classAttrsToDict, url
from management.models import (GhMarketPlan, Invitation, Management,
                               ReportCategory)

from .apps import APPNAME


def isPictureDeletable(picture: str) -> bool:
    """
    Checks whether the given profile picture is a third-party picture, and therefore can be deleted or not.
    """
    return picture != defaultImagePath() and not (str(picture).startswith('http') and str(picture).startswith(settings.SITE))


class UserAccountManager(BaseUserManager):
    def create_user(self, email, first_name, last_name=None, password=None) -> "User":
        if not email:
            raise ValueError('Users must have an email address')
        user = self.model(
            email=self.normalize_email(email),
        )

        user.first_name = first_name
        user.last_name = last_name
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, first_name, password, last_name=None) -> "User":
        user = self.create_user(
            email=self.normalize_email(email),
            password=password,
            first_name=first_name,
            last_name=last_name
        )

        user.is_admin = True
        user.is_staff = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser, PermissionsMixin):
    """The base User model. This gets deleted when user deletes account.
    This model should be refrained from being used in relations with other
    models which depend on presence of user proile. Profile model should be the primary choice for user relations.
    """
    USERNAME_FIELD = 'email'
    id: UUID = models.UUIDField(
        primary_key=True, default=uuid4, editable=False)
    email: str = models.EmailField(
        verbose_name="email", max_length=60, unique=True)
    username = None
    first_name: str = models.CharField(max_length=100)
    last_name: str = models.CharField(max_length=100, null=True, blank=True)

    date_joined: datetime = models.DateTimeField(
        verbose_name='date joined', default=timezone.now)
    last_login: datetime = models.DateTimeField(
        verbose_name='last login', auto_now=True)
    is_admin: bool = models.BooleanField(default=False)
    is_active: bool = models.BooleanField(default=True)
    is_staff: bool = models.BooleanField(default=False)

    REQUIRED_FIELDS: list = ['first_name']

    objects: UserAccountManager = UserAccountManager()

    def __str__(self) -> str:
        return self.email

    @property
    def get_id(self) -> str:
        """Returns the user's ID hex. The is the only ID to be used while referencing the user."""
        return self.id.hex

    def getID(self) -> str:
        return self.get_id

    def has_perm(self, perm, obj=None):
        return self.is_admin

    def has_module_perms(self, app_label):
        return True

    def emails(self, require_verified=False) -> list:
        """Returns all emails of the user.

        Args:
            require_verified (bool, optional): If True, only returns verified emails. Defaults to False.

        Returns:
            list<string>: All emails of the user.
        """
        if require_verified:
            return EmailAddress.objects.filter(user=self, verified=True).values_list('email', flat=True)
        return EmailAddress.objects.filter(user=self).values_list('email', flat=True)

    def get_emailaddresses(self, require_verified=False) -> models.QuerySet:
        """Returns all Emailaddress instances of the user.

        Args:
            require_verified (bool, optional): If True, only returns verified Emailaddress instances. Defaults to False.

        Returns:
            models.QuerySet<Emailaddress>: All Emailaddress instances of the user.
        """
        if require_verified:
            return EmailAddress.objects.filter(user=self, verified=True)
        return EmailAddress.objects.filter(user=self)

    def phones(self, require_verified=False) -> list:
        """Returns all phones of the user.

        Args:
            require_verified (bool, optional): If True, only returns verified phones. Defaults to False.

        Returns:
            list<string>: All phones of the user.
        """
        if require_verified:
            return PhoneNumber.objects.filter(user=self, verified=True).values_list('phone', flat=True)
        return PhoneNumber.objects.filter(user=self).values_list('number', flat=True)

    def get_phonenumbers(self, require_verified=False) -> models.QuerySet:
        """Returns all PhoneNumber instances of the user.

        Args:
            require_verified (bool, optional): If True, only returns verified PhoneNumber instances. Defaults to False.

        Returns:
            models.QuerySet<PhoneNumber>: All PhoneNumber instances of the user.
        """
        if require_verified:
            return PhoneNumber.objects.filter(user=self, verified=True)
        return PhoneNumber.objects.filter(user=self)

    @property
    def get_name(self) -> str:
        """Returns the proper display name of the user."""
        if self.last_name:
            return f"{self.first_name} {self.last_name}"
        else:
            return self.first_name

    def getName(self) -> str:
        return self.get_name

    @property
    def get_link(self) -> str:
        """Returns the link to the user's profile page."""
        return f"{url.getRoot(APPNAME)}{url.people.profile(userID=self.getID())}"

    def getLink(self) -> str:
        """Returns the link to the user's profile page."""
        return f"{url.getRoot(APPNAME)}{url.people.profile(userID=self.getID())}"

    def has_totp_device_enabled(self) -> bool:
        """Returns True if the user has a 2FA totp device enabled."""
        return user_has_valid_totp_device(user=self)

    def verify_totp(self, token) -> bool:
        """Verifies the given totp token for the user."""
        for device in devices_for_user(self, True):
            if device.verify_token(token):
                break
        else:
            return False
        return True

    def add_phone(self, number: str, country: Country, verified: bool = False) -> PhoneNumber:
        """Adds a phone number to the user's profile.

        Args:
            number (str): The phone number to add.
            country (Country): The country the phone number is from.
            verified (bool, optional): If True, sets the phone number as verified. Defaults to False.

        Returns:
            PhoneNumber: The newly created PhoneNumber instance.
        """
        number = str(number)[:30].strip()
        if PhoneNumber.objects.filter(number=number, country=country, verified=True).exists():
            return False
        primary = False
        if PhoneNumber.objects.filter(user=self).count() == 0:
            primary = True
        return PhoneNumber.objects.get_or_create(user=self, number=number, country=country, defaults=dict(
            user=self,
            number=number,
            country=country,
            primary=primary,
            verified=verified
        ))


class Topic(models.Model):
    """The Topic model."""
    id: UUID = models.UUIDField(
        primary_key=True, default=uuid4, editable=False)
    name: str = models.CharField(max_length=100)
    """name (CharField): The name of the topic."""
    creator: "Profile" = models.ForeignKey("Profile", on_delete=models.SET_NULL,
                                           related_name='topic_creator', null=True, blank=True)
    """creator (ForeignKey): The profile that created the topic."""
    createdOn: datetime = models.DateTimeField(
        auto_now=False, default=timezone.now, null=True, blank=True)
    """createdOn (DateTimeField): The date and time the topic was created."""
    tags = models.ManyToManyField(
        f'{PROJECTS}.Tag', default=[], through='TopicTag')
    """tags (ManyToManyField): The tags associated with the topic."""

    def __str__(self) -> str:
        return str(self.name)

    @property
    def get_id(self) -> str:
        return self.id.hex

    @property
    def get_name(self) -> str:
        return self.name.lower().capitalize()

    @property
    def label_type(self) -> str:
        return Code.TOPIC

    @deprecated
    def getID(self) -> str:
        return self.get_id

    @property
    def getLink(self) -> str:
        return f"{url.getRoot(MANAGEMENT)}{url.management.label(self.label_type,self.get_id)}"

    def getProfiles(self) -> models.QuerySet:
        """Returns all profiles that are associated with the topic.

        Returns:
            models.QuerySet<Profile>: All profiles instances that are associated with the topic.
        """
        cacheKey = f"topic_profiles_{self.id}"
        topicprofiles = cache.get(cacheKey, None)
        if topicprofiles is None:
            topicprofiles = Profile.objects.filter(topics=self)
            cache.set(cacheKey, topicprofiles, settings.CACHE_SHORT)
        return topicprofiles

    def totalProfiles(self) -> int:
        return self.getProfiles().count()

    def getProfilesLimited(self, limit=50) -> models.QuerySet:
        return self.getProfiles()[:limit]

    def getTags(self) -> models.QuerySet:
        cacheKey = f"topic_tags_{self.id}"
        topictags = cache.get(cacheKey, None)
        if topictags is None:
            topictags = self.tags.all()
            cache.set(cacheKey, topictags, settings.CACHE_SHORT)
        return topictags

    def totalTags(self) -> int:
        cacheKey = f"topic_tagscount_{self.id}"
        topictagscount = cache.get(cacheKey, None)
        if topictagscount is None:
            topictagscount = self.tags.count()
            cache.set(cacheKey, topictagscount, settings.CACHE_SHORT)
        return topictagscount

    def getProjects(self) -> models.QuerySet:
        """Returns all projects that are associated with the topic.

        Returns:
            models.QuerySet<Project>: All projects instances that are associated with the topic.
        """
        cacheKey = f"topic_projects_{self.id}"
        topicprojects = cache.get(cacheKey, None)
        if topicprojects is None:
            from projects.models import Project
            topicprojects = Project.objects.filter(topics=self)
            cache.set(cacheKey, topicprojects, settings.CACHE_SHORT)
        return topicprojects

    def totalProjects(self):
        return self.getProjects().count()

    def totalXP(self) -> int:
        """Cumulative XP of this topic across all profiles in community.

        Returns:
            int: The total XP of this topic across all profiles in community.
        """
        cacheKey = f"topic_totalxp_{self.id}"
        topictotalxp = cache.get(cacheKey, None)
        if topictotalxp is None:
            topictotalxp = (ProfileTopic.objects.filter(
                topic=self).aggregate(models.Sum('points')))['points__sum']
            cache.set(cacheKey, topictotalxp, settings.CACHE_SHORT)
        return topictotalxp

    def is_deletable(self) -> bool:
        """Returns True if the topic is deletable."""
        return self.totalProjects() == 0 and self.totalProfiles() == 0

    def homepage_topics(limit: int = 3) -> models.QuerySet:
        """Returns the most popular topics.

        Args:
            limit (int, optional): The number of topics to return. Defaults to 3.

        Returns:
            models.QuerySet<Topic>: The most popular topics.
        """
        cacheKey = 'homepage_topics'
        topics = cache.get(cacheKey, [])
        if not len(topics):
            topics = Topic.objects.filter()[:limit]
            cache.set(cacheKey, topics, settings.CACHE_LONG)
        return topics


class TopicTag(models.Model):
    """The model for relation between a topic and a tag."""
    class Meta:
        unique_together = ('topic', 'tag')

    id: UUID = models.UUIDField(
        primary_key=True, default=uuid4, editable=False)
    topic: Topic = models.ForeignKey(Topic, on_delete=models.CASCADE)
    tag = models.ForeignKey(f'{PROJECTS}.Tag', on_delete=models.CASCADE)


def profileImagePath(instance: "Profile", filename: str) -> str:
    fileparts = filename.split('.')
    return f"{APPNAME}/avatars/{str(instance.get_userid)}_{str(uuid4().hex)}.{fileparts[-1]}"


def defaultImagePath() -> str:
    return f"{APPNAME}/default.png"


class Profile(models.Model):
    """The Profile model of a user.

    NOTE: This model doesn't get deleted when account gets deleted, to maintain relations the many models that depend on user.
    But the user details are replaced by dummy details. (Zombie)
    """
    id: UUID = models.UUIDField(
        primary_key=True, default=uuid4, editable=False)
    user: User = models.OneToOneField(
        User, null=True, on_delete=models.SET_NULL, related_name='profile', blank=True)
    """user (OneToOneField<User>): The user that is associated with the profile."""
    createdOn: datetime = models.DateTimeField(
        auto_now=False, default=timezone.now)
    """createdOn (DateTimeField): The date and time the profile was created."""
    picture: File = models.ImageField(
        upload_to=profileImagePath, default=defaultImagePath, null=True, blank=True)
    """picture (ImageField): The profile picture."""
    githubID: str = models.CharField(
        max_length=40, null=True, default=None, blank=True)
    """githubID (CharField): The GitHub ID of the user."""
    bio: str = models.CharField(max_length=350, blank=True, null=True)
    """bio (CharField): The bio of the user."""
    successor: User = models.ForeignKey(User, null=True, blank=True, related_name='successor_profile',
                                        on_delete=models.SET_NULL, help_text='If user account gets deleted, this is to be set.')
    """successor (ForeignKey<User>): The successor of the user."""
    successor_confirmed: bool = models.BooleanField(
        default=False, help_text='Whether the successor is confirmed, if set.')
    """successor_confirmed (BooleanField): Whether the successor is confirmed."""

    is_moderator: bool = models.BooleanField(default=False)
    """is_moderator (BooleanField): Whether the user is a moderator."""
    is_mentor: bool = models.BooleanField(default=False)
    """is_mentor (BooleanField): Whether the user is a mentor."""

    is_active: bool = models.BooleanField(
        default=True, help_text='Account active/inactive status.')
    """is_active (BooleanField): Whether the account is active. This is different from the user's is_active field."""
    is_verified: bool = models.BooleanField(
        default=False, help_text='The blue tick.')
    """is_verified (BooleanField): Whether the user is verified."""
    to_be_zombie: bool = models.BooleanField(
        default=False, help_text='True if user scheduled for deletion. is_active should be false')
    """to_be_zombie (BooleanField): Whether the user is scheduled for deletion."""
    is_zombie: bool = models.BooleanField(
        default=False, help_text='If user account deleted, this becomes true')
    """is_zombie (BooleanField): Whether the user is deleted. (Profile instance remains)"""
    zombied_on: datetime = models.DateTimeField(blank=True, null=True)
    """zombied_on (DateTimeField): The date and time the user was deleted."""
    suspended: bool = models.BooleanField(
        default=False, help_text='Illegal activities make this true.')
    """suspended (BooleanField): Whether the user is suspended."""

    topics = models.ManyToManyField(Topic, through='ProfileTopic', default=[])
    """topics (ManyToManyField<Topic>): The topics the user is interested in."""
    tags = models.ManyToManyField(
        f'{PROJECTS}.Tag', through='ProfileTag', default=[])
    """tags (ManyToManyField<Tag>): The tags the user is interested in."""

    xp: int = models.IntegerField(default=1, help_text='Experience count')
    """xp (IntegerField): The profile experience count."""

    blocklist = models.ManyToManyField(
        'User', through='BlockedUser', default=[], related_name='blocked_users')
    """blocklist (ManyToManyField<User>): The users that the user has blocked."""
    reportlist = models.ManyToManyField(
        'User', through='ReportedUser', default=[], related_name='reported_users')
    """reportlist (ManyToManyField<User>): The users that the user has reported."""

    on_boarded: bool = models.BooleanField(default=False)
    """on_boarded (BooleanField): Whether the user has completed the onboarding."""

    admirers = models.ManyToManyField('Profile', through="ProfileAdmirer", default=[
    ], related_name='admirer_profiles')
    """admirers (ManyToManyField<Profile>): The users that have admired this user."""
    emoticon: str = models.CharField(
        max_length=30, null=True, default=None, blank=True)
    """emoticon (CharField): The emoticon of the user. (unique)"""
    nickname: str = models.CharField(
        max_length=30, null=True, default=None, blank=True)
    """nickname (CharField): The nickname of the user.(unique)"""

    def __str__(self) -> str:
        return self.getID() if self.is_zombie else self.user.email

    def getID(self) -> str:
        """Returns Profile model ID in hex form.
        NOTE: DO NOT use this ID or the profile model ID itself to reference the User.
        To avoid user ID confusion, this profile model has `get_userid` method for the actual and
        the only user ID to reference a profile or user model of a person.

        Returns:
            str: The profile model ID in hex form.
        """
        return self.id.hex

    def getUserID(self) -> str:
        """Returns the user ID of the user.
        NOTE: This is the actual user ID that should be used to reference a user profile.
        """
        return self.getID() if self.is_zombie else self.user.get_id

    @property
    def get_userid(self) -> str:
        """Returns the user ID of the user.
        NOTE: This is the actual user ID that should be used to reference a user profile.
        """
        return None if self.is_zombie else self.user.get_id

    def KNOTBOT() -> "Profile":
        """Returns the profile of the knottersbot. 
        This is not specific to a user, but is a global profile.
        """
        cacheKey = 'profile_knottersbot'
        knotbot = cache.get(cacheKey)
        if not knotbot:
            knotbot = Profile.objects.get(user__email=BOTMAIL)
            cache.set(cacheKey, knotbot, settings.CACHE_MAX)
        return knotbot

    @property
    def CACHE_KEYS(self):
        """Returns the cache keys for the profile instance."""
        class CKEYS():
            has_ghID = f"profile_hasghID_{self.id}"
            is_manager = f"profile_ismanager_{self.id}"
            management = f"profile_mgm_{self.id}"
            managements = f"profile_management_person_{self.id}"
            gh_user = f"gh_user_data_{self.id}"
            gh_link = f"profile_ghlink_{self.id}"
            topic_ids = f"profile_topicIDs_{self.id}"
            blocked_ids = f"blocked_userids_{self.user.id}"
            blocked_profiles = f"blocked_userprofiles_{self.user.id}"
            tags = f"profile_tags_{self.id}"
            recommended_projects = f"profile_recommendedprojects_{self.id}"
            recommended_topics = f"profile_recommendedtopics_{self.id}"
            gh_socialacc = f"socialaccount_gh_{self.id}"
            gh_user_data = f"gh_user_data_{self.id}"
            gh_user_ghorgs = f"gh_user_ghorgs_{self.id}"
            total_admirations = f'{self.id}_profile_total_admiration'
            profile_admirers = f'{self.id}_profile_admirers'
            profile_socialsites = f"profile_socialsites_{self.id}"
            socialaccount_gh = f"socialaccount_gh_{self.get_userid}"
            pallete_topics = f"pallete_topics_{self.get_userid}"
        return CKEYS()

    MODEL_CACHE_KEY = f"{APPNAME}_profiledata"

    def save(self, *args, **kwargs):
        try:
            previous: Profile = Profile.objects.get(id=self.id)
            if previous.picture != self.picture:
                if isPictureDeletable(previous.picture):
                    previous.picture.delete(False)
        except:
            pass
        super(Profile, self).save(*args, **kwargs)

    def is_manager(self) -> bool:
        """Returns True if the profile a management profile.
        This will imply that the profile represents an organization.
        """
        cacheKey = self.CACHE_KEYS.is_manager
        exists = cache.get(cacheKey, None)
        if not exists:
            exists = Management.objects.filter(profile=self).exists()
            cache.set(cacheKey, exists,
                      settings.CACHE_MAX if exists else settings.CACHE_SHORT)
        return exists

    def phone_number(self) -> "PhoneNumber":
        """Returns the primary & verified phone number instance of the user.

        Returns:
            PhoneNumber: The primary & verified phone number instance of the user.
        """
        if self.user:
            return PhoneNumber.objects.filter(user=self.user, verified=True, primary=True).first()
        return None

    def phone_numbers(self) -> models.QuerySet:
        """Returns all verified phone number instances of the user.

        Returns:
            models.QuerySet: The all verified phone number instances of the user.
        """
        if self.user:
            return PhoneNumber.objects.filter(user=self.user, verified=True)
        return []

    def get_nickname(self) -> str:
        """Returns the nickname of the user.
            Also generates and sets the nickname if not set.
        Returns:
            str: The nickname of the user.
        """
        if not self.nickname:
            if not self.is_normal:
                return None
            if self.githubID:
                nickname = self.githubID
            else:
                nickname = self.user.email.split('@')[0]
            if Profile.objects.filter(nickname__iexact=nickname).exclude(id=self.id).exists():
                nickname = nickname + str(self.get_userid)
            self.nickname = re_sub(r'[^a-zA-Z0-9\-]', "", nickname)[:50]
            self.save()
        return self.nickname

    def get_cache_one(*args, nickname=None, userID=None, throw=False) -> "Profile":
        """Returns the profile instance of the nickname or userID, preferably from cache.

        Args:
            nickname (str): The nickname of the user.
            userID (str): The user ID of the user.
            throw (bool): If True, will throw an exception if not found.

        Returns:
            Profile: The profile instance of the nickname or userID.
        """
        if nickname:
            cacheKey = f"{Profile.MODEL_CACHE_KEY}_{nickname}"
        else:
            cacheKey = f"{Profile.MODEL_CACHE_KEY}_{userID}"
        profile: Profile = cache.get(cacheKey, None)
        if not profile:
            if nickname:
                if throw:
                    profile: Profile = Profile.objects.get(
                        nickname=nickname, to_be_zombie=False, is_active=True)
                else:
                    profile: Profile = Profile.objects.filter(
                        nickname=nickname, to_be_zombie=False, is_active=True).first()
            else:
                if throw:
                    profile: Profile = Profile.objects.get(
                        user__id=userID, to_be_zombie=False, is_active=True)
                else:
                    profile: Profile = Profile.objects.filter(
                        user__id=userID, to_be_zombie=False, is_active=True).first()
            cache.set(cacheKey, profile, settings.CACHE_SHORT)
        return profile

    def total_admirers(self) -> int:
        """Returns the total number of admirers of this profile.
        """
        cacheKey = self.CACHE_KEYS.total_admirations
        count = cache.get(cacheKey, None)
        if not count:
            count = self.admirers.count()
            cache.set(cacheKey, count, settings.CACHE_INSTANT)
        return count

    def get_admirers(self) -> models.QuerySet:
        """Returns the admirers of this profile.
        """
        cacheKey = self.CACHE_KEYS.profile_admirers
        admirers = cache.get(cacheKey, [])
        if not len(admirers):
            admirers = self.admirers.all()
            cache.set(cacheKey, admirers, settings.CACHE_INSTANT)
        return admirers

    def total_admiration(self) -> int:
        """Deprecated. User total_admirers
        """
        return self.total_admirers()

    def total_admirations(self) -> int:
        """Deprecated. User total_admirers
        """
        return self.total_admirers()

    def management(self) -> Management:
        """Returns the management instance of the user, if this is a management/organization profile.

        Returns:
            Management: The management instance of the user, if this is a management/organization profile.
        """
        try:
            cacheKey = self.CACHE_KEYS.management
            data = cache.get(cacheKey, False)
            if data is False:
                data = Management.objects.get(profile=self)
                cache.set(cacheKey, data, settings.CACHE_SHORT)
            return data
        except ObjectDoesNotExist:
            return False
        except Exception as e:
            errorLog(e)
            return False

    def update_management(self, **args) -> int:
        """To update the fields of management instance of the user, if this is a management/organization profile.

        Args:
            **args: The arguments to update the management instance with.
        """
        try:
            cacheKey = self.CACHE_KEYS.management
            cache.delete(cacheKey)
            return Management.objects.filter(profile=self).update(**args)
        except Exception as e:
            errorLog(e)
            return False

    def manager_id(self) -> str:
        """Returns the ID of the management instance of the user, if this is a management/organization profile.

        Returns:
            int: The ID of the management instance of the user, if this is a management/organization profile.
        """
        try:
            return Management.objects.get(profile=self).get_id
        except ObjectDoesNotExist:
            return False
        except Exception as e:
            errorLog(e)
            return False

    def managements(self) -> models.QuerySet:
        """Returns all management instances of which this user is a member.

        Returns:
            models.QuerySet: All management instances of which this user is a member.
        """
        cacheKey = self.CACHE_KEYS.managements
        data = cache.get(cacheKey, None)
        if data is None:
            data = Management.objects.filter(people=self)
            cache.set(cacheKey, data, settings.CACHE_MINI)
        return data

    def addToManagement(self, mgmID: UUID) -> bool:
        """Adds the user to the management instance with the given ID.

        Args:
            mgmID (UUID): The ID of the management instance to add the user to.

        Returns:
            bool: True if the user was added to the management instance, False otherwise.
        """
        try:
            mgm = Management.objects.get(id=mgmID)
            if self.management() == mgm:
                raise ObjectDoesNotExist(mgm)
            mgm.people.add(self)
            return True
        except ObjectDoesNotExist:
            pass
        except Exception as e:
            errorLog(e)
            pass
        return False

    def removeFromManagement(self, mgmID: UUID) -> bool:
        """Removes the user from the management instance with the given ID.

        Args:
            mgmID (UUID): The ID of the management instance to remove the user from.

        Returns:
            bool: True if the user was removed from the management instance, False otherwise.
        """
        try:
            mgm = Management.objects.get(id=mgmID, people=self)
            mgm.people.remove(self)
            return True
        except ObjectDoesNotExist:
            pass
        except Exception as e:
            errorLog(e)
            pass
        return False

    def convertToManagement(self, force: bool = False) -> bool:
        """Converts the user to a management account by creating a management instance for it, if possible.

        Args:
            force (bool): If True, the user will be converted to a management account forcefully,
                by revoking moderator/mentor status if possible. If failed to revoke these statuses,
                then force will also not work.

        Returns:
            bool: True if the user was converted to a management account, False otherwise.
        """
        try:
            if (not self.is_normal) or self.is_manager():
                raise Exception()
            if force:
                if self.is_moderator:
                    if not self.unMakeModerator():
                        raise Exception()
                if self.is_mentor:
                    if not self.unMakeMentor():
                        raise Exception()
            elif self.is_moderator or self.is_mentor:
                raise Exception()
            if Management.objects.create(profile=self):
                cache.delete(self.CACHE_KEYS.is_manager)
            return True
        except:
            return False

    def makeModerator(self) -> bool:
        """Makes the user a moderator, if possible.

        Returns:
            bool: True if the user was made a moderator, False otherwise.
        """
        if not self.is_normal or self.is_moderator or self.is_mentor:
            return False
        self.is_moderator = True
        self.save()
        return True

    def unMakeModerator(self, altmoderator: "Profile" = None) -> bool:
        """Revokes the moderator status of the user, if possible.

        Args:
            altmoderator (Profile, optional): The moderator to transfer the pending moderations to. Defaults to None.
                If not specified, then moderator status will not be revoked if pending moderations exist.

        Returns:
            bool: True if the moderator status was revoked, False otherwise.
        """
        from moderation.models import Moderation
        if Moderation.objects.filter(moderator=self, resolved=False).exists():
            if altmoderator and altmoderator.is_moderator:
                for modn in Moderation.objects.filter(moderator=self, resolved=False):
                    modn.moderator = altmoderator
                    modn.save()
                    modn.alertModerator()
            else:
                return False
        self.is_moderator = False
        self.save()
        return True

    def makeMentor(self):
        """Makes the user a mentor, if possible.

        Returns:
            bool: True if the user was made a mentor, False otherwise.
        """
        if not self.is_normal or self.is_mentor or self.is_moderator:
            return False
        self.is_mentor = True
        self.save()
        return

    def unMakeMentor(self, altmentor: "Profile" = None):
        """Revokes the mentor status of the user, if possible.

        Args:
            altmentor (Profile, optional): The mentor to transfer the existing user's mentorships to. Defaults to None.
                If not specified, then mentor status will not be revoked if mentorships exist.

        Returns:
            bool: True if the moderator status was revoked, False otherwise.
        """
        from projects.models import CoreProject, Project
        if Project.objects.filter(mentor=self, trashed=False).exists() or CoreProject.objects.filter(mentor=self, trashed=False).exists():
            if altmentor and altmentor.is_mentor:
                Project.objects.filter(
                    mentor=self, trashed=False).update(mentor=altmentor)
                CoreProject.objects.filter(
                    mentor=self, trashed=False).update(mentor=altmentor)
            else:
                return False
        self.is_mentor = False
        self.save()
        return True

    def isRemoteDp(self) -> bool:
        """Checks if the user has a third party dp"""
        return str(self.picture).startswith("http") and not str(self.picture).startswith(settings.SITE)

    @property
    def get_dp(self) -> str:
        """Returns the user's dp URL"""
        if self.is_zombie:
            return f"{settings.MEDIA_URL}{defaultImagePath()}"
        dp = str(self.picture)
        return dp if self.isRemoteDp() else f"{settings.MEDIA_URL}{dp}" if not dp.startswith('/') else f"{settings.MEDIA_URL}{dp.removeprefix('/')}"

    @property
    def get_abs_dp(self) -> str:
        """Returns the user's dp absolute URL"""
        if self.get_dp.startswith('http:'):
            return self.get_dp
        return f"{settings.SITE}{self.get_dp}"

    def getDP(self) -> str:
        return self.get_dp

    @property
    def get_name(self) -> str:
        """Returns the user's display name"""
        return Code.ZOMBIE if self.is_zombie else self.user.getName()

    def getName(self) -> str:
        """Returns the user's display name"""
        return self.get_name

    def getFName(self) -> str:
        """Returns the user's first name"""
        return Code.ZOMBIE if self.is_zombie else self.user.first_name

    def getLName(self) -> str:
        """Returns the user's last name"""
        return Code.ZOMBIE if self.is_zombie else self.user.last_name or ''

    @property
    def get_email(self) -> str:
        """Returns the user's primary email"""
        return Code.ZOMBIEMAIL if self.is_zombie else self.user.email

    def getEmail(self) -> str:
        """Returns the user's primary email"""
        return self.get_email

    def getBio(self) -> str:
        """Returns the user's bio"""
        return self.bio if self.bio else ''

    def getSubtitle(self) -> str:
        """Returns the user's subtitle"""
        return self.bio if self.bio else self.ghID() if self.ghID() else ''

    def has_labels(self) -> bool:
        """Checks if the user has any labels (MNT, MOD)"""
        return self.is_moderator or self.is_mentor or self.is_manager()

    def get_labels(self) -> list:
        """Returns the user's labels with theme and text (MNT, MOD)

        Returns:
            list<dict): The user's labels (name,theme,text)
        """
        labels = []
        if self.is_moderator:
            labels.append(dict(name='MOD', theme='accent', text='moderator'))
        if self.is_mentor:
            labels.append(dict(name='MNT', theme='active', text='mentor'))
        if self.is_manager():
            labels.append(dict(name='MGR', theme='vibrant', text='manager'))
        return labels

    def get_label(self) -> dict:
        """Returns the user's label with theme and text (MNT, MOD)

        Returns:
            dict: The user's label (name,theme,text)
        """
        labels = self.get_labels()
        if len(labels):
            return labels[0]
        return None

    def theme(self) -> str:
        """Returns the user's theme.
        This depends on client side theme classes.
        """
        if self.is_moderator:
            return 'accent'
        if self.is_mentor:
            return 'active'
        if self.is_manager():
            return 'vibrant'
        return "positive"

    def text_theme(self) -> str:
        """Returns the user's text theme.
        This depends on client side theme classes.
        """
        if self.is_moderator:
            return 'text-accent'
        if self.is_mentor:
            return 'text-active'
        if self.is_manager():
            return 'text-vibrant'
        return "text-positive"

    def theme_text(self) -> str:
        """Returns the user's theme for text
        This depends on client side theme classes.
        """
        if self.is_moderator:
            return 'accent-text'
        if self.is_mentor:
            return 'active-text'
        if self.is_manager():
            return 'vibrant-text bold'
        return "positive-text bold"

    def socialsites(self) -> models.QuerySet:
        """Returns the user's social site instances

        Returns:
            models.QuerySet: The user's social site instances
        """
        cacheKey = self.CACHE_KEYS.profile_socialsites
        sites = cache.get(cacheKey, [])
        if not len(sites):
            sites = ProfileSocial.objects.filter(profile=self)
            if len(sites):
                cache.set(cacheKey, sites, settings.CACHE_INSTANT)
        return sites

    def gh_token(self) -> str:
        """Returns the user's GitHub access token"""
        try:
            return (SocialAccount.objects.get(user=self.user, provider=GitHubProvider.id)).token
        except:
            return None

    def gh_api(self) -> GHub:
        """Returns the GitHub API object with the user's Github access token
        """
        try:
            return GH_API(self.gh_token())
        except:
            return None

    def gh_org(self) -> Organization:
        """Returns the GitHub organization object instance linked with profile if account is a management account
        """
        try:
            return self.management().get_ghorg()
        except Exception as e:
            return None

    def gh_orgID(self) -> str:
        """Returns the GitHub organization name, linked with profile if account is a management account
        """
        try:
            return self.management().get_ghorgName()
        except Exception as e:
            return None

    def ghID(self) -> str:
        """Github ID of profile or Org, if linked.
        """
        if self.is_zombie:
            return None
        try:
            cacheKey = self.CACHE_KEYS.socialaccount_gh
            data = cache.get(cacheKey)
            if not (data and SocialAccount.objects.filter(user=self.user, provider=GitHubProvider.id).exists()):
                data = SocialAccount.objects.get(
                    user=self.user, provider=GitHubProvider.id)
                cache.set(cacheKey, data, settings.CACHE_SHORT)
            cacheKey2 = f"gh_user_data_{data.uid}"
            ghUser = cache.get(cacheKey2)
            if not ghUser:
                try:
                    ghUser = self.gh_api().get_user_by_id(int(data.uid))
                    cache.set(cacheKey2, ghUser, settings.CACHE_SHORT)
                except:
                    return data.extra_data['login']
            ghID = ghUser.login
            if ghID and ghID != self.githubID:
                self.githubID = ghID
                self.save()
            return ghID
        except:
            return None

    def has_ghID(self) -> bool:
        """Github linked or not.
        """
        cacheKey = self.CACHE_KEYS.has_ghID
        data = cache.get(cacheKey, None)
        if data is None:
            data = not self.is_zombie and SocialAccount.objects.filter(
                user=self.user, provider=GitHubProvider.id).exists()
            if data:
                cache.set(cacheKey, data, settings.CACHE_INSTANT)
        return data

    def gh_user(self) -> NamedUser:
        """Returns the GitHub NamedUser object instance linked with profile.
        """
        try:
            if not self.has_ghID():
                return None
            cachekey = f"{self.CACHE_KEYS.gh_user}{self.ghID()}"
            ghuser = cache.get(cachekey, None)
            if not ghuser:
                ghuser = self.gh_api().get_user(self.ghID())
                cache.set(cachekey, ghuser, settings.CACHE_LONG)
            return ghuser
        except Exception as e:
            return None

    def delete_github_cache(self):
        """Deletes cached data related to github account of the user.
        """
        return cache.delete_many(self.CACHE_KEYS.gh_socialacc, self.CACHE_KEYS.gh_user_data,
                                 self.CACHE_KEYS.gh_user_ghorgs, self.CACHE_KEYS.socialaccount_gh)

    def update_githubID(self, ghID: str = None) -> bool:
        """Updates the user's githubID attribute.

        Args:
            ghID (str, optional): The new githubID. Defaults to None. (Will set None by default)

        Returns:
            bool: True if the update was successful, False otherwise
        """
        if self.githubID == ghID:
            if ghID is not None:
                return True
        self.githubID = ghID
        if not ghID:
            self.delete_github_cache()
        self.save()
        return True

    def get_ghOrgs(self) -> list:
        """Returns the user's GitHub API organization object instances linked with the (if) linked Github account

        Returns:
            list<Organization>: The user's GitHub API organization object instances linked with the (if) linked Github account
        """
        try:
            cacheKey = self.CACHE_KEYS.gh_socialacc
            data = cache.get(cacheKey, None)
            if not (data and SocialAccount.objects.filter(user=self.user, provider=GitHubProvider.id).exists()):
                data = SocialAccount.objects.get(
                    user=self.user, provider=GitHubProvider.id)
                cache.set(cacheKey, data, settings.CACHE_SHORT)
            cacheKey2 = self.CACHE_KEYS.gh_user_data
            ghUser = cache.get(cacheKey2)
            if not ghUser:
                ghUser = self.gh_api().get_user_by_id(int(data.uid))
                cache.set(cacheKey2, ghUser, settings.CACHE_SHORT)
            cacheKey3 = self.CACHE_KEYS.gh_user_ghorgs
            orgs = cache.get(cacheKey3, None)
            if not orgs:
                orgs = ghUser.get_orgs()
                cache.set(cacheKey3, orgs, settings.CACHE_SHORT)
            return orgs
        except Exception as e:
            return None

    def get_ghOrgsIDName(self) -> list:
        """Returns the user's GitHub organization ids, names dict, linked with the (if) linked Github account

        Returns:
            list<dict>: The user's GitHub organization names, linked with the (if) linked Github account
        """
        try:
            return [dict(id=org.id, name=org.login) for org in self.get_ghOrgs()]
        except:
            return None

    def get_ghOrgIDs(self) -> list:
        """Returns the user's GitHub organization IDs, linked with the (if) linked Github account

        Returns:
            list<int>: The user's GitHub organization IDs, linked with the (if) linked Github account
        """
        try:
            return [org.id for org in self.get_ghOrgs()]
        except:
            return None

    def get_ghOrgNames(self) -> list:
        """Returns the user's GitHub organization names, linked with the (if) linked Github account

        Returns:
            list<int>: The user's GitHub organization names, linked with the (if) linked Github account
        """
        try:
            return [org.login for org in self.get_ghOrgs()]
        except:
            return None

    def get_ghLink(self) -> str:
        """Returns the user's GitHub profile link, linked with the (if) linked Github account"""
        try:
            cacheKey = self.CACHE_KEYS.gh_link
            data = cache.get(cacheKey, None)
            if data is None:
                data = SocialAccount.objects.filter(
                    user=self.user, provider=GitHubProvider.id).first().get_profile_url()
                if data:
                    cache.set(cacheKey, data, settings.CACHE_MINI)
            return data
        except:
            return None

    @deprecated('Use the property method for the same')
    def getGhUrl(self) -> str:
        return self.get_ghLink()

    @property
    def get_link(self) -> str:
        """Returns the user's profile URL

        Returns:
            str: The user's profile URL
        """
        return self.getLink()

    @property
    def get_abs_link(self) -> str:
        """Returns the user's profile absolute URL
        """
        if self.get_link.startswith('http:'):
            return self.get_link
        return f"{settings.SITE}{self.get_link}"

    def getLink(self, error: str = '', success: str = '', alert: str = '') -> str:
        if not self.is_zombie:
            nickname = self.get_nickname()
            if nickname:
                return f"{url.getRoot(APPNAME)}{url.people.profile(userID=nickname)}{url.getMessageQuery(alert,error,success)}"
            return f"{url.getRoot(APPNAME)}{url.people.profile(userID=self.getUserID())}{url.getMessageQuery(alert,error,success)}"
        return f'{url.getRoot(APPNAME)}{url.people.zombie(profileID=self.getID())}{url.getMessageQuery(alert,error,success)}'

    @property
    def get_short_link(self) -> str:
        """Returns the user's profile short URL

        Returns:
            str: The user's profile short URL
        """
        return f"{url.getRoot()}{url.at_nickname(nickname=self.get_nickname())}"

    @property
    def is_normal(self) -> bool:
        """Returns True if the user is a normal user, False otherwise.

            Normal is defined as a profile that:
                - Is not a zombie
                - Has profile active
                - Is not suspended
                - Is not going to be a zombie
                - Has an active user model (not a zombie)

        """
        return self.user and self.user.is_active and self.is_active and not (self.suspended or self.to_be_zombie or self.is_zombie)

    @deprecated('Use the property method for the same')
    def isNormal(self) -> bool:
        return self.is_normal

    def hasPredecessors(self) -> bool:
        """Returns True if the user has predecessors, False otherwise.
        Predecessors are those profiles which depend on user's profile for succession of their assets.

        NOTE/TODO: Currently only one successor can be opted by a user.
            Succession settings have to be updated for sepecific succession controls for a user.

        """
        return Profile.objects.filter(successor=self.user).exists()

    def predecessors(self) -> models.QuerySet:
        """Returns the user's predecessors Profile instances"""
        return Profile.objects.filter(successor=self.user)

    def getSuccessorInviteLink(self) -> str:
        """Returns the user's successor invite link, used by the user's successor to render invitation page."""
        return f"{url.getRoot(APPNAME)}{url.auth.successorInvite(predID=self.getUserID())}"

    @property
    def get_xp(self) -> str:
        """Returns the user's XP in human readable format"""
        return f"{self.xp if self.xp else 0} XP" if not self.is_manager() else ""

    def getXP(self) -> str:
        return self.get_xp

    def increaseXP(self, by: int = 0, notify: bool = True, reason: str = '') -> int:
        """Increases the user's XP by the given amount.

        Args:
            by (int): The amount to increase the user's XP by
            notify (bool): Whether to notify the user about the XP increase. Defaults to True
            reason (str): The reason for the XP increase

        Returns:
            int: The user's new XP
        """
        if not self.is_active:
            return self.xp
        if self.xp == None:
            self.xp = 0
        self.xp = self.xp + by
        self.save()
        if notify:
            user_device_notify(self.user, "Profile XP Increased!",
                               f"You have gained +{by} XP!", self.get_abs_link)
        ProfileXPRecord.objects.create(profile=self, xp=by, reason=reason)
        return self.xp

    def decreaseXP(self, by: int = 0, notify: bool = True, reason: str = '') -> int:
        """Decreases the user's XP by the given amount.

        Args:
            by (int): The amount to decrease the user's XP by
            notify (bool): Whether to notify the user about the XP decrease. Defaults to True
            reason (str): The reason for the XP decrease

        Returns:
            int: The user's new XP
        """
        if not self.is_active:
            return self.xp
        if self.xp == None:
            self.xp = 0
            self.save()
            return self.xp
        diff = self.xp - by
        if diff < 0:
            diff = 0
        if self.xp == diff:
            return self.xp
        self.xp = int(diff)
        self.save()
        if notify:
            user_device_notify(self.user, "Profile XP Decreased",
                               f"You have lost -{by} XP.", self.get_abs_link)
        ProfileXPRecord.objects.create(profile=self, xp=by, reason=reason)
        return self.xp

    def increaseTopicPoints(self, topic, by: int = 0, notify: bool = True, reason: str = '') -> int:
        """Increases the user's XP in given topic by the given amount.

        Args:
            topic (str): The topic to increase the user's XP in
            by (int): The amount to increase the user's XP by
            notify (bool): Whether to notify the user about the XP increase. Defaults to True
            reason (str): The reason for the XP increase

        Returns:
            int: The user's new XP in topic
        """
        proftop, _ = ProfileTopic.objects.get_or_create(
            profile=self, topic=topic, defaults=dict(
                profile=self,
                topic=topic,
                trashed=True,
                points=0,
            )
        )
        return proftop.increasePoints(by, notify, reason)

    def increaseBulkTopicPoints(self, topics, by: int = 0, notify: bool = True, reason: str = '') -> "ProfileBulkTopicXPRecord":
        """Increases the user's XP in given topics by the given amount.

        Args:
            topics (list): The topics to increase the user's XP in
            by (int): The amount to increase the user's XP by
            notify (bool): Whether to notify the user about the XP increase. Defaults to True
            reason (str): The reason for the XP increase

        Returns:
            ProfileBulkTopicXPRecord: The user's bulk xp record instance
        """
        proftops = []
        for topic in topics:
            proftops.append(
                ProfileTopic(
                    topic=topic,
                    profile=self,
                    trashed=True,
                    points=0
                )
            )

        ProfileTopic.objects.bulk_create(proftops, ignore_conflicts=True)

        for proftop in proftops:
            proftop.increasePoints(by, notify=False, record=False)

        profbulktoprecord = ProfileBulkTopicXPRecord.objects.create(
            xp=by, reason=reason)
        profbulktoprecord.profile_topics.set(proftops)
        if notify:
            user_device_notify(self.user, "Bulk Topics XP Increased!",
                               f"You have gained +{by} XP in multiple topics at once!", self.get_abs_link)
        return profbulktoprecord

    def decreaseTopicPoints(self, topic, by: int = 0, notify=True, reason='') -> int:
        """Decreases the user's XP in given topic by the given amount.

        Args:
            topic (str): The topic to decrease the user's XP in
            by (int): The amount to decrease the user's XP by
            notify (bool): Whether to notify the user about the XP decrease. Defaults to True
            reason (str): The reason for the XP decrease

        Returns:
            int: The user's new XP in topic
        """
        proftop, _ = ProfileTopic.objects.get_or_create(
            profile=self, topic=topic, defaults=dict(
                profile=self,
                topic=topic,
                trashed=True,
                points=0,
            )
        )
        return proftop.decreasePoints(by, notify, reason)

    def xpTarget(self) -> int:
        """Returns the user's next XP target"""
        xp = self.xp
        strxp = str(xp)
        if xp > 100:
            target = str()
            for i in range(len(strxp)):
                if i == 0:
                    target = str(int(strxp[i]) + 1)
                else:
                    target = target + '0'
            return int(target)
        else:
            return 100

    def getTopicIds(self) -> list:
        """Returns the user's visible topic ids"""
        cacheKey = self.CACHE_KEYS.topic_ids
        data = cache.get(cacheKey, None)
        if data is None:
            topIDs = ProfileTopic.objects.filter(profile=self, trashed=False).order_by(
                '-points').values_list('topic__id', flat=True)
            data = list(map(lambda t: t.hex, list(topIDs)))
            if len(data):
                cache.set(cacheKey, data, settings.CACHE_MINI)
        return data

    def getTopics(self) -> list:
        """Returns the user's  visible topics instances"""
        proftops = ProfileTopic.objects.filter(
            profile=self, trashed=False).order_by('-points')
        topics = []
        for proftop in proftops:
            topics.append(proftop.topic)
        return topics

    def getTopicsData(self) -> models.QuerySet:
        """Returns the user's visible topics relation instances list

        Returns:
            models.QuerySet<ProfileTopic>: The user's topics relation instances list
        """
        return ProfileTopic.objects.filter(profile=self, trashed=False).order_by('-points')

    def totalTopics(self) -> int:
        """Returns the user's total visible topics"""
        return ProfileTopic.objects.filter(profile=self, trashed=False).count()

    @property
    def getTrashedTopicIds(self) -> list:
        """Returns the user's trashed/invisible topic ids list"""
        topIDs = ProfileTopic.objects.filter(profile=self, trashed=True).order_by(
            '-points').values_list('topic__id', flat=True)

        def hexize(topUUID):
            return topUUID.hex
        return list(map(hexize, topIDs))

    def getTrashedTopics(self) -> list:
        """Returns the user's trashed/invisible topics instances"""
        proftops = ProfileTopic.objects.filter(profile=self, trashed=True)
        topics = []
        for proftop in proftops:
            topics.append(proftop.topic)
        return topics

    def getTrashedTopicsData(self) -> models.QuerySet:
        """Returns the user's trashed/invisible topics relation instances list"""
        return ProfileTopic.objects.filter(profile=self, trashed=True).order_by('-points')

    def totalTrashedTopics(self) -> int:
        """Returns the user's total trashed/invisible topics"""
        return ProfileTopic.objects.filter(profile=self, trashed=True).count()

    @deprecated(reason="Typo", action="Use the proper spelled one")
    def getTrahedTopics(self):
        return self.getTrashedTopics()

    @deprecated(reason="Typo", action="Use the proper spelled one")
    def getTrahedTopicsData(self):
        return self.getTrashedTopicsData()

    @deprecated(reason="Typo", action="Use the proper spelled one")
    def totalTrahedTopics(self):
        return self.totalTrashedTopics()

    def getAllTopicIds(self) -> list:
        """Returns the user's all topic ids"""
        topIDs = ProfileTopic.objects.filter(profile=self).order_by(
            '-points').values_list('topic__id', flat=True)
        return list(map(lambda tid: tid.hex, topIDs))

    def getAllTopics(self) -> list:
        """Returns the user's all topics instances"""
        proftops = ProfileTopic.objects.filter(
            profile=self).order_by('-points')
        topics = []
        for proftop in proftops:
            topics.append(proftop.topic)
        return topics

    def getPalleteTopics(self, limit: int = 2) -> list:
        """Returns the user's pallete topics instances"""
        topics = cache.get(self.CACHE_KEYS.pallete_topics, [])
        if not len(topics):
            proftops = ProfileTopic.objects.filter(
                profile=self).order_by('-points')[:limit]
            for proftop in proftops:
                topics.append(proftop.topic)
            cache.set(self.CACHE_KEYS.pallete_topics,
                      topics, settings.CACHE_MINI)
        return topics

    def getAllTopicsData(self) -> list:
        """Returns the user's all topics relation instances list"""
        return ProfileTopic.objects.filter(profile=self).order_by('-points')

    def totalAllTopics(self) -> int:
        """Returns the user's total all topics"""
        return self.topics.count()

    def isBlocked(self, user: User) -> bool:
        """Returns whether the user is blocked by the given user, or viceversa"""
        return BlockedUser.objects.filter(Q(profile=self, blockeduser=user) | Q(blockeduser=self.user, profile=user.profile)).exists()

    def isBlockedProfile(self, profile: "Profile") -> bool:
        """Returns whether the user is blocked by the given profile, or viceversa (same as isBlocked method)"""
        return BlockedUser.objects.filter(Q(profile=self, blockeduser=profile.user) | Q(blockeduser=self.user, profile=profile)).exists()

    def is_blocked(self, user: User) -> bool:
        """Returns whether the user is blocked by the given user, or viceversa"""
        return self.isBlocked(user)

    def is_blocked_profile(self, profile: "Profile") -> bool:
        """Returns whether the user is blocked by the given profile, or viceversa (same as is_blocked method)"""
        return self.isBlockedProfile(profile)

    def reportUser(self, user: User, category: ReportCategory) -> "ReportedUser":
        """Reports the given user in given category

        NOTE: Because the reporting is initial liability of the reporter, that's why this and other report methods reside in Profile class.
        """
        report, _ = ReportedUser.objects.get_or_create(user=user, profile=self, category=category, defaults=dict(
            user=user, profile=self, category=category
        ))
        return report

    def reportProject(self, baseproject, category: ReportCategory):
        """Reports the given project in given category"""
        from projects.models import ReportedProject
        report, _ = ReportedProject.objects.get_or_create(baseproject=baseproject, profile=self, category=category, defaults=dict(
            baseproject=baseproject, profile=self, category=category
        ))
        return report

    def reportModeration(self, moderation, category: ReportCategory):
        """Reports the given moderation in given category"""
        from moderation.models import ReportedModeration
        report, _ = ReportedModeration.objects.get_or_create(moderation=moderation, profile=self, category=category, defaults=dict(
            moderation=moderation, profile=self, category=category
        ))
        return report

    def reportSnapshot(self, snapshot, category: ReportCategory):
        """Reports the given snapshot in given category"""
        from projects.models import ReportedSnapshot
        report, _ = ReportedSnapshot.objects.get_or_create(snapshot=snapshot, profile=self, category=category, defaults=dict(
            snapshot=snapshot, profile=self, category=category
        ))
        return report

    def blockUser(self, user: User):
        """Blocks the given user"""
        self.blocklist.add(user)
        return True

    def unblockUser(self, user: User):
        """Unblocks the given user"""
        self.blocklist.remove(user)
        return True

    def blockedIDs(self) -> list:
        """Returns the blocked user ids (mutually blocked as well)"""
        cachekey = self.CACHE_KEYS.blocked_ids
        ids = cache.get(cachekey, [])
        if not len(ids):
            ids = list(map(lambda block: block.profile.get_userid if block.blockeduser == self.user else block.blockeduser.get_id,
                           BlockedUser.objects.filter(Q(profile=self) | Q(blockeduser=self.user))))
            cache.set(cachekey, ids, settings.CACHE_INSTANT)
        return ids

    def blockedProfiles(self) -> list:
        """Returns the blocked profiles (mutually blocked as well)

        Returns:
            list<Profile>: The blocked profiles instances list
        """
        cachekey = self.CACHE_KEYS.blocked_profiles
        profiles = cache.get(cachekey, [])
        if not len(profiles):
            profiles = list(map(lambda block: block.profile if block.blockeduser == self.user else block.blockeduser.profile,
                                BlockedUser.objects.filter(Q(profile=self) | Q(blockeduser=self.user))))
            cache.set(cachekey, profiles, settings.CACHE_INSTANT)
        return profiles

    def filterBlockedProfiles(self, profiles: list) -> list:
        """Filters the given profiles list to remove the blocked ones.

        Args:
            profiles (list<Profile>): The profiles list to filter

        Returns:
            list<Profile>: The filtered profiles list
        """
        return list(filter(lambda p: not self.isBlockedProfile(p), profiles))

    def all_tags(self) -> list:
        """Returns the user's tags instances (linked or unlinked)"""
        cacheKey = self.CACHE_KEYS.tags
        data = cache.get(cacheKey, [])
        if not len(data):
            data = self.topics.values_list('tags', flat=True).distinct()
            cache.set(cacheKey, data, settings.CACHE_MINI)
        return data

    def recommended_projects(self, atleast: int = 3, atmost: int = 4) -> list:
        """Returns the user's recommended projects instances

        Args:
            atleast (int): The minimum number of recommended projects to return
            atmost (int): The maximum number of recommended projects to return

        Returns:
            list<BaseProject>: The recommended projects instances list
        """
        try:
            cacheKey = self.CACHE_KEYS.recommended_projects
            rec_projects = cache.get(cacheKey, [])
            if not len(rec_projects):
                from projects.models import BaseProject
                constquery = ~Q(
                    admirers=self, creator__in=self.blockedProfiles())
                query = Q(topics__in=self.topics.all())
                rec_projects = BaseProject.get_approved_projects(
                    Q(query, constquery), atmost)
                if len(rec_projects) < atleast:
                    rec_projects = BaseProject.get_approved_projects(
                        constquery, atmost)
                cache.set(cacheKey, rec_projects, settings.CACHE_SHORT)
            return rec_projects[:atmost]
        except Exception as e:
            errorLog(e)
            return []

    def free_projects(self) -> models.QuerySet:
        """Returns the user's free (Quick) projects instances

        Returns:
            models.QuerySet: The free projects instances list
        """
        try:
            from projects.models import FreeProject
            return FreeProject.objects.filter(creator=self, trashed=False, suspended=False, is_archived=False)
        except Exception as e:
            errorLog(e)
            return []

    def recommended_topics(self, atleast: int = 1, atmost: int = 5) -> models.QuerySet:
        """Returns the user's recommended topics instances

        Args:
            atleast (int): The minimum number of recommended topics to return
            atmost (int): The maximum number of recommended topics to return

        Returns:
            list<Topic>: The recommended topics instances list
        """
        try:
            cacheKey = self.CACHE_KEYS.recommended_topics
            data = cache.get(cacheKey, None)
            if data is None:
                data = Topic.objects.exclude(
                    id__in=self.getAllTopicIds())[:atmost]
                if len(data):
                    cache.set(cacheKey, data, settings.CACHE_MINI)
            return data[:atmost]
        except Exception as e:
            errorLog(e)
            return []

    def nickname_profile_url(nickname: str, *args) -> str:
        """Returns the profile url for the given nickname.
        Independent of the user's profile.
        """
        cacheKey = f"nickname_profile_url_{nickname}"
        profile_url = cache.get(cacheKey, None)
        if not profile_url:
            profile = Profile.objects.get(nickname=nickname)
            profile_url = profile.get_link
            cache.set(cacheKey, profile_url, settings.CACHE_SHORT)
        return profile_url

    def emoticon_profile_url(emoticon: str, *args) -> str:
        """Returns the profile url for the given emoticon.
        Independent of the user's profile.
        """
        cacheKey = f"emoticon_profile_url_{emoticon}"
        profile_url = cache.get(cacheKey, None)
        if not profile_url:
            profile = Profile.objects.get(emoticon=emoticon)
            profile_url = profile.get_link
            cache.set(cacheKey, profile_url, settings.CACHE_SHORT)
        return profile_url

    def clearCache(self):
        return cache.delete_many(classAttrsToDict(self.CACHE_KEYS.__class__).values())


class ProfileSetting(models.Model):
    """Profile settings model
    TODO
    """
    id: UUID = models.UUIDField(
        primary_key=True, default=uuid4, editable=False)
    profile: Profile = models.OneToOneField(
        Profile, on_delete=models.CASCADE, related_name='settings_profile', null=False, blank=False)
    privatemail: bool = models.BooleanField(default=True)

    def __str__(self) -> str:
        return self.profile.getID()

    def savePreferencesLink(self) -> str:
        return f"{url.getRoot(APPNAME)}{url.people.ACCOUNTPREFERENCES}"


class ProfileTag(models.Model):
    """The model for relationship between a profile and a tag"""
    id: UUID = models.UUIDField(
        primary_key=True, default=uuid4, editable=False)
    profile: Profile = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name='tag_profile')
    """profile (ForeignKey<Profile>): The profile in relation"""
    tag = models.ForeignKey(
        f'{PROJECTS}.Tag', on_delete=models.CASCADE, related_name='profile_tag')
    """tag (ForeignKey<Tag>): The tag in relation"""

    class Meta:
        unique_together = ('profile', 'tag')


class ProfileTopic(models.Model):
    """The model for relationship between a profile and a topic"""
    id: UUID = models.UUIDField(
        primary_key=True, default=uuid4, editable=False)
    profile: Profile = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name='topic_profile')
    """profile (ForeignKey<Profile>): The profile in relation"""
    topic: Topic = models.ForeignKey(
        Topic, on_delete=models.CASCADE, related_name='profile_topic')
    """topic (ForeignKey<Topic>): The topic in relation"""
    trashed: int = models.BooleanField(default=False)
    """trashed (BooleanField): Whether the topic is trashed/invisible or not"""
    points: int = models.IntegerField(default=0)
    """points (IntegerField): The XP of profile in the topic"""

    class Meta:
        unique_together = ('profile', 'topic')

    @property
    def hidden(self) -> bool:
        return self.trashed

    def increasePoints(self, by: int = 0, notify: bool = True, reason: str = '', record: bool = True) -> int:
        """Increases the points/XP of the profile in the topic

        Args:
            by (int): The amount to increase the points/XP by
            notify (bool): Whether to notify the user of the change
            reason (str): The reason for the change
            record (bool): Whether to record the change in the profile's history

        Returns:
            int: The new XP in topic
        """
        points = 0
        if not self.points:
            points = by
        else:
            points = self.points + by
        self.points = points
        self.save()
        if notify:
            user_device_notify(self.profile.user, "Topic XP Increased!",
                               f"You have gained +{by} XP in {self.topic.get_name}! {self.points} is your current XP.{' You may add it to your profile.' if self.trashed else ''}", self.profile.get_abs_link)
        if record:
            ProfileTopicXPRecord.objects.create(
                profile_topic=self, xp=by, reason=reason)
        return self.points

    def decreasePoints(self, by: int = 0, notify: bool = True, reason: str = '') -> int:
        """Decreases the points/XP of the profile in the topic

        Args:
            by (int): The amount to decrease the points/XP by
            notify (bool): Whether to notify the user of the change
            reason (str): The reason for the change

        Returns:
            int: The new XP in topic
        """
        if not self.points:
            points = 0
        elif self.points - by < 0:
            points = 0
        else:
            points = self.points - by
        self.points = points
        self.save()
        if notify:
            user_device_notify(self.profile.user, "Topic XP decreased.",
                               f"You have lost -{by} XP in {self.topic.get_name}. {self.points} is your current XP.", self.profile.get_abs_link)
        ProfileTopicXPRecord.objects.create(
            profile_topic=self, xp=by, reason=reason)
        return self.points

    def get_points(self, raw=False) -> str:
        """Returns the human readable points/XP of the profile in the topic

        Args:
            raw (bool): Whether to return the raw points/XP
        """
        if raw:
            return self.points or 0
        if (self.points or 0) < 10**3:
            return self.points or 0
        if self.points < 10**6:
            return f"{self.points//(10**3)}k"
        if self.points < 10**9:
            return f"{self.points//(10**6)}M"
        if self.points < 10**12:
            return f"{self.points//(10**9)}B"
        return


class BlockedUser(models.Model):
    """The model for relationship between a profile and a blocked user"""
    id: UUID = models.UUIDField(
        primary_key=True, default=uuid4, editable=False)
    profile: Profile = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name='blocker_profile')
    """profile (ForeignKey<Profile>): The profile in relation"""
    blockeduser: User = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='blocked_user')
    """blockeduser (ForeignKey<User>): The blocked user in relation"""

    class Meta:
        unique_together = ('profile', 'blockeduser')


class ReportedUser(models.Model):
    """The model for relationship between a profile and a reported user"""
    class Meta:
        unique_together = ('profile', 'user', 'category')

    id: UUID = models.UUIDField(
        primary_key=True, default=uuid4, editable=False)
    profile: Profile = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name='user_reporter_profile')
    """profile (ForeignKey<Profile>): The profile in relation"""
    user: User = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='reported_user')
    """user (ForeignKey<User>): The reported user in relation"""
    category: ReportCategory = models.ForeignKey(
        ReportCategory, on_delete=models.PROTECT, related_name='reported_user_category')
    """category (ForeignKey<ReportCategory>): The category of the report"""


def displayMentorImagePath(instance: "DisplayMentor", filename: str) -> str:
    fileparts = filename.split('.')
    return f"{APPNAME}/displaymentors/{instance.get_id}.{fileparts[-1]}"


class DisplayMentor(models.Model):
    """The model for a display mentor (marketing thing)"""
    id: UUID = models.UUIDField(
        primary_key=True, default=uuid4, editable=False)
    profile: Profile = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name='display_mentor_profile', null=True, blank=True)
    """profile (ForeignKey<Profile>): The profile of display mentor, if present."""
    name: datetime = models.CharField(max_length=100, null=True, blank=True)
    """name (CharField): The name of the display mentor"""
    about: str = models.CharField(max_length=500, null=True, blank=True)
    """about (CharField): The about of the display mentor"""
    picture: str = models.ImageField(
        upload_to=displayMentorImagePath, default=defaultImagePath, null=True, blank=True)
    """picture (ImageField): The picture of the display mentor"""
    website: datetime = models.URLField(max_length=500, null=True, blank=True)
    """website (URLField): The website of the display mentor"""
    hidden: datetime = models.BooleanField(default=False)
    """hidden (BooleanField): Whether the display mentor is hidden"""
    createdOn: datetime = models.DateTimeField(
        auto_now=False, default=timezone.now)
    """createdOn (DateTimeField): The time the display mentor was created"""

    def __str__(self):
        return self.name or self.get_name or str(self.id)

    @property
    def get_id(self):
        return self.id.hex

    @property
    def get_DP(self):
        if self.profile:
            return self.profile.getDP()
        dp = str(self.picture)
        return settings.MEDIA_URL+dp if not dp.startswith('/') else settings.MEDIA_URL + dp.removeprefix('/')

    @property
    def get_name(self) -> str:
        if self.profile:
            return self.profile.getName()
        return self.name

    @property
    def get_about(self) -> str:
        if self.profile:
            return self.profile.getBio()
        return self.about

    @property
    def get_link(self) -> str:
        if self.profile:
            return self.profile.getLink()
        return self.website


class ProfileSuccessorInvitation(Invitation):
    """The model for a profile successor invitation"""
    sender: Profile = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name='successor_invitation_sender')
    receiver: Profile = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name='successor_invitation_receiver')

    class Meta:
        unique_together = ('sender', 'receiver')


class GHMarketPurchase(models.Model):
    """The model for a GitHub Marketplace purchase record of a user
    The attributes of this class are based on the GitHub Marketplace API.

    Reference: https://docs.github.com/en/rest/reference/apps#marketplace
    """
    id: UUID = models.UUIDField(
        primary_key=True, default=uuid4, editable=False)
    profile: Profile = models.ForeignKey(Profile, on_delete=models.PROTECT,
                                         related_name='purchaser_profile', null=True, blank=True)
    """profile (ForeignKey<Profile>): The profile of the purchaser"""
    email: str = models.EmailField(null=True, blank=True)
    """email (EmailField): The email of the purchaser"""
    gh_app_plan: GhMarketPlan = models.ForeignKey(
        GhMarketPlan, on_delete=models.SET_NULL, null=True, blank=True)
    """gh_app_plan (ForeignKey<GhMarketPlan>): The GitHub Marketplace plan of the purchaser"""
    effective_date: datetime = models.DateTimeField(
        auto_now=False, default=timezone.now)
    """effective_date (DateTimeField): The time the purchase was effective"""
    next_billing_date: datetime = models.DateTimeField(
        auto_now=False, default=timezone.now)
    """next_billing_date (DateTimeField): The time the purchase will be billed"""
    units_purchased: int = models.IntegerField(default=1)
    """units_purchased (IntegerField): The number of units purchased"""

    @property
    def purchase_by(self) -> "Profile|str":
        return self.profile or self.email

    @property
    def is_active(self) -> bool:
        if self.effective_date <= timezone.now() and self.next_billing_date > timezone.now():
            return True
        return False


def frameworkImagePath(instance: "Framework", filename: str) -> str:
    fileparts = filename.split('.')
    return f"{APPNAME}/frameworks/{str(instance.id)}_{uuid4().hex}.{fileparts[len(fileparts)-1]}"


class Framework(models.Model):
    """The model for a framework (Frameshot)
    TODO
    """
    id: UUID = models.UUIDField(
        primary_key=True, default=uuid4, editable=False)
    title: str = models.CharField(max_length=100)
    """title (CharField): The title of the framework"""
    description: str = models.CharField(max_length=500)
    """description (CharField): The description of the framework"""
    banner: File = models.ImageField(
        upload_to=frameworkImagePath, default=None, null=True, blank=True)
    """banner (ImageField): The banner of the framework"""
    primary_color: str = models.CharField(max_length=10, null=True, blank=True)
    """primary_color (CharField): The primary color of the framework"""
    secondary_color: str = models.CharField(
        max_length=10, null=True, blank=True)
    """secondary_color (CharField): The secondary color of the framework"""
    is_draft: bool = models.BooleanField(default=True)
    """is_draft (BooleanField): Whether the framework is a draft"""
    creator: Profile = models.ForeignKey(
        Profile, on_delete=models.PROTECT, related_name='framework_creator')
    """creator (ForeignKey<Profile>): The profile of the creator"""
    createdOn: datetime = models.DateTimeField(
        auto_now=False, default=timezone.now)
    """createdOn (DateTimeField): The time the framework was created"""
    trashed: bool = models.BooleanField(default=False)
    """trashed (BooleanField): Whether the framework is trashed"""
    suspended: bool = models.BooleanField(default=False)
    """suspended (BooleanField): Whether the framework is suspended"""
    admirers = models.ManyToManyField(
        Profile, through="FrameworkAdmirer", related_name='framework_admirers', default=[])
    """admirers (ManyToManyField<Profile>): The profiles who admire the framework"""
    reporters = models.ManyToManyField(
        Profile, through="FrameworkReport", related_name='framework_reporters', default=[])
    """reporters (ManyToManyField<Profile>): The profiles who report the framework"""

    def __str__(self):
        return self.name

    @property
    def get_image(self):
        return str(self.image)

    @property
    def total_frames(self):
        return Frame.objects.filter(framework=self)

    @property
    def frames(self):
        return Frame.objects.filter(framework=self)


class Frame(models.Model):
    """The model for a frame in a framework (Frameshot)
    TODO
    """
    id: UUID = models.UUIDField(
        primary_key=True, default=uuid4, editable=False)
    framework: Framework = models.ForeignKey(
        Framework, on_delete=models.CASCADE, related_name='frame_framework')
    """framework (ForeignKey<Framework>): The framework of the frame"""
    title: str = models.CharField(max_length=100)
    """title (CharField): The title of the frame"""
    image: File = models.ImageField(
        upload_to=frameworkImagePath, default=None, null=True, blank=True)
    """image (ImageField): The image of the frame"""
    video: File = models.FileField(upload_to=frameworkImagePath,
                                   default=None, null=True, blank=True)
    attachment: File = models.FileField(
        upload_to=frameworkImagePath, default=None, null=True, blank=True)
    text: str = models.CharField(max_length=500)
    snapshot = models.ForeignKey(
        "projects.Snapshot", related_name='frame_snapshot', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not (self.image or self.video or self.snapshot):
            raise ValidationError(
                'At least one of image, video or snapshot must be provided')
        super(Frame, self).save(*args, **kwargs)


class FrameworkAdmirer(models.Model):
    """The model relation between a framework and an admirer"""
    id: UUID = models.UUIDField(
        primary_key=True, default=uuid4, editable=False)
    framework: Framework = models.ForeignKey(
        Framework, on_delete=models.CASCADE, related_name='admirer_framework')
    admirer: Profile = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name='admirer_profile')
    createdOn: datetime = models.DateTimeField(
        auto_now=False, default=timezone.now)


class FrameworkReport(models.Model):
    """The model relation between a framework and a reporter"""
    class Meta:
        unique_together = ('profile', 'framework', 'category')

    id: UUID = models.UUIDField(
        primary_key=True, default=uuid4, editable=False)
    profile: Profile = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name='framework_reporter_profile')
    framework: Framework = models.ForeignKey(
        Framework, on_delete=models.CASCADE, related_name='reported_framework')
    category: ReportCategory = models.ForeignKey(
        ReportCategory, on_delete=models.PROTECT, related_name='reported_framework_category')


class ProfileAdmirer(models.Model):
    """The model relation between a profile and an admirer"""
    class Meta:
        unique_together = ('profile', 'admirer')

    id: UUID = models.UUIDField(
        primary_key=True, default=uuid4, editable=False)
    admirer: Profile = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name='profile_admirer_profile')
    """admirer (ForeignKey<Profile>): The admirer Profile"""
    profile: Profile = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name='admired_profile')
    """profile (ForeignKey<Profile>): The profile who is admired"""


class ProfileSocial(models.Model):
    """The model for a profile social links"""
    id: UUID = models.UUIDField(
        primary_key=True, default=uuid4, editable=False)
    profile: Profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    """profile (ForeignKey<Profile>): The profile of which the link is for"""
    site: str = models.URLField(max_length=800)
    """site (URLField): The url of the social link"""


class CoreMember(models.Model):
    """The model for a core member (marketing thing)"""
    id: UUID = models.UUIDField(
        primary_key=True, default=uuid4, editable=False)
    profile: Profile = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name='core_member_profile')
    """profile (ForeignKey<Profile>): The profile linked to core memeber."""
    hidden: bool = models.BooleanField(default=False)
    """hidden (BooleanField): Whether the core member is hidden"""
    about: str = models.CharField(max_length=500, null=True, blank=True)
    """about (CharField): The about text of the core member"""

    def __str__(self) -> str:
        return self.profile.get_name

    def get_about(self):
        return self.about or self.profile.getBio()


class ProfileXPRecord(models.Model):
    """The model for a profile xp changes record"""
    id: UUID = models.UUIDField(
        primary_key=True, default=uuid4, editable=False)
    profile: Profile = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name='profile_xp_record_profile')
    """profile (ForeignKey<Profile>): The profile of which the xp changes record is for"""
    xp: int = models.IntegerField(default=0, editable=False)
    """xp (IntegerField): The xp changes"""
    reason: str = models.TextField(max_length=500, null=True, blank=True)
    """reason (TextField): The reason for the xp changes"""
    createdOn: datetime = models.DateTimeField(
        auto_now=False, default=timezone.now)
    """createdOn (DateTimeField): The date and time of the xp changes"""


class ProfileTopicXPRecord(models.Model):
    """The model for a profile topic xp changes record"""
    id: UUID = models.UUIDField(
        primary_key=True, default=uuid4, editable=False)
    profile_topic: ProfileTopic = models.ForeignKey(
        ProfileTopic, on_delete=models.CASCADE, related_name='profilet_xp_record_profilet')
    """profile_topic (ForeignKey<ProfileTopic>): The profile topic relation instance of which the xp changes record is for"""
    xp: int = models.IntegerField(default=0, editable=False)
    """xp (IntegerField): The xp changes"""
    reason: str = models.TextField(max_length=500, null=True, blank=True)
    """reason (TextField): The reason for the xp changes"""
    createdOn: datetime = models.DateTimeField(
        auto_now=False, default=timezone.now)
    """createdOn (DateTimeField): The date and time of the xp changes"""


class ProfileBulkTopicXPRecord(models.Model):
    """The model for a profile bulk topics xp changes record"""
    id: UUID = models.UUIDField(
        primary_key=True, default=uuid4, editable=False)
    profile_topics = models.ManyToManyField(
        ProfileTopic, related_name='profilets_xp_record_profilets', through='ProfileBulkTopicXPRecordTopic', default=[])
    """profile_topics (ManyToManyField<ProfileTopic>): The profile topics relation instances of which the xp changes record is for"""
    xp: int = models.IntegerField(default=0, editable=False)
    """xp (IntegerField): The xp changes"""
    reason: str = models.TextField(max_length=500, null=True, blank=True)
    """reason (TextField): The reason for the xp changes"""
    createdOn: datetime = models.DateTimeField(
        auto_now=False, default=timezone.now)
    """createdOn (DateTimeField): The date and time of the xp changes"""


class ProfileBulkTopicXPRecordTopic(models.Model):
    """The model for relation between a profile topic relation and thier bulk xp changes record"""
    id: UUID = models.UUIDField(
        primary_key=True, default=uuid4, editable=False)
    profile_topic: ProfileTopic = models.ForeignKey(
        ProfileTopic, on_delete=models.CASCADE, related_name='profilets_xp_record_topic_profilets')
    """profile_topic (ForeignKey<ProfileTopic>): The profile topic relation instance"""
    profile_bulk_topic_xp_record: ProfileBulkTopicXPRecord = models.ForeignKey(
        ProfileBulkTopicXPRecord, on_delete=models.CASCADE, related_name='profilets_xp_record_topic_profilets_xp_record')
    """profile_bulk_topic_xp_record (ForeignKey<ProfileBulkTopicXPRecord>): The profile bulk topics xp changes record instance"""
