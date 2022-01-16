import uuid

from django.core.exceptions import ObjectDoesNotExist, ValidationError
from allauth.account.models import EmailAddress
from allauth.socialaccount.models import SocialAccount
from allauth.socialaccount.providers.github.provider import GitHubProvider
from deprecated import deprecated
from django.db import models
from django.db.models import Q
from django.core.cache import cache
from main.bots import Github
from main.methods import errorLog
from management.models import Management, ReportCategory, GhMarketApp, GhMarketPlan, Invitation
from projects.models import BaseProject, ReportedProject, ReportedSnapshot, Project, Snapshot
from moderation.models import ReportedModeration, Moderation
from django.contrib.auth.models import PermissionsMixin
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.utils import timezone
from django.conf import settings
from main.strings import Code, PROJECTS, url, MANAGEMENT
from auth2.models import PhoneNumber
from .apps import APPNAME


def isPictureDeletable(picture: str) -> bool:
    """
    Checks whether the given profile picture is stored in web server storage separately, and therefore can be deleted or not.
    """
    return picture != defaultImagePath() and not str(picture).startswith('http')


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

    @property
    def emails(self):
        return EmailAddress.objects.filter(user=self).values_list('email', flat=True)

    @property
    def phones(self):
        return PhoneNumber.objects.filter(user=self).values_list('number', flat=True)

    @property
    def get_name(self) -> str:
        if self.last_name:
            return f"{self.first_name} {self.last_name}"
        else:
            return self.first_name

    def getName(self) -> str:
        return self.get_name

    def getLink(self) -> str:
        return f"{url.getRoot(APPNAME)}{url.people.profile(userID=self.getID())}"
    
    def add_phone(self,number,country):
        number = str(number).strip()
        if PhoneNumber.objects.filter(number=number,country=country,verified=True).exists():
            return False
        primary = False
        if PhoneNumber.objects.filter(user=self).count() == 0:
            primary = True
        return PhoneNumber.objects.get_or_create(user=self,number=number,country=country, defaults=dict(
            user=self,
            number=number,
            country=country,
            primary=primary,
            verified=False
        ))


