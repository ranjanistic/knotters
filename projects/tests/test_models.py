from django.test import TestCase, tag
from django.core.exceptions import ObjectDoesNotExist
from people.models import User, Profile
from people.tests.utils import TEST_NAME, TEST_PASSWORD, TEST_EMAIL
from projects.models import *
from .utils import TEST_PROJ_NAME,TEST_PROJ_REPO


@tag(Code.Test.MODEL, APPNAME)
class ProjectTest(TestCase):

    def test_project_create_invalid(self):
        with self.assertRaises(ObjectDoesNotExist):
            Project.objects.create(name=TEST_PROJ_NAME)

    def test_project_create_valid(self):
        user = User.objects.create_user(first_name=TEST_NAME, password=TEST_PASSWORD, email=TEST_EMAIL)
        creator = Profile.objects.get(user=user)
        prevxp = creator.xp
        proj = Project.objects.create(name=TEST_PROJ_NAME, creator=creator, reponame=TEST_PROJ_REPO)
        self.assertTrue(proj.creator.xp > prevxp)
