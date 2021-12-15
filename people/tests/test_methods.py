from main.strings import Code
from django.test import TestCase, tag
from main.tests.utils import getRandomStr
from main.env import BOTMAIL
from people.methods import *
from .utils import getTestBio, getTestEmail, getTestFName, getTestLName, getTestName, getTestPassword


@tag(Code.Test.METHOD, APPNAME)
class PeopleMethodsTest(TestCase):
    @classmethod
    def setUpTestData(self) -> None:
        self.bot, _ = User.objects.get_or_create(email=BOTMAIL, defaults=dict(
            first_name='knottersbot', email=BOTMAIL, password=getTestPassword()))
        self.user = User.objects.create_user(
            email=getTestEmail(), password=getTestPassword(), first_name=getTestName())
        self.profile = Profile.objects.get(user=self.user)
        return super().setUpTestData()

    def test_convertToFLname(self):
        firstname = getTestFName()
        lastname = getTestLName()
        fname, lname = convertToFLname(firstname)
        self.assertEqual(lname, str())
        self.assertEqual(fname, firstname)
        fname, lname = convertToFLname(f"{firstname} {lastname}")
        self.assertEqual(lname, lastname)
        self.assertEqual(fname, firstname)
        midname = getTestLName()
        fname, lname = convertToFLname(f"{firstname} {midname} {lastname}")
        self.assertTrue(f"{midname} {lastname}".__contains__(lname))
        self.assertNotEqual(lname, f"{midname} {lastname}")
        self.assertEqual(fname, firstname)
        midname = getTestName()
        fname, lname = convertToFLname(
            f"{firstname} {midname} {getTestLName()} {getTestLName()} {getTestLName()}")
        self.assertFalse(len(f"{fname} {lname}") > 70)
        self.assertEqual(fname, firstname)

    def test_filterBio(self):
        self.assertIsInstance(filterBio(getTestBio()+getTestBio()), str)
        self.assertFalse(len(filterBio(getTestBio()+getTestBio())) > 300)

    def test_getProfileSectionData(self):
        defdata = dict(self=True, person=self.user)
        self.assertFalse(getProfileSectionData(
            getRandomStr(), self.profile, self.user))
        self.assertDictEqual(getProfileSectionData(
            profileString.OVERVIEW, self.profile, self.user), defdata)
        self.assertIsInstance(getProfileSectionData(
            profileString.PROJECTS, self.profile, self.user), dict)
        self.assertDictEqual(getProfileSectionData(
            profileString.CONTRIBUTION, self.profile, self.user), defdata)
        self.assertDictEqual(getProfileSectionData(
            profileString.ACTIVITY, self.profile, self.user), defdata)
        self.assertDictEqual(getProfileSectionData(
            profileString.MODERATION, self.profile, self.user), defdata)

    def test_settingSectionData(self):
        defdata = dict()
        self.assertDictEqual(getSettingSectionData(
            profileString.Setting.ACCOUNT, self.user, self.user), defdata)
        self.assertDictEqual(getSettingSectionData(profileString.Setting.PREFERENCE, self.user, self.user), {
                             **defdata, f"{Code.SETTING}": ProfileSetting.objects.get(profile=self.profile)})

    def test_isPictureDeleteable(self):
        self.assertFalse(isPictureDeletable(self.profile.picture))

    def test_isPictureSocialImage(self):
        self.assertFalse(isPictureSocialImage(self.profile.picture))

    def test_getUsernameFromGHSocial(self):
        self.assertIsNone(getUsernameFromGHSocial(None))

    def test_migrateUserAssets(self):
        self.assertTrue(migrateUserAssets(self.user, self.user))
