from people.tests.utils import getTestUsersInst
from people.models import User
from django.test import TestCase, tag
from moderation.methods import *
from projects.tests.utils import TEST_PROJ_NAME, TEST_PROJ_REPO
from compete.tests.utils import TEST_COMP_TITLE

@tag(Code.Test.METHOD,APPNAME)
class ModerationMethodTest(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        choices = [True, False, True, False, True, False, False]
        users = User.objects.bulk_create(getTestUsersInst(len(choices)))
        profiles = []
        c = 0
        for user in users:
            profiles.append(Profile(
                user=user,
                is_moderator=choices[c]
            ))
            c+=1
        cls.profiles = Profile.objects.bulk_create(profiles)
        cls.profile = cls.profiles[0]
        cls.competition = Competition.objects.create(title=TEST_COMP_TITLE)
        cls.competition.judges.add(cls.profiles[1])
        cls.competition.judges.add(cls.profiles[2])
        cls.project = Project.objects.create(name=TEST_PROJ_NAME, creator=cls.profiles[3], reponame=TEST_PROJ_REPO)
        return super().setUpTestData()

    def test_getModelByType(self):
        self.assertEqual(getModelByType(PROJECTS), Project)
        self.assertEqual(getModelByType(COMPETE), Competition)
        self.assertEqual(getModelByType(PEOPLE), Profile)
        with self.assertRaises(IllegalModerationType):
            self.assertEqual(getModelByType(""), Profile)

    def test_getIgnoreModProfileIDs(self):
        self.assertTrue(getIgnoreModProfileIDs(PROJECTS, self.project).__contains__(self.project.creator.id))
        self.assertTrue(getIgnoreModProfileIDs(COMPETE, self.competition).__contains__(self.competition.getJudges()[0].id))
        self.assertTrue(getIgnoreModProfileIDs(PEOPLE, self.profile).__contains__(self.profile.id))
        self.assertTrue(getIgnoreModProfileIDs(PEOPLE, self.profile, [self.profiles[2]]).__contains__(self.profiles[2].id))
        self.assertFalse(getIgnoreModProfileIDs(PEOPLE, self.project))
        
    def test_getModeratorToAssignModeration(self):
        with self.assertRaises(IllegalModeration):
            getModeratorToAssignModeration(PROJECTS,self.profile)
        mod = getModeratorToAssignModeration(PROJECTS,self.project)
        self.assertIsInstance(mod,Profile)
        self.assertTrue(mod.is_moderator)
        self.assertTrue(mod.is_active)
        self.assertFalse(mod.is_zombie)
        self.assertNotEqual(mod,self.project.creator)
        mod2 = getModeratorToAssignModeration(COMPETE,self.competition)
        self.assertNotEqual(mod,mod2)
        self.assertFalse(self.competition.isJudge(mod2))
        mod3 = getModeratorToAssignModeration(PEOPLE,self.profile,preferModProfiles=[self.profiles[2],self.profiles[4]])
        self.assertNotEqual(mod3,self.profile)
        self.assertTrue([self.profiles[2],self.profiles[4]].__contains__(mod3))
        
    
    def test_requestModerationForObject(self):
        moderation = requestModerationForObject(self.project,PROJECTS)
        self.assertIsInstance(moderation,Moderation)
        moderation.status = Code.REJECTED
        moderation.save()
        self.assertFalse(requestModerationForObject(self.project,PROJECTS))
        self.assertIsInstance(requestModerationForObject(self.project,PROJECTS,reassignIfRejected=True),Moderation)
        
