import uuid
from django.db import models
from django.contrib.auth.models import PermissionsMixin
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.utils import timezone
from main.settings import MEDIA_URL
from main.strings import Code, PROJECTS, url
from .apps import APPNAME


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
        return f"{url.getRoot(APPNAME)}{url.people.profile(userID=self.getID())}"


class Topic(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    tags = models.ManyToManyField(
        f'{PROJECTS}.Tag', default=[], through='TopicTag')

    def __str__(self) -> str:
        return self.name

    def getID(self) -> str:
        return self.id.hex


class TopicTag(models.Model):
    class Meta:
        unique_together = ('topic', 'tag')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE)
    tag = models.ForeignKey(f'{PROJECTS}.Tag', on_delete=models.CASCADE)


def profileImagePath(instance, filename) -> str:
    fileparts = filename.split('.')
    return f"{APPNAME}/avatars/{str(instance.getID())}.{fileparts[len(fileparts)-1]}"


def defaultImagePath() -> str:
    return f"{APPNAME}/default.png"


class Profile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        User, null=True, on_delete=models.SET_NULL, related_name='profile', blank=True)
    createdOn = models.DateTimeField(auto_now=False, default=timezone.now)
    picture = models.ImageField(
        upload_to=profileImagePath, default=defaultImagePath, null=True, blank=True)
    githubID = models.CharField(
        max_length=40, null=True, default=None, blank=True)
    bio = models.CharField(max_length=100, blank=True, null=True)
    successor = models.ForeignKey('User', null=True, blank=True, related_name='successor_profile',
                                  on_delete=models.SET_NULL, help_text='If user account gets deleted, this is to be set.')
    successor_confirmed = models.BooleanField(
        default=False, help_text='Whether the successor is confirmed, if set.')
    is_moderator = models.BooleanField(default=False)
    is_manager = models.BooleanField(default=False)
    is_active = models.BooleanField(
        default=True, help_text='Account active/inactive status.')
    is_verified = models.BooleanField(
        default=False, help_text='The blue tick.')
    to_be_zombie = models.BooleanField(
        default=False, help_text='True if user scheduled for deletion. is_active should be false')
    is_zombie = models.BooleanField(
        default=False, help_text='If user account deleted, this becomes true')
    zombied_on = models.DateTimeField(blank=True, null=True)
    suspended = models.BooleanField(
        default=False, help_text='Illegal activities make this true.')

    reporters = models.ManyToManyField(
        'Profile', through='ProfileReport', related_name='profile_reporters', default=[])
    topics = models.ManyToManyField(Topic, through='ProfileTopic', default=[])

    xp = models.IntegerField(default=10, help_text='Experience count')

    def __str__(self) -> str:
        return self.getID() if self.is_zombie else self.user.email

    def getID(self) -> str:
        return self.id.hex

    def getUserID(self) -> str:
        return self.getID() if self.is_zombie else self.user.getID()

    def save(self, *args, **kwargs):
        try:
            previous = Profile.objects.get(id=self.id)
            if previous.picture != self.picture:
                if isPictureDeletable(previous.picture):
                    previous.picture.delete(False)
        except:
            pass
        super(Profile, self).save(*args, **kwargs)

    def isRemoteDp(self) -> bool:
        return str(self.picture).startswith("http")

    def getDP(self) -> str:
        dp = str(self.picture)
        return dp if self.isRemoteDp() else MEDIA_URL+dp if not dp.startswith('/') else MEDIA_URL + dp.removeprefix('/')

    def getName(self) -> str:
        return Code.ZOMBIE if self.is_zombie else self.user.getName()

    def getFName(self) -> str:
        return Code.ZOMBIE if self.is_zombie else self.user.first_name

    def getEmail(self) -> str:
        return Code.ZOMBIEMAIL if self.is_zombie else self.user.email

    def getBio(self) -> str:
        return self.bio if self.bio else ''

    def getSubtitle(self) -> str:
        return self.bio if self.bio else self.githubID if self.githubID else ''

    def getGhUrl(self) -> str:
        return url.githubProfile(ghID=self.githubID) if self.githubID else ''

    def getLink(self, error: str = '', success: str = '', alert: str = '') -> str:
        if not self.is_zombie:
            if self.githubID:
                return f"{url.getRoot(APPNAME)}{url.people.profile(userID=self.githubID)}{url.getMessageQuery(alert,error,success)}"
            return f"{url.getRoot(APPNAME)}{url.people.profile(userID=self.getUserID())}{url.getMessageQuery(alert,error,success)}"
        return f'{url.getRoot(APPNAME)}{url.people.zombie(profileID=self.getID())}{url.getMessageQuery(alert,error,success)}'

    def isNormal(self) -> bool:
        return self.user and self.user.is_active and self.is_active and not (self.suspended or self.to_be_zombie or self.is_zombie)

    def isReporter(self, profile) -> bool:
        if profile in self.reporters.all():
            return True
        return False

    def getSuccessorInviteLink(self) -> str:
        return f"{url.getRoot(APPNAME)}{url.people.successorInvite(predID=self.getUserID())}"

    def getXP(self) -> str:
        return f"{self.xp} XP"

    def increaseXP(self, by: int = 0) -> int:
        if self.xp == None:
            self.xp = 0
        self.xp = self.xp + by
        self.save()
        return self.xp

    def decreaseXP(self, by: int = 0) -> int:
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
        return self.xp

    def xpTarget(self):
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

    def getTopics(self):
        proftops = ProfileTopic.objects.filter(profile=self, trashed=False)
        topics = []
        for proftop in proftops:
            topics.append(proftop.topic)
        return topics

    def getTopicsData(self):
        return ProfileTopic.objects.filter(profile=self, trashed=False).order_by('-points')

    def totalTopics(self):
        return ProfileTopic.objects.filter(profile=self, trashed=False).count()

    def getTrahedTopics(self):
        proftops = ProfileTopic.objects.filter(profile=self, trahsed=True)
        topics = []
        for proftop in proftops:
            topics.append(proftop.topic)
        return topics

    def getTrahedTopicsData(self):
        return ProfileTopic.objects.filter(profile=self, trahsed=True)

    def totalTrahedTopics(self):
        return ProfileTopic.objects.filter(profile=self, trahsed=True).count()

    def getAllTopics(self):
        proftops = ProfileTopic.objects.filter(profile=self)
        topics = []
        for proftop in proftops:
            topics.append(proftop.topic)
        return topics

    def getAllTopicsData(self):
        return ProfileTopic.objects.filter(profile=self)

    def totalAllTopics(self):
        return ProfileTopic.objects.filter(profile=self).count()


class ProfileSetting(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profile = models.OneToOneField(
        Profile, on_delete=models.CASCADE, related_name='settings_profile', null=False, blank=False)
    newsletter = models.BooleanField(default=True)
    recommendations = models.BooleanField(default=True)
    competitions = models.BooleanField(default=True)
    privatemail = models.BooleanField(default=True)

    def __str__(self) -> str:
        return self.profile.getID()

    def savePreferencesLink(self) -> str:
        return f"{url.getRoot(APPNAME)}{url.people.ACCOUNTPREFERENCES}"


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
    trashed = models.BooleanField(default=False)
    points = models.IntegerField(default=0)

    class Meta:
        unique_together = ('profile', 'topic')

    def increasePoints(self, by: int = 0) -> int:
        points = 0
        if not self.points:
            points = by
        else:
            points = self.points + by
        self.points = points
        self.save()
        return self.points

    def decreasePoints(self, by: int = 0) -> int:
        if not self.points:
            points = 0
        elif self.points - by < 0:
            points = 0
        else:
            points = self.points - by
        self.points = points
        self.save()
        return self.points

from .methods import isPictureDeletable