class Topic(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    creator = models.ForeignKey("Profile", on_delete=models.SET_NULL, related_name='topic_creator', null=True, blank=True)
    createdOn = models.DateTimeField(auto_now=False, default=timezone.now, null=True, blank=True)
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
    return f"{APPNAME}/avatars/{str(instance.getUserID())}_{str(uuid.uuid4().hex)}.{fileparts[len(fileparts)-1]}"

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
    bio = models.CharField(max_length=350, blank=True, null=True)
    successor = models.ForeignKey('User', null=True, blank=True, related_name='successor_profile',
                                  on_delete=models.SET_NULL, help_text='If user account gets deleted, this is to be set.')
    successor_confirmed = models.BooleanField(
        default=False, help_text='Whether the successor is confirmed, if set.')
    is_moderator = models.BooleanField(default=False)
    is_mentor = models.BooleanField(default=False)
    
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

    xp = models.IntegerField(default=1, help_text='Experience count')

    blocklist = models.ManyToManyField(
        'User', through='BlockedUser', default=[], related_name='blocked_users')
    reportlist = models.ManyToManyField(
        'User', through='ReportedUser', default=[], related_name='reported_users')

    on_boarded = models.BooleanField(default=False)

    def __str__(self) -> str:
        return self.getID() if self.is_zombie else self.user.email

    def getID(self) -> str:
        return self.id.hex

    def getUserID(self) -> str:
        return self.getID() if self.is_zombie else self.user.get_id

    @property
    def get_userid(self) -> str:
        return None if self.is_zombie else self.user.get_id

    def save(self, *args, **kwargs):
        try:
            previous = Profile.objects.get(id=self.id)
            if previous.picture != self.picture:
                if isPictureDeletable(previous.picture):
                    previous.picture.delete(False)
        except:
            pass
        super(Profile, self).save(*args, **kwargs)

    @property
    def is_manager(self):
        return Management.objects.filter(profile=self).exists()

    @property
    def phone_number(self):
        if self.user:
            return PhoneNumber.objects.filter(user=self.user,verified=True,primary=True).first()
        return None

    @property
    def phone_numbers(self):
        if self.user:
            return PhoneNumber.objects.filter(user=self.user,verified=True)
        return []

    @property
    def management(self):
        try:
            return Management.objects.get(profile=self)
        except ObjectDoesNotExist:
            return False
        except Exception as e:
            errorLog(e)
            return False

    @property
    def manager_id(self):
        try:
            return Management.objects.get(profile=self).get_id
        except ObjectDoesNotExist:
            return False
        except Exception as e:
            errorLog(e)
            return False

    @property
    def managements(self):
        return Management.objects.filter(people=self)
    
    def addToManagement(self, mgmID) -> bool:
        try:
            mgm = Management.objects.get(id=mgmID)
            if self.management == mgm:
                raise Exception(mgm)
            mgm.people.add(self)
            return True
        except:
            return False

    def removeFromManagement(self, mgmID) -> bool:
        try:
            mgm = Management.objects.get(id=mgmID,people=self)
            mgm.people.remove(self)
            return True
        except ObjectDoesNotExist:
            return False
        except Exception as e:
            errorLog(e)
            return False

    def convertToManagement(self, force=False) -> bool:
        try:
            if not self.is_normal:
                raise Exception()
            if self.is_manager:
                raise Exception()
            if force:
                if self.is_moderator:
                    done = self.unMakeModerator()
                    if not done: raise Exception()
                if self.is_mentor:
                    done = self.unMakeMentor()
                    if not done: raise Exception()
            elif self.is_moderator or self.is_mentor:
                raise Exception()
            mgm = Management.objects.create(profile=self)
            return True
        except:
            return False
    
    def makeModerator(self):
        self.is_moderator = True
        self.save()
        return True

    def unMakeModerator(self):
        if Moderation.objects.filter(moderator=self,resolved=False).exists():
            return False
        self.is_moderator = False
        self.save()
        return True

    def makeMentor(self):
        self.is_mentor = True
        self.save()
        return

    def unMakeMentor(self):
        if Project.objects.filter(mentor=self,trashed=False).exists():
            return False
        self.is_mentor = False
        self.save()
        return True

    def isRemoteDp(self) -> bool:
        return str(self.picture).startswith("http")

    @property
    def get_dp(self) -> str:
        if self.is_zombie:
            return settings.MEDIA_URL + defaultImagePath()
        dp = str(self.picture)
        return dp if self.isRemoteDp() else settings.MEDIA_URL+dp if not dp.startswith('/') else settings.MEDIA_URL + dp.removeprefix('/')

    @property
    def get_abs_dp(self) -> str:
        if self.get_dp.startswith('http:'):
            return self.get_dp
        return f"{settings.SITE}{self.get_dp}"
        
    def getDP(self) -> str:
        return self.get_dp

    @property
    def get_name(self) -> str:
        return Code.ZOMBIE if self.is_zombie else self.user.getName()

    def getName(self) -> str:
        return self.get_name

    def getFName(self) -> str:
        return Code.ZOMBIE if self.is_zombie else self.user.first_name

    def getLName(self) -> str:
        return Code.ZOMBIE if self.is_zombie else self.user.last_name or ''

    @property
    def get_email(self) -> str:
        return Code.ZOMBIEMAIL if self.is_zombie else self.user.email

    def getEmail(self) -> str:
        return self.get_email

    def getBio(self) -> str:
        return self.bio if self.bio else ''

    def getSubtitle(self) -> str:
        return self.bio if self.bio else self.ghID if self.ghID else ''
    
    @property
    def has_labels(self):
        return self.is_moderator or self.is_mentor or self.is_manager

    def get_labels(self):
        labels = []
        if self.is_moderator:
            labels.append(dict(name='MOD', theme='accent', text='moderator'))
        if self.is_mentor:
            labels.append(dict(name='MNT', theme='active', text='mentor'))
        if self.is_manager:
            labels.append(dict(name='MGR', theme='tertiary positive-text', text='manager'))
        return labels

    @property
    def theme(self):
        if self.is_moderator:
            return 'accent'
        if self.is_mentor:
            return 'active'
        if self.is_manager:
            return 'tertiary'
        return "positive"

    @property
    def text_theme(self):
        if self.is_moderator:
            return 'text-accent'
        if self.is_mentor:
            return 'text-active'
        if self.is_manager:
            return 'positive-text'
        return "text-positive"

    @property
    def ghID(self) -> str:
        """
        Github ID of profile, if linked.
        """
        if self.is_zombie:
            return None
        try:
            data = cache.get(f"socialaccount_gh_{self.get_userid}")
            if not (data and SocialAccount.objects.filter(user=self.user, provider=GitHubProvider.id).exists()):
                data = SocialAccount.objects.get(
                    user=self.user, provider=GitHubProvider.id)
                cache.set(f"socialaccount_gh_{self.get_userid}", data, settings.CACHE_SHORT)
            
            ghUser = cache.get(f"gh_user_data_{data.uid}")
            if not ghUser:
                try:
                    ghUser = Github.get_user_by_id(int(data.uid))
                    cache.set(f"gh_user_data_{data.uid}",
                            ghUser, settings.CACHE_SHORT)
                except:
                    return data.extra_data['login']
            ghID = ghUser.login
            if ghID:
                if ghID != self.githubID:
                    self.githubID = ghID
                    self.save()
            return ghID
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
        try:
            return SocialAccount.objects.filter(user=self.user, provider=GitHubProvider.id).first().get_profile_url()
        except:
            return None

    @deprecated('Use the property method for the same')
    def getGhUrl(self) -> str:
        return self.get_ghLink

    @property
    def get_link(self):
        return self.getLink()

    @property
    def get_abs_link(self) -> str:
        if self.get_link.startswith('http:'):
            return self.get_link
        return f"{settings.SITE}{self.get_link}"
        
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
        return f"{self.xp if self.xp else 0} XP" if not self.is_manager else ""

    def getXP(self) -> str:
        return self.get_xp

    def increaseXP(self, by: int = 0) -> int:
        if not self.is_active:
            return self.xp
        if self.xp == None:
            self.xp = 0
        self.xp = self.xp + by
        self.save()
        return self.xp

    def decreaseXP(self, by: int = 0) -> int:
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
        return self.xp

    def increaseTopicPoints(self, topic, by: int = 0) -> int:
        proftop, created = ProfileTopic.objects.get_or_create(
            profile=self, topic=topic, defaults=dict(
                profile=self,
                topic=topic,
                trashed=True,
                points=by,
            )
        )
        if created:
            return by
        return proftop.increasePoints(by)
        


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

    @property
    def getTopicIds(self):
        topIDs = ProfileTopic.objects.filter(profile=self, trashed=False).order_by('-points').values_list('topic__id', flat=True)
        def hexize(topUUID):
            return topUUID.hex
        return list(map(hexize,topIDs))

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

    @property
    def getTrashedTopicIds(self):
        topIDs = ProfileTopic.objects.filter(profile=self, trashed=True).order_by('-points').values_list('topic__id', flat=True)
        def hexize(topUUID):
            return topUUID.hex
        return list(map(hexize,topIDs))

    def getTrashedTopics(self):
        proftops = ProfileTopic.objects.filter(profile=self, trashed=True)
        topics = []
        for proftop in proftops:
            topics.append(proftop.topic)
        return topics

    def getTrashedTopicsData(self):
        return ProfileTopic.objects.filter(profile=self, trashed=True).order_by('-points')

    def totalTrashedTopics(self):
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

    @property
    def getAllTopicIds(self):
        topIDs = ProfileTopic.objects.filter(profile=self).order_by('-points').values_list('topic__id', flat=True)
        return list(map(lambda tid: tid.hex,topIDs))

    def getAllTopics(self):
        return self.topics.all()

    def getAllTopicsData(self):
        return ProfileTopic.objects.filter(profile=self).order_by('-points')

    def totalAllTopics(self):
        return self.topics.count()

    def isBlocked(self, user: User) -> bool:
        return BlockedUser.objects.filter(Q(profile=self, blockeduser=user) | Q(blockeduser=self.user, profile=user.profile)).exists()

    def is_blocked(self, user: User) -> bool:
        return self.isBlocked(user)

    def reportUser(self, user: User, category):
        report, _ = ReportedUser.objects.get_or_create(user=user, profile=self, category=category, defaults=dict(
            user=user, profile=self, category=category
        ))
        return report

    def reportProject(self, baseproject, category):
        """
        Because the report is liability of the reporting user, that's why this and other report methods reside in Profile class.
        """
        report, _ = ReportedProject.objects.get_or_create(baseproject=baseproject, profile=self, category=category, defaults=dict(
            baseproject=baseproject, profile=self, category=category
        ))
        return report

    def reportModeration(self, moderation, category):
        report, _ = ReportedModeration.objects.get_or_create(moderation=moderation, profile=self, category=category, defaults=dict(
            moderation=moderation, profile=self, category=category
        ))
        return report

    def reportSnapshot(self, snapshot, category):
        report, _ = ReportedSnapshot.objects.get_or_create(snapshot=snapshot, profile=self, category=category, defaults=dict(
            snapshot=snapshot, profile=self, category=category
        ))
        return report

    def blockUser(self, user: User):
        return self.blocklist.add(user)

    def unblockUser(self, user: User):
        return self.blocklist.remove(user)

    @property
    def blockedIDs(self) -> list:
        cachekey = f"blocked_userids_{self.user.id}"
        ids = cache.get(cachekey,[])
        if not len(ids):
            for block in BlockedUser.objects.filter(Q(profile=self) | Q(blockeduser=self.user)):
                if block.blockeduser == self.user:
                    ids.append(block.profile.getUserID())
                else:
                    ids.append(block.blockeduser.getID())
            if len(ids):
                cache.set(cachekey, ids, settings.CACHE_INSTANT)
        return ids

    @property
    def blockedProfiles(self) -> list:
        cachekey = f"blocked_userprofiles_{self.user.id}"
        profiles = cache.get(cachekey,[])
        if not len(profiles):
            for block in BlockedUser.objects.filter(Q(profile=self) | Q(blockeduser=self.user)):
                if block.blockeduser == self.user:
                    profiles.append(block.profile)
                else:
                    profiles.append(block.blockeduser.profile)
                if len(profiles):
                    cache.set(cachekey, profiles, settings.CACHE_INSTANT)
        return profiles

    def filterBlockedProfiles(self,profiles) -> list:
        filteredProfiles = []
        for profile in profiles:
            if not self.isBlocked(profile.user):
                filteredProfiles.append(profile)
        return filteredProfiles


    @property
    def tags(self) -> list:
        return self.topics.values_list('tags',flat=True).distinct()
    
    def recommended_projects(self, atleast=3, atmost=4):
        def approved_only(project):
            return project.is_approved
        try:
            constquery = Q(admirers=self,suspended=True,trashed=True,creator__in=self.blockedProfiles)
            query = Q(topics__in=self.topics.all())
            projects = BaseProject.objects.filter(~constquery,query).order_by('-admirers').distinct()
            projects = list(set(list(filter(approved_only,projects))))
            if len(projects) < atleast:
                projects = BaseProject.objects.filter(~constquery).order_by('-admirers').distinct()
                projects = list(set(list(filter(approved_only,projects))))
            return projects[:atmost]
        except Exception as e:
            errorLog(e)
            return []

    def recommended_topics(self, atleast=1, atmost=5):
        try:
            topics = Topic.objects.exclude(id__in=self.getAllTopicIds)[:atmost]
            return topics
        except Exception as e:
            errorLog(e)
            return []


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
    
    def get_points(self, raw=False):
        if raw: return self.points or 0
        if self.points or 0 < 10**3: return self.points or 0
        if self.points < 10**6: return f"{self.points//(10**3)}k"
        if self.points < 10**9: return f"{self.points//(10**6)}M"
        return 


class BlockedUser(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profile = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name='blocker_profile')
    blockeduser = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='blocked_user')

    class Meta:
        unique_together = ('profile', 'blockeduser')


