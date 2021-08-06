from people.tests.utils import getTestUsersInst
from main.strings import Code
from people.models import User
from django.test import TestCase, tag
from projects.methods import *
from .utils import TEST_PROJ_NAME, TEST_PROJ_REPO, TEST_CATEGORY, TEST_DESC, TEST_TAG,TEST_LIC_NAME, TEST_LIC_DESC, getTestTags

@tag(Code.Test.METHOD, APPNAME)
class ProjectsMethodTest(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        users = User.objects.bulk_create(getTestUsersInst(2))
        cls.creator = Profile.objects.create(user=users[0])
        cls.mod = Profile.objects.create(user=users[1],is_moderator=True)
        cls.license = License.objects.create(name=TEST_LIC_NAME, description=TEST_LIC_DESC)
        return super().setUpTestData()

    def test_uniqueRepoName(self):
        self.assertTrue(uniqueRepoName(TEST_PROJ_REPO))

    def test_addCategoryToDatabase(self):
        self.assertIsInstance(addCategoryToDatabase(TEST_CATEGORY),Category)

    def test_uniqueTag(self):
        self.assertTrue(uniqueTag(TEST_PROJ_REPO))

    def test_addTagToDatabase(self):
        self.assertIsInstance(addTagToDatabase(TEST_TAG),Tag)
        
    def test_createProject(self):
        self.assertIsInstance(createProject(TEST_PROJ_NAME, TEST_CATEGORY, TEST_PROJ_REPO, TEST_DESC, getTestTags(3), self.creator,self.license.getID()), Project)
        pass

    def test_setupApprovedProject(self):
        project = createProject(TEST_PROJ_NAME, TEST_CATEGORY, TEST_PROJ_REPO, TEST_DESC, getTestTags(3), self.creator, self.license.getID())
        self.assertIsInstance(project,Project)
        self.assertFalse(setupApprovedProject(project,self.mod))
        project.status = Code.APPROVED
        project.save()
        self.assertTrue(setupApprovedProject(project,self.mod))
