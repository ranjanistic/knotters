from auth2.tests.utils import getTestEmail, getTestName, getTestPassword
from compete.models import Competition
from compete.tests.utils import getCompTitle
from django.core.exceptions import ObjectDoesNotExist
from django.test import TestCase, tag
from main.env import BOTMAIL
from main.exceptions import (DuplicateKeyError, IllegalModeration,
                             IllegalModerationEntity, IllegalModerationState,
                             IllegalModerationType, IllegalModerator)
from main.tests.utils import getRandomStr
from moderation.apps import APPNAME
from moderation.models import *
from people.models import Profile, User
from people.tests.utils import getTestUsersInst
from projects.models import Category, License, Project
from projects.tests.utils import (getLicDesc, getLicName, getProjCategory,
                                  getProjName, getProjRepo)

from .utils import getLocalKey, getLocalValue


@tag(Code.Test.MODEL, APPNAME)
class ModerationTest(TestCase):
    @classmethod
    def setUpTestData(self) -> None:
        self.bot, _ = User.objects.get_or_create(email=BOTMAIL, defaults=dict(
            first_name='knottersbot', email=BOTMAIL, password=getTestPassword()))
        users = User.objects.bulk_create(getTestUsersInst(2))
        self.moderator = Profile.objects.create(
            user=users[0], is_moderator=True)

        self.profile = Profile.objects.create(user=users[1])
        self.mguser = User.objects.create_user(
            email=getTestEmail(), password=getTestPassword(), first_name=getTestName())
        self.mgprofile = self.mguser.profile
        self.mgprofile.convertToManagement()
        self.competition = Competition.objects.create(
            title=getCompTitle(), creator=self.mguser.profile, endAt=timezone.now()+timedelta(days=3))
        self.category = Category.objects.create(name=getProjCategory())
        self.license = License.objects.create(name=getLicName(
        ), description=getLicDesc(), creator=self.bot.profile, public=True)
        self.project = Project.objects.create(name=getProjName(
        ), creator=self.profile, reponame=getProjRepo(), category=self.category, license=self.license)

        return super().setUpTestData()
    
    def setUp(self) -> None:
        Profile.KNOTBOT()
        return super().setUp()

    def test_moderation_creation_fail(self):
        with self.assertRaises(ObjectDoesNotExist):
            Moderation.objects.create()
        with self.assertRaises(IllegalModerator):
            Moderation.objects.create(moderator=self.profile)
        with self.assertRaises(IllegalModerationType):
            Moderation.objects.create(moderator=self.moderator, type=APPNAME)
        with self.assertRaises(IllegalModerationEntity):
            Moderation.objects.create(moderator=self.moderator, type=PROJECTS)
        with self.assertRaises(IllegalModerationState):
            Moderation.objects.create(
                moderator=self.moderator, type=PROJECTS, project=self.project, status=getRandomStr())
        with self.assertRaises(IllegalModeration):
            Moderation.objects.create(
                moderator=self.moderator, type=PROJECTS, competition=self.competition)
        self.assertEqual(Moderation.objects.filter(
            moderator=self.profile).count(), 0)

    def test_moderation_creation_pass(self):
        Moderation.objects.create(
            moderator=self.moderator, type=PROJECTS, project=self.project)


@tag(Code.Test.MODEL, APPNAME)
class ModerationAttributeTest(TestCase):
    @classmethod
    def setUpTestData(self) -> None:
        self.bot, _ = User.objects.get_or_create(email=BOTMAIL, defaults=dict(
            first_name='knottersbot', email=BOTMAIL, password=getTestPassword()))
        users = User.objects.bulk_create(getTestUsersInst(3))
        self.moderator = Profile.objects.create(
            user=users[0], is_moderator=True)

        self.profile = Profile.objects.create(user=users[1])
        self.category = Category.objects.create(name=getProjCategory())
        self.license = License.objects.create(name=getLicName(
        ), description=getLicDesc(), creator=self.bot.profile, public=True)
        self.project = Project.objects.create(name=getProjName(
        ), creator=self.profile, reponame=getProjRepo(), category=self.category, license=self.license)
        self.mguser = User.objects.create_user(
            email=getTestEmail(), password=getTestPassword(), first_name=getTestName())
        self.mgprofile = self.mguser.profile
        self.mgprofile.convertToManagement()
        self.competition = Competition.objects.create(
            title=getCompTitle(), creator=self.mguser.profile, endAt=timezone.now()+timedelta(days=3))
        self.mod = Moderation.objects.create(
            moderator=self.moderator, type=PROJECTS, project=self.project)
    
    def setUp(self) -> None:
        Profile.KNOTBOT()
        return super().setUp()

    def test_moderation_methods(self):
        self.assertEqual(self.mod.getID(), self.mod.id.hex)
        self.assertEqual(self.mod.__str__(), self.project.name)
        self.assertTrue(self.mod.isRequestor(self.profile))
        self.assertEqual(self.mod.getModerateeFieldByType(), self.project)

        self.assertTrue(self.mod.isPending())
        self.assertFalse(self.mod.isRejected())
        self.assertFalse(self.mod.isApproved())

        self.assertTrue(self.mod.approve())
        self.assertTrue(self.mod.isApproved())

        self.mod.status = Code.MODERATION
        self.mod.save()
        self.assertTrue(self.mod.reject())

        self.mod.status = Code.MODERATION
        self.mod.type = COMPETE
        self.mod.competition = self.competition
        self.mod.save()
        self.competition.judges.add(self.profile)
        self.assertTrue(self.mod.isRequestor(self.profile))
        self.assertEqual(self.mod.__str__(), self.competition.title)
        self.assertEqual(self.mod.getModerateeFieldByType(), self.competition)

        self.assertTrue(self.mod.getLink().endswith(self.mod.getID()))
        self.assertTrue(self.mod.reapplyLink().endswith(
            url.moderation.reapply(modID=self.mod.getID())))
        self.assertTrue(self.mod.approveCompeteLink().endswith(
            url.moderation.approveCompete(modID=self.mod.getID())))


@tag(Code.Test.MODEL, APPNAME)
class LocalStorageTest(TestCase):

    def test_create_localstorage_error(self):
        key = getLocalKey()
        LocalStorage.objects.create(key=key, value=getLocalValue())
        with self.assertRaises(DuplicateKeyError):
            LocalStorage.objects.create(key=key, value=getLocalValue())

    def test_create_localstorage(self):
        LocalStorage.objects.create(key=getLocalKey(), value=getLocalValue())


@tag(Code.Test.MODEL, APPNAME)
class LocalStorageAttributeTest(TestCase):
    @classmethod
    def setUpTestData(self) -> None:
        self.bot, _ = User.objects.get_or_create(email=BOTMAIL, defaults=dict(
            first_name='knottersbot', email=BOTMAIL, password=getTestPassword()))
        self.local = LocalStorage.objects.create(
            key=getLocalKey(), value=getLocalValue())
    
    def setUp(self) -> None:
        Profile.KNOTBOT()
        return super().setUp()

    def test_localstorage_methods(self):
        self.assertEqual(self.local.__str__(), self.local.key)
