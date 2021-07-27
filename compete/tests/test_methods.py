from main.strings import Code
import os
from django.test import TestCase, tag, Client
from people.tests.utils import TEST_EMAIL, TEST_NAME, TEST_PASSWORD
from people.models import Profile
from compete.methods import *
from .utils import TEST_COMP_TITLE


@tag(Code.Test.METHOD, APPNAME)
class CompeteMethodsTest(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.comp = Competition.objects.create(title=TEST_COMP_TITLE)
        cls.user = User.objects.create_user(email=TEST_EMAIL, password=TEST_PASSWORD, first_name=TEST_NAME)
        cls.profile = Profile.objects.get(user=cls.user)
        return super().setUpTestData()

    def test_competition_section_data(self):
        self.assertIsNone(getCompetitionSectionData('abcd', self.comp, self.user))
        self.assertDictEqual(getCompetitionSectionData(Compete.OVERVIEW, self.comp, self.user), dict(compete=self.comp))
        self.assertDictEqual(getCompetitionSectionData(Compete.TASK, self.comp, self.user), dict(compete=self.comp))
        self.assertDictEqual(getCompetitionSectionData(Compete.GUIDELINES, self.comp, self.user), dict(compete=self.comp))
        self.assertDictEqual(getCompetitionSectionData(Compete.SUBMISSION, self.comp, self.user),dict(compete=self.comp,submission=None))
        self.assertDictEqual(getCompetitionSectionData(Compete.RESULT, self.comp, self.user),dict(compete=self.comp,results=None))
