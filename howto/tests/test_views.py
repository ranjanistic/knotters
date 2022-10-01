from django.test import TestCase, Client, tag
from allauth.account.models import EmailAddress
from auth2.tests.utils import (getTestEmail, getTestGHID, getTestName,
                               getTestPassword)
from management.models import Management
from people.models import Profile, Topic, User
from main.env import BOTMAIL
from howto.apps import APPNAME
from people.tests.utils import getTestTopicsInst

class TestViews(TestCase):
    @classmethod
    def setUpTestData(self) -> None:
        self.bot, _ = User.objects.get_or_create(email=BOTMAIL, defaults=dict(
            first_name='knottersbot', email=BOTMAIL, password=getTestPassword()))
        management = Management.objects.create(profile=self.bot)
        self.client = Client()
        self.email = getTestEmail()
        self.ghID = getTestGHID()
        self.password = getTestPassword()
        self.user = User.objects.create_user(
            email=self.email, password=self.password, first_name=getTestName())
        self.profile = Profile.objects.get(user=self.user)
        self.moduser: User = User.objects.create_user(
            email=getTestEmail(), password=self.password, first_name=getTestName())
        self.modprofile = Profile.objects.get(user=self.moduser)
        self.modprofile.is_moderator = True
        self.modprofile.save()
        EmailAddress.objects.get_or_create(
            user=self.user, email=self.email, verified=True, primary=True)
        return super().setUpTestData()



