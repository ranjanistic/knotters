from django.db import models
import uuid
from django.contrib.auth.models import PermissionsMixin
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager

class UserAccountManager(BaseUserManager):
    def create_user(self, email, first_name, last_name, password=None):
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

    def create_superuser(self, email, first_name, last_name, password):
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


def profileImagePath(instance,filename):
    return 'users/{}/'.format(str(instance.id))+'/profile/{}'.format(filename)

class User(AbstractBaseUser,PermissionsMixin):
    USERNAME_FIELD = 'email'
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(verbose_name="email", max_length=60, unique=True)
    username =  None
    first_name = models.CharField(max_length=100, default="first_name")
    last_name = models.CharField(max_length=100, default="last_name")
    profile_pic = models.ImageField(upload_to=profileImagePath,default="/users/default.png")
    date_joined = models.DateTimeField(verbose_name='date joined', auto_now_add=True)
    last_login = models.DateTimeField(verbose_name='last login', auto_now=True)
    is_verified = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    REQUIRED_FIELDS = ['first_name', 'last_name' ]

    objects = UserAccountManager()

    def __str__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        return self.is_admin

    def has_module_perms(self, app_label):
        return True

def projectImagePath(instance,filename):
    return 'projects/{}/'.format(str(instance.id))+'/{}'.format(filename)

class Tag(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=1000,null=False,blank=False)

    def __str__(self):
        return self.name

class Project(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50,null=False,blank=False)
    url = models.CharField(max_length=500,null=True,blank=True)
    image = models.FileField(upload_to=projectImagePath,max_length=500, default='/projects/default.png')
    reponame = models.CharField(max_length=500,unique=True,null=False,blank=False)
    description = models.CharField(max_length=5000,null=False,blank=False)
    tags = models.ManyToManyField(Tag)
    creator = models.ForeignKey("User", on_delete=models.CASCADE)
    def __str__(self):
        return self.name
