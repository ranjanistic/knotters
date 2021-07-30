from main.strings import Code
from django.test import TestCase, tag
from people.methods import *
from .utils import TEST_BIO, TEST_EMAIL, TEST_FNAME, TEST_LNAME, TEST_NAME, TEST_PASSWORD


@tag(Code.Test.METHOD,APPNAME)
class PeopleMethodsTest(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.user = User.objects.create_user(
                email=TEST_EMAIL, password=TEST_PASSWORD, first_name=TEST_NAME)
        cls.profile = Profile.objects.get(user=cls.user)
        return super().setUpTestData()

    def test_convertToFLname(self):
        fname, lname = convertToFLname(TEST_FNAME)
        self.assertEqual(lname,str())
        self.assertEqual(fname,TEST_FNAME)
        fname, lname = convertToFLname(f"{TEST_FNAME} {TEST_LNAME}")
        self.assertEqual(lname,TEST_LNAME)
        self.assertEqual(fname,TEST_FNAME)
        fname, lname = convertToFLname(f"{TEST_FNAME} {TEST_LNAME} Test")
        self.assertEqual(lname,f"{TEST_LNAME} Test")
        self.assertEqual(fname,TEST_FNAME)
        fname, lname = convertToFLname(f"{TEST_FNAME} {TEST_LNAME} {TEST_LNAME}")
        self.assertFalse(len(f"{fname} {lname}") > 70)
        self.assertEqual(fname,TEST_FNAME)


    def test_filterBio(self):
        self.assertIsInstance(filterBio(TEST_BIO+TEST_BIO),str)
        self.assertFalse(len(filterBio(TEST_BIO+TEST_BIO))>120)

    def test_getProfileSectionData(self):
        defdata = dict(self=True,person=self.user)
        self.assertFalse(getProfileSectionData("abcd", self.profile,self.user))
        self.assertDictEqual(getProfileSectionData(profileString.OVERVIEW, self.profile,self.user),defdata)
        self.assertIsInstance(getProfileSectionData(profileString.PROJECTS, self.profile,self.user), dict)
        self.assertDictEqual(getProfileSectionData(profileString.CONTRIBUTION, self.profile,self.user),defdata)
        self.assertDictEqual(getProfileSectionData(profileString.ACTIVITY, self.profile,self.user),defdata)
        self.assertDictEqual(getProfileSectionData(profileString.MODERATION, self.profile,self.user),defdata)

    def test_settingSectionData(self):
        defdata = dict()
        self.assertDictEqual(getSettingSectionData(profileString.Setting.ACCOUNT, self.user,self.user),defdata)
        self.assertDictEqual(getSettingSectionData(profileString.Setting.PREFERENCE, self.user,self.user),{**defdata, f"{Code.SETTING}":ProfileSetting.objects.get(profile=self.profile)})

    def test_isPictureDeleteable(self):
        self.assertFalse(isPictureDeletable(self.profile.picture))
    
    def test_isPictureSocialImage(self):
        self.assertFalse(isPictureSocialImage(self.profile.picture))

    def test_getUsernameFromGHSocial(self):
        self.assertIsNone(getUsernameFromGHSocial(None))

    def test_migrateUserAssets(self):
        self.assertTrue(migrateUserAssets(self.user,self.user))