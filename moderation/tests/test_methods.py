from datetime import timedelta

from auth2.tests.utils import getTestEmail, getTestName, getTestPassword
from compete.tests.utils import getCompTitle
from django.test import TestCase, tag
from django.utils import timezone
from main.env import BOTMAIL
from main.tests.utils import getRandomStr
from moderation.methods import *
from people.models import User
from people.tests.utils import getTestUsersInst
from projects.models import Category, License
from projects.tests.utils import (getLicDesc, getLicName, getProjCategory,
                                  getProjName, getProjRepo)


@tag(Code.Test.METHOD, APPNAME)
class ModerationMethodTest(TestCase):
    @classmethod
    def setUpTestData(self) -> None:
        self.bot, _ = User.objects.get_or_create(email=BOTMAIL, defaults=dict(
            first_name='knottersbot', email=BOTMAIL, password=getTestPassword()))
        choices = [True, False, True, False, True, False, False]
        users = User.objects.bulk_create(getTestUsersInst(len(choices)))
        profiles = []
        c = 0
        for user in users:
            profiles.append(Profile(
                user=user,
                is_moderator=True
            ))
            c += 1
        self.profiles = Profile.objects.bulk_create(profiles)
        self.profile = self.profiles[0]
        self.mguser = User.objects.create_user(
            email=getTestEmail(), password=getTestPassword(), first_name=getTestName())
        self.mgprofile = self.mguser.profile
        self.mgprofile.convertToManagement()
        self.competition = Competition.objects.create(title=getCompTitle(
        ), creator=self.mguser.profile, endAt=timezone.now()+timedelta(days=3))
        self.competition.judges.add(self.profiles[1])
        self.competition.judges.add(self.profiles[2])
        self.category = Category.objects.create(name=getProjCategory())
        self.license = License.objects.create(name=getLicName(
        ), description=getLicDesc(), creator=self.bot.profile, public=True)
        self.project = Project.objects.create(name=getProjName(
        ), creator=self.profiles[3], reponame=getProjRepo(), category=self.category, license=self.license)
        return super().setUpTestData()

    def test_getModelByType(self):
        self.assertEqual(getModelByType(PROJECTS), Project)
        self.assertEqual(getModelByType(COMPETE), Competition)
        self.assertEqual(getModelByType(PEOPLE), Profile)
        with self.assertRaises(IllegalModerationType):
            self.assertEqual(getModelByType(getRandomStr()), Profile)

    def test_getIgnoreModProfileIDs(self):
        self.assertTrue(getIgnoreModProfileIDs(
            PROJECTS, self.project).__contains__(self.project.creator.id))
        self.assertTrue(getIgnoreModProfileIDs(COMPETE, self.competition).__contains__(
            self.competition.getJudges()[0].id))
        self.assertTrue(getIgnoreModProfileIDs(
            PEOPLE, self.profile).__contains__(self.profile.id))
        self.assertTrue(getIgnoreModProfileIDs(PEOPLE, self.profile, [
                        self.profiles[2]]).__contains__(self.profiles[2].id))
        self.assertFalse(getIgnoreModProfileIDs(PEOPLE, self.project))

    @tag('modtest')
    def test_getModeratorToAssignModeration(self):
        with self.assertRaises(IllegalModeration):
            getModeratorToAssignModeration(PROJECTS, self.profile)
        mod = getModeratorToAssignModeration(PROJECTS, self.project)
        self.assertIsInstance(mod, Profile)
        self.assertTrue(mod.is_moderator)
        self.assertTrue(mod.is_active)
        self.assertFalse(mod.is_zombie)
        self.assertNotEqual(mod, self.project.creator)
        mod2 = getModeratorToAssignModeration(COMPETE, self.competition)
        #self.assertNotEqual(mod, mod2)
        self.assertFalse(self.competition.isJudge(mod2))
        mod3 = getModeratorToAssignModeration(PEOPLE, self.profile, preferModProfiles=[
                                              self.profiles[2], self.profiles[4]])
        self.assertNotEqual(mod3, self.profile)
        self.assertTrue(
            [self.profiles[2], self.profiles[4]].__contains__(mod3))

    def test_requestModerationForObject(self):
        moderation = requestModerationForObject(self.project, PROJECTS)
        self.assertIsInstance(moderation, Moderation)
        moderation.status = Code.REJECTED
        moderation.resolved = True
        moderation.save()
        self.assertFalse(requestModerationForObject(self.project, PROJECTS))
        self.assertIsInstance(requestModerationForObject(
            self.project, PROJECTS, reassignIfRejected=True), Moderation)
