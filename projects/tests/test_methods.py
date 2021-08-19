from people.tests.utils import getTestUsersInst
from main.strings import Code
from people.models import User
from django.test import TestCase, tag
from .utils import getProjName, getProjRepo, getProjCategory, getProjDesc, getTag, getLicName, getLicDesc, getTestTags
from projects.methods import *


@tag(Code.Test.METHOD, APPNAME)
class ProjectsMethodTest(TestCase):
    @classmethod
    def setUpTestData(self) -> None:
        users = User.objects.bulk_create(getTestUsersInst(2))
        self.creator = Profile.objects.create(user=users[0])
        self.mod = Profile.objects.create(user=users[1], is_moderator=True)
        self.license = License.objects.create(
            name=getLicName(), description=getLicDesc())
        return super().setUpTestData()

    def test_uniqueRepoName(self):
        self.assertTrue(uniqueRepoName(getProjRepo()))

    def test_addCategoryToDatabase(self):
        self.assertIsInstance(addCategoryToDatabase(
            getProjCategory()), Category)

    def test_uniqueTag(self):
        self.assertTrue(uniqueTag(getProjRepo()))

    def test_addTagToDatabase(self):
        self.assertIsInstance(addTagToDatabase(getTag()), Tag)

    def test_createProject(self):
        self.assertIsInstance(createProject(getProjName(), getProjCategory(), getProjRepo(), getProjDesc(), getTestTags(3), self.creator, self.license.getID()), Project)
        pass

    def test_setupApprovedProject(self):
        project = createProject(getProjName(), getProjCategory(), getProjRepo(), getProjDesc(), getTestTags(5), self.creator, self.license.getID())
        self.assertIsInstance(project, Project)
        self.assertFalse(setupApprovedProject(project, self.mod))
        project.status = Code.APPROVED
        project.save()
        self.assertTrue(setupApprovedProject(project, self.mod))
