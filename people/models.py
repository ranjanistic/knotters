import uuid
from allauth.socialaccount.models import SocialAccount
from allauth.socialaccount.providers.github.provider import GitHubProvider
from deprecated import deprecated
from django.db import models
from django.db.models import Q
from django.contrib.auth.models import PermissionsMixin
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.utils import timezone
from django.conf import settings
from main.strings import Code, PROJECTS, url, MANAGEMENT
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

    @property
    def get_id(self) -> str:
        return self.id.hex

    def getID(self) -> str:
        return self.get_id


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

    @property
    def get_id(self) -> str:
        return self.id.hex

    @property
    def label_type(self) -> str:
        return Code.TOPIC

    @deprecated
    def getID(self) -> str:
        return self.get_id

    @property
    def getLink(self) -> str:
        return f"{url.getRoot(MANAGEMENT)}{url.management.label(self.label_type,self.get_id)}"

    @property
    def totalProfiles(self):
        return Profile.objects.filter(topics=self).count()

    @property
    def getProfiles(self):
        return Profile.objects.filter(topics=self)

    @property
    def getProfilesLimited(self):
        return Profile.objects.filter(topics=self)[0:50]

    @property
    def totalTags(self):
        return self.tags.count()

    @property
    def getTags(self):
        return self.tags.all()

    @property
    def totalProjects(self):
        from projects.models import Project
        return Project.objects.filter(topics=self).count()

    @property
    def getProjects(self):
        from projects.models import Project
        return Project.objects.filter(topics=self)

    @property
    def totalXP(self):
        return (ProfileTopic.objects.filter(topic=self).aggregate(models.Sum('points')))['points__sum']

    @property
    def isDeletable(self) -> bool:
        if self.totalProjects > 0:
            return False
        if self.totalProfiles > 0:
            return False
        return True


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

    topics = models.ManyToManyField(Topic, through='ProfileTopic', default=[])

    blocklist = models.ManyToManyField('User', through='BlockedUser', default=[], related_name='blocked_users')

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
        if self.is_zombie:
            return settings.MEDIA_URL + defaultImagePath()
        dp = str(self.picture)
        return dp if self.isRemoteDp() else settings.MEDIA_URL+dp if not dp.startswith('/') else settings.MEDIA_URL + dp.removeprefix('/')

    def getName(self) -> str:
        return Code.ZOMBIE if self.is_zombie else self.user.getName()

    def getFName(self) -> str:
        return Code.ZOMBIE if self.is_zombie else self.user.first_name

    def getLName(self) -> str:
        return Code.ZOMBIE if self.is_zombie else self.user.last_name or ''

    def getEmail(self) -> str:
        return Code.ZOMBIEMAIL if self.is_zombie else self.user.email

    def getBio(self) -> str:
        return self.bio if self.bio else ''

    def getSubtitle(self) -> str:
        return self.bio if self.bio else self.githubID if self.githubID else ''

    @property
    def ghID(self) -> str:
        """
        Github ID of profile, if linked.
        """
        if self.is_zombie:
            return None
        try:
            data = SocialAccount.objects.get(user=self.user, provider=GitHubProvider.id)
            return getUsernameFromGHSocial(data)
        except:
            return None

    @property
    def has_ghID(self) -> bool:
        """
        Github linked or not.
        """
        return not self.is_zombie and SocialAccount.objects.filter(user=self.user, provider=GitHubProvider.id).exists()


    @property
    def get_ghLink(self) -> str:
        return url.githubProfile(ghID=self.ghID) if self.ghID else ''

    @deprecated('Use the property method for the same')
    def getGhUrl(self) -> str:
        return url.githubProfile(ghID=self.ghID) if self.ghID else ''

    def getLink(self, error: str = '', success: str = '', alert: str = '') -> str:
        if not self.is_zombie:
            ghID = self.ghID
            if ghID:
                return f"{url.getRoot(APPNAME)}{url.people.profile(userID=ghID)}{url.getMessageQuery(alert,error,success)}"
            return f"{url.getRoot(APPNAME)}{url.people.profile(userID=self.getUserID())}{url.getMessageQuery(alert,error,success)}"
        return f'{url.getRoot(APPNAME)}{url.people.zombie(profileID=self.getID())}{url.getMessageQuery(alert,error,success)}'

    @property
    def is_normal(self) -> bool:
        return self.user and self.user.is_active and self.is_active and not (self.suspended or self.to_be_zombie or self.is_zombie)

    
    @deprecated('Use the property method for the same')
    def isNormal(self) -> bool:
        return self.is_normal

    @property
    def hasPredecessors(self) -> bool:
        return Profile.objects.filter(successor=self.user).exists()

    @property
    def predecessors(self) -> models.QuerySet:
        return Profile.objects.filter(successor=self.user)

    def getSuccessorInviteLink(self) -> str:
        return f"{url.getRoot(APPNAME)}{url.people.successorInvite(predID=self.getUserID())}"

    @property
    def get_xp(self) -> str:
        return f"{self.xp if self.xp else 0} XP"

    def getXP(self) -> str:
        return self.get_xp

    def increaseXP(self, by: int = 0) -> int:
        if not self.is_active: return self.xp
        if self.xp == None:
            self.xp = 0
        self.xp = self.xp + by
        self.save()
        return self.xp

    def decreaseXP(self, by: int = 0) -> int:
        if not self.is_active: return self.xp
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

    def getTrashedTopics(self):
        proftops = ProfileTopic.objects.filter(profile=self, trashed=True)
        topics = []
        for proftop in proftops:
            topics.append(proftop.topic)
        return topics

    def getTrashedTopicsData(self):
        return ProfileTopic.objects.filter(profile=self, trashed=True)

    def totalTrashedTopics(self):
        return ProfileTopic.objects.filter(profile=self, trashed=True).count()

    @deprecated(reason="Typo", action="Use the proper spelled one")
    def getTrahedTopics(self):
        proftops = ProfileTopic.objects.filter(profile=self, trashed=True)
        topics = []
        for proftop in proftops:
            topics.append(proftop.topic)
        return topics

    @deprecated(reason="Typo", action="Use the proper spelled one")
    def getTrahedTopicsData(self):
        return ProfileTopic.objects.filter(profile=self, trashed=True)

    @deprecated(reason="Typo", action="Use the proper spelled one")
    def totalTrahedTopics(self):
        return ProfileTopic.objects.filter(profile=self, trashed=True).count()

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

    def isBlocked(self, user:User) -> bool:
        return BlockedUser.objects.filter(profile=self,blockeduser=user).exists() or BlockedUser.objects.filter(profile=user.profile,blockeduser=self.user).exists()

    def blockUser(self,user:User):
        return self.blocklist.add(user)

    def unblockUser(self,user:User):
        return self.blocklist.remove(user)
        

    @property
    def blockedIDs(self) -> list:
        ids = []
        for block in BlockedUser.objects.filter(Q(profile=self)|Q(blockeduser=self.user)):
            if block.blockeduser == self.user:
                ids.append(block.profile.getUserID())
            else:
                ids.append(block.blockeduser.getID())
        return ids

    @property
    def blockedProfiles(self) -> list:
        profiles = []
        for block in BlockedUser.objects.filter(Q(profile=self)|Q(blockeduser=self.user)):
            if block.blockeduser == self.user:
                profiles.append(block.profile)
            else:
                profiles.append(block.blockeduser.profile)
        return profiles


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

    @property
    def hidden(self) -> bool:
        return self.trashed


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

class BlockedUser(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='blocker_profile')
    blockeduser = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blocked_user')

    class Meta:
        unique_together = ('profile', 'blockeduser')

from .methods import isPictureDeletable, getUsernameFromGHSocial
