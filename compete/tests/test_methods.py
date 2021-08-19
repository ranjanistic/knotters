from main.strings import Code
from django.test import TestCase, tag
from people.models import Profile
from people.tests.utils import getTestEmail, getTestName, getTestPassword
from main.tests.utils import getRandomStr
from .utils import getCompTitle
from compete.methods import *


@tag(Code.Test.METHOD, APPNAME)
class CompeteMethodsTest(TestCase):
    @classmethod
    def setUpTestData(self) -> None:
        self.comp = Competition.objects.create(title=getCompTitle())
        self.user = User.objects.create_user(email=getTestEmail(
        ), password=getTestPassword(), first_name=getTestName())
        self.profile = Profile.objects.get(user=self.user)
        return super().setUpTestData()

    def test_competition_section_data(self):
        self.assertIsNone(getCompetitionSectionData(
            getRandomStr(), self.comp, self.user))
        self.assertDictEqual(getCompetitionSectionData(
            Compete.OVERVIEW, self.comp, self.user), dict(compete=self.comp))
        self.assertDictEqual(getCompetitionSectionData(
            Compete.TASK, self.comp, self.user), dict(compete=self.comp))
        self.assertDictEqual(getCompetitionSectionData(
            Compete.GUIDELINES, self.comp, self.user), dict(compete=self.comp))
        self.assertDictEqual(getCompetitionSectionData(
            Compete.SUBMISSION, self.comp, self.user), dict(compete=self.comp, submission=None))
        self.assertDictEqual(getCompetitionSectionData(
            Compete.RESULT, self.comp, self.user), dict(compete=self.comp, results=None))
