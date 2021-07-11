import uuid
from django.db import models
from django.contrib.auth.models import PermissionsMixin
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.utils import timezone
from main.settings import MEDIA_URL
from .apps import APPNAME
from main.strings import PROJECTS, url


class UserAccountManager(BaseUserManager):
    def create_user(self, email, first_name, last_name=None, password=None):
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

    def create_superuser(self, email, first_name, password, last_name=None):
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
    USERNAME_FIELD = 'email'
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(verbose_name="email", max_length=60, unique=True)
    username = None
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100, null=True, blank=True)

    date_joined = models.DateTimeField(
        verbose_name='date joined', default=timezone.now)
    last_login = models.DateTimeField(verbose_name='last login', auto_now=True)
    is_admin = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    REQUIRED_FIELDS = ['first_name']

    objects = UserAccountManager()

    def __str__(self) -> str:
        return self.email

    def getID(self) -> str:
        return self.id.hex

    def has_perm(self, perm, obj=None):
        return self.is_admin

    def has_module_perms(self, app_label):
        return True

    def getName(self) -> str:
        if self.last_name:
            return f"{self.first_name} {self.last_name}"
        else:
            return self.first_name

    def getLink(self) -> str:
        return f"/{APPNAME}/profile/{self.getID()}"


class Topic(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    tags = models.ManyToManyField(
        f'{PROJECTS}.Tag', default=[], through=f'{PROJECTS}.Relation')

    def __str__(self) -> str:
        return self.name


def profileImagePath(instance, filename) -> str:
    fileparts = filename.split('.')
    return f"{APPNAME}/avatars/{str(instance.id).replace('-','')}.{fileparts[len(fileparts)-1]}"


def defaultImagePath() -> str:
    return f"{APPNAME}/default.png"


class Profile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        User, null=True, on_delete=models.SET_NULL, related_name='profile', blank=True)
    createdOn = models.DateTimeField(auto_now=False, default=timezone.now)
    picture = models.ImageField(
        upload_to=profileImagePath, default=defaultImagePath, null=True, blank=True)
    is_moderator = models.BooleanField(default=False)
    githubID = models.CharField(
        max_length=40, null=True, unique=True, default=None, blank=True)
    bio = models.CharField(max_length=100, blank=True, null=True)
    successor = models.ForeignKey('User', null=True, blank=True, related_name='successor_profile',
                                  on_delete=models.SET_NULL, help_text='If user account gets deleted, this is to be set.')
    successor_confirmed = models.BooleanField(
        default=True, help_text='Whether the successor is confirmed, if set.')
    is_active = models.BooleanField(
        default=True, help_text='Account active/inactive status.')
    is_verified = models.BooleanField(
        default=False, help_text='The blue tick.')
    to_be_zombie = models.BooleanField(
        default=False, help_text='True if user scheduled for deletion. is_active should be false')
    is_zombie = models.BooleanField(
        default=False, help_text='If user account deleted, this becomes true')
    zombied_on = models.DateTimeField(blank=True,null=True)
    suspended = models.BooleanField(
        default=False, help_text='Illegal activities make this true.')

    reporters = models.ManyToManyField(
        'Profile', through='ProfileReport', related_name='profile_reporters', default=[])
    topics = models.ManyToManyField(Topic, through='ProfileTopic', default=[])

    def __str__(self) -> str:
        if self.user:
            return self.user.email
        return 'Zombie Profile'

    def getID(self)->str:
        return self.id.hex

    def save(self, *args, **kwargs):
        try:
            previous = Profile.objects.get(id=self.id)
            if previous.picture != self.picture:
                if isPictureDeletable(previous.picture):
                    previous.picture.delete(False)
        except:
            pass
        super(Profile, self).save(*args, **kwargs)

    def getDP(self) -> str:
        dp = str(self.picture)
        return dp if dp.startswith("http") else MEDIA_URL+dp if not dp.startswith('/') else MEDIA_URL + dp.removeprefix('/')

    def isRemoteDp(self) -> bool:
        return self.getDP().startswith("http")

    def getName(self) -> str:
        if self.user:
            return self.user.getName()
        return 'Zombie Profile'

    def getBio(self) -> str:
        return self.bio if self.bio else ''

    def getSubtitle(self) -> str:
        return self.bio if self.bio else self.githubID if self.githubID else ''

    def getGhUrl(self) -> str:
        return f"https://github.com/{self.githubID}" if self.githubID else ''

    def getLink(self, error: str = '', success: str = '', alert: str = '') -> str:
        if error:
            error = f"?e={error}"
        elif alert:
            alert = f"?a={alert}"
        elif success:
            success = f"?s={success}"
        if not self.is_zombie:
            if self.githubID:
                return f"/{url.PEOPLE}profile/{self.githubID}{success}{alert}{error}"
            return f"/{url.PEOPLE}profile/{self.user.getID()}{success}{alert}{error}"
        return f'/{url.PEOPLE}zombie/{self.getID()}'

    def isReporter(self, profile) -> bool:
        if profile in self.reporters.all():
            return True
        return False

    def getSuccessorInviteLink(self) -> str:
        return f"/{url.PEOPLE}invitation/successor/{self.user.getID()}"


class ProfileSetting(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profile = models.OneToOneField(
        Profile, on_delete=models.CASCADE, related_name='settings_profile')
    newsletter = models.BooleanField(default=True)
    recommendations = models.BooleanField(default=True)
    competitions = models.BooleanField(default=True)
    privatemail = models.BooleanField(default=True)

    def __str__(self) -> str:
        return self.profile.getID()
        

    def savePreferencesLink(self) -> str:
        return f"/{url.PEOPLE}account/preferences/{self.profile.user.id}"


class ProfileReport(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profile = models.ForeignKey(
        Profile, related_name='reported_profile', on_delete=models.CASCADE)
    reporter = models.ForeignKey(
        Profile, related_name='profile_reporter', on_delete=models.CASCADE)

    class Meta:
        unique_together = ('profile', 'reporter')


class ProfileTopic(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profile = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name='topic_profile')
    topic = models.ForeignKey(
        Topic, on_delete=models.CASCADE, related_name='profile_topic')

    class Meta:
        unique_together = ('profile', 'topic')

from .methods import isPictureDeletable