class ReportedUser(models.Model):
    class Meta:
        unique_together = ('profile', 'user', 'category')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profile = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name='user_reporter_profile')
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='reported_user')
    category = models.ForeignKey(
        ReportCategory, on_delete=models.PROTECT, related_name='reported_user_category')

def displayMentorImagePath(instance, filename) -> str:
    fileparts = filename.split('.')
    return f"{APPNAME}/displaymentors/{str(instance.get_id)}.{fileparts[len(fileparts)-1]}"

class DisplayMentor(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profile = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name='display_mentor_profile',null=True, blank=True)
    name = models.CharField(max_length=100, null=True, blank=True)
    about = models.CharField(max_length=500, null=True, blank=True)
    picture = models.ImageField(
        upload_to=displayMentorImagePath, default=defaultImagePath, null=True, blank=True)
    website = models.URLField(max_length=500,null=True, blank=True)
    hidden = models.BooleanField(default=False)
    createdOn = models.DateTimeField(auto_now=False, default=timezone.now)

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
    def get_name(self):
        if self.profile:
            return self.profile.getName()
        return self.name

    @property
    def get_about(self):
        if self.profile:
            return self.profile.getBio()
        return self.about

    @property
    def get_link(self):
        if self.profile:
            return self.profile.getLink()
        return self.website

