from main.strings import Code
from people.models import User
from django.test import TestCase, tag
from main.env import BOTMAIL
from auth2.tests.utils import getTestPassword
from people.tests.utils import getTestUsersInst
from .utils import getProjName, getProjRepo, getProjCategory, getProjDesc, getTag, getLicName, getLicDesc
from projects.methods import *


@tag(Code.Test.METHOD, APPNAME)
class ProjectsMethodTest(TestCase):
    @classmethod
    def setUpTestData(self) -> None:
        self.bot, _ = User.objects.get_or_create(email=BOTMAIL, defaults=dict(
            first_name='knottersbot', email=BOTMAIL, password=getTestPassword()))
        users = User.objects.bulk_create(getTestUsersInst(2))
        self.creator = Profile.objects.create(user=users[0])
        self.mod = Profile.objects.create(user=users[1], is_moderator=True)
        self.license = License.objects.create(
            name=getLicName(), description=getLicDesc(),creator=self.bot.profile, public=True)
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

    @tag('create')
    def test_createProject(self):
        self.assertIsInstance(createProject(getProjName(), getProjCategory(), getProjRepo(), getProjDesc(), self.creator, self.license.getID()), Project)
        pass

    def test_setupApprovedProject(self):
        project = createProject(getProjName(), getProjCategory(), getProjRepo(), getProjDesc(), self.creator, self.license.getID())
        self.assertIsInstance(project, Project)
        self.assertFalse(setupApprovedProject(project, self.mod))
        project.status = Code.APPROVED
        project.save()
        self.assertTrue(setupApprovedProject(project, self.mod))
