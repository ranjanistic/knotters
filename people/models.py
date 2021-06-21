from django.db import models
import uuid
from django.contrib.auth.models import PermissionsMixin

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager

from main.settings import MEDIA_URL
from .apps import APPNAME
from main.strings import PROJECTS


def profileImagePath(instance, filename):
    return f"{APPNAME}/{instance.id}/profile/{filename}"


def defaultImagePath():
    return f"/{APPNAME}/default.png"


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
        verbose_name='date joined', auto_now_add=True)
    last_login = models.DateTimeField(verbose_name='last login', auto_now=True)
    is_admin = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    REQUIRED_FIELDS = ['first_name']

    objects = UserAccountManager()

    def __str__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        return self.is_admin

    def has_module_perms(self, app_label):
        return True

    def getName(self):
        if self.last_name:
            return f"{self.first_name} {self.last_name}"
        else:
            return self.first_name

    def getLink(self) -> str:
        return f"/{APPNAME}/profile/{self.id}"

class Topic(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=10)
    tags = models.ManyToManyField(f'{PROJECTS}.Tag',default=[],through=f'{PROJECTS}.Relation')

    def __str__(self) -> str:
        return self.name

class Profile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField("User", on_delete=models.CASCADE,related_name='profile')
    picture = models.ImageField(
        upload_to=profileImagePath, default=defaultImagePath,null=True, blank=True)
    is_moderator = models.BooleanField(default=False)
    githubID = models.CharField(max_length=40, blank=True, null=True)
    bio = models.CharField(max_length=100, blank=True, null=True)
    topics = models.ManyToManyField(Topic,through='Relation',default=[])
    is_verified = models.BooleanField(default=False)
    
    def __str__(self) -> str:
        return self.user.email

    def getDP(self):
        dp = str(self.picture)
        return dp if dp.startswith("http") else MEDIA_URL+dp if not dp.startswith('/') else MEDIA_URL + dp.removeprefix('/')

    def getBio(self) -> str:
        return self.bio if self.bio else ''

    def getSubtitle(self) -> str:
        return self.bio if self.bio else self.githubID if self.githubID else ''

    def getGhUrl(self) -> str:
        return f"https://github.com/{self.githubID}"

    def getLink(self, error='', success='') -> str:
        if error:
            error = f"?e={error}"
        elif success:
            success = f"?s={success}"
        if self.githubID:
            return f"/{APPNAME}/profile/{self.githubID}{success}{error}"
        return f"/{APPNAME}/profile/{self.user.id}{success}{error}"
    
class Relation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profile = models.ForeignKey(Profile,on_delete=models.CASCADE)
    topic = models.ForeignKey(Topic,on_delete=models.CASCADE)

    class Meta:
        unique_together = ('profile','topic')