class ProfileSuccessorInvitation(Invitation):
    sender = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='successor_invitation_sender')
    receiver = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='successor_invitation_receiver')

    class Meta:
        unique_together = ('sender', 'receiver')

class GHMarketPurchase(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profile = models.ForeignKey(Profile, on_delete=models.SET_NULL, related_name='purchaser_profile',null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    gh_app_plan = models.ForeignKey(GhMarketPlan, on_delete=models.SET_NULL, null=True, blank=True)
    effective_date = models.DateTimeField(auto_now=False, default=timezone.now)
    next_billing_date = models.DateTimeField(auto_now=False, default=timezone.now)
    units_purchased = models.IntegerField(default=1)

    @property
    def purchase_by(self):
        return self.profile or self.email

    @property
    def is_active(self):
        if self.effective_date <= timezone.now() and self.next_billing_date > timezone.now():
            return True
        return False

def frameworkImagePath(instance, filename) -> str:
    fileparts = filename.split('.')
    return f"{APPNAME}/frameworks/{str(instance.id)}_{str(uuid.uuid4().hex)}.{fileparts[len(fileparts)-1]}"

class Framework(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=100)
    description = models.CharField(max_length=500)
    banner = models.ImageField(upload_to=frameworkImagePath, default=None, null=True, blank=True)
    primary_color = models.CharField(max_length=10,null=True, blank=True)
    secondary_color = models.CharField(max_length=10,null=True, blank=True)
    is_draft = models.BooleanField(default=True)
    creator = models.ForeignKey(Profile, on_delete=models.PROTECT, related_name='framework_creator')
    createdOn = models.DateTimeField(auto_now=False, default=timezone.now)
    trashed = models.BooleanField(default=False)
    suspended = models.BooleanField(default=False)
    admirers = models.ManyToManyField(Profile, through="FrameworkAdmirer", related_name='framework_admirers', default=[])
    reporters = models.ManyToManyField(Profile, through="FrameworkReport", related_name='framework_reporters', default=[])

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
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    framework = models.ForeignKey(Framework, on_delete=models.CASCADE, related_name='frame_framework')
    title = models.CharField(max_length=100)
    image = models.ImageField(upload_to=frameworkImagePath, default=None, null=True, blank=True)
    video = models.FileField(upload_to=frameworkImagePath, default=None,null=True, blank=True)
    attachment = models.FileField(upload_to=frameworkImagePath, default=None,null=True, blank=True)
    text = models.CharField(max_length=500)
    snapshot = models.ForeignKey(Snapshot, related_name='frame_snapshot', on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not (self.image or self.video or self.snapshot):
            raise ValidationError('At least one of image, video or snapshot must be provided')
        super(Frame, self).save(*args, **kwargs)

class FrameworkAdmirer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    framework = models.ForeignKey(Framework, on_delete=models.CASCADE, related_name='admirer_framework')
    admirer = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='admirer_profile')
    createdOn = models.DateTimeField(auto_now=False, default=timezone.now)
    
class FrameworkReport(models.Model):
    class Meta:
        unique_together = ('profile', 'framework', 'category')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='framework_reporter_profile')
    framework = models.ForeignKey(Framework, on_delete=models.CASCADE, related_name='reported_framework')
    category = models.ForeignKey(
        ReportCategory, on_delete=models.PROTECT, related_name='reported_framework_category')
