from django.test import TestCase, tag
from django.core.exceptions import ObjectDoesNotExist
from main.exceptions import DuplicateKeyError, IllegalModeration, IllegalModerationEntity, IllegalModerationState, IllegalModerationType, IllegalModerator
from people.models import User, Profile
from compete.models import Competition
from projects.tests.utils import TEST_PROJ_NAME, TEST_PROJ_REPO
from projects.models import Project
from compete.tests.utils import TEST_COMP_TITLE, TEST_KEY, TEST_VALUE
from people.tests.utils import getTestUsersInst
from moderation.apps import APPNAME
from moderation.models import *

@tag(Code.Test.MODEL, APPNAME)
class ModerationTest(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        users = User.objects.bulk_create(getTestUsersInst(2))
        cls.moderator = Profile.objects.create(user=users[0], is_moderator=True)

        cls.profile = Profile.objects.create(user=users[1])
        cls.competition = Competition.objects.create(title=TEST_COMP_TITLE)
        cls.project = Project.objects.create(name=TEST_PROJ_NAME, creator=cls.profile, reponame=TEST_PROJ_REPO)

        return super().setUpTestData()

    def test_moderation_creation_fail(self):
        with self.assertRaises(ObjectDoesNotExist):
            Moderation.objects.create()
        with self.assertRaises(IllegalModerator):
            Moderation.objects.create(moderator=self.profile)
        with self.assertRaises(IllegalModerationType):
            Moderation.objects.create(moderator=self.moderator,type=APPNAME)
        with self.assertRaises(IllegalModerationEntity):
            Moderation.objects.create(moderator=self.moderator, type=PROJECTS)
        with self.assertRaises(IllegalModerationState):
            Moderation.objects.create(moderator=self.moderator, type=PROJECTS, project=self.project, status='DONE')
        with self.assertRaises(IllegalModeration):
            Moderation.objects.create(moderator=self.moderator, type=PROJECTS, competition=self.competition)
        self.assertEqual(Moderation.objects.filter(moderator=self.profile).count(),0)

    def test_moderation_creation_pass(self):
        Moderation.objects.create(moderator=self.moderator,type=PROJECTS,project=self.project)
    

@tag(Code.Test.MODEL, APPNAME)
class ModerationAttributeTest(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        users = User.objects.bulk_create(getTestUsersInst(3))
        cls.moderator = Profile.objects.create(user=users[0], is_moderator=True)

        cls.profile = Profile.objects.create(user=users[1])
        cls.reporter = Profile.objects.create(user=users[2])
        cls.project = Project.objects.create(name=TEST_PROJ_NAME, creator=cls.profile, reponame=TEST_PROJ_REPO)
        cls.competition = Competition.objects.create(title=TEST_COMP_TITLE)
        cls.mod = Moderation.objects.create(moderator=cls.moderator,type=PROJECTS,project=cls.project)

    def test_moderation_methods(self):
        self.assertEqual(self.mod.getID(),self.mod.id.hex)
        self.assertEqual(self.mod.__str__(), self.project.name)
        self.assertTrue(self.mod.isRequestor(self.profile))
        self.assertEqual(self.mod.getModerateeFieldByType(),self.project)

        self.assertTrue(self.mod.isPending())
        self.assertFalse(self.mod.isRejected())
        self.assertFalse(self.mod.isApproved())

        self.assertTrue(self.mod.approve())
        self.assertTrue(self.mod.isApproved())

        self.mod.status = Code.MODERATION
        self.mod.save()
        self.assertTrue(self.mod.reject())

        self.mod.status = Code.MODERATION
        self.mod.type = PEOPLE
        self.mod.profile = self.profile
        self.mod.save()
        self.profile.reporters.add(self.reporter)
        self.assertTrue(self.mod.isRequestor(self.reporter))
        self.assertEqual(self.mod.__str__(), self.profile.getName())
        self.assertEqual(self.mod.getModerateeFieldByType(),self.profile)

        self.mod.status = Code.MODERATION
        self.mod.type = COMPETE
        self.mod.competition = self.competition
        self.mod.save()
        self.competition.judges.add(self.profile)
        self.assertTrue(self.mod.isRequestor(self.profile))
        self.assertEqual(self.mod.__str__(), self.competition.title)
        self.assertEqual(self.mod.getModerateeFieldByType(),self.competition)

        self.assertTrue(self.mod.getLink().endswith(self.mod.getID()))
        self.assertTrue(self.mod.reapplyLink().endswith(url.moderation.reapply(modID=self.mod.getID())))
        self.assertTrue(self.mod.approveCompeteLink().endswith(url.moderation.approveCompete(modID=self.mod.getID())))
        
@tag(Code.Test.MODEL, APPNAME,'local')
class LocalStorageTest(TestCase):
    
    def test_create_localstorage_error(self):
        LocalStorage.objects.create(key=TEST_KEY, value=TEST_VALUE)
        with self.assertRaises(DuplicateKeyError):
            LocalStorage.objects.create(key=TEST_KEY, value=TEST_VALUE)

    def test_create_localstorage(self):
        LocalStorage.objects.create(key=TEST_KEY, value=TEST_VALUE)

        
@tag(Code.Test.MODEL, APPNAME)
class LocalStorageAttributeTest(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.local = LocalStorage.objects.create(key=TEST_KEY, value=TEST_VALUE)

    def test_localstorage_methods(self):
        self.assertEqual(self.local.__str__(),self.local.key)
