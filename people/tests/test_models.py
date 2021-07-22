from django.test import TestCase, tag
from allauth.account.models import EmailAddress
from people.models import *


@tag('model1')
class UserTest(TestCase):

    def test_setting_creation_fail(self):
        settings = ProfileSetting.objects.create()
        self.assertIsNone(settings.profile)

    def test_profile_creation_fail(self):
        with self.assertRaises(Exception):
            profile = Profile.objects.create(githubID="testing")

    def test_user_creation_fail(self):
        with self.assertRaises(Exception):
            user = User.objects.create_user(
                email="testing@knotters.org", password='12345@testing')

    def test_user_creation_pass(self):
        user = User.objects.create_user(
            email="testing@knotters.org", password='12345@testing', first_name="Testing")
        profile = Profile.objects.get(user=user)
        settings = ProfileSetting.objects.get(profile=profile)


@tag('model')
class UserAttributeTest(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.user = User.objects.create_user(
            email="testing@knotters.org", password='12345@testing', first_name="Testing")
        cls.profile = Profile.objects.get(user=cls.user)
        cls.setting = ProfileSetting.objects.get(profile=cls.profile)
        cls.emailaddress = EmailAddress.objects.create(
            user=cls.user, email=cls.user.email)

    def test_user_profile_defaults(self):
        self.assertFalse(self.profile.is_moderator)
        self.assertFalse(self.profile.is_verified)
        self.assertFalse(self.profile.suspended)
        self.assertTrue(self.profile.is_active)
        self.assertFalse(self.profile.is_zombie)
        self.assertFalse(self.profile.to_be_zombie)
        self.assertFalse(self.profile.successor_confirmed)
        self.assertIsNone(self.profile.successor)
        self.assertIsNone(self.profile.githubID)
        self.assertFalse(isPictureDeletable(self.profile.picture))

    def test_profile_setting_defaults(self):
        self.assertTrue(self.setting.newsletter)
        self.assertTrue(self.setting.recommendations)
        self.assertTrue(self.setting.competitions)
        self.assertTrue(self.setting.privatemail)


    def test_email_verification(self):
        self.assertFalse(self.emailaddress.verified)
        EmailAddress.objects.filter(user=self.user).update(verified=True)
        EmailAddress.objects.get(user=self.user, verified=True)

    def test_profile_methods(self):
        self.assertTrue(
            str(self.profile.getDP()).__contains__(defaultImagePath()))
        self.assertEquals(self.profile.getFName(), self.user.first_name)
        self.assertEquals(self.profile.getEmail(), self.user.email)
        self.assertFalse(self.profile.isRemoteDp())


@tag('model')
class ProfileM2MTest(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.user = User.objects.create_user(
            email="testing@knotters.org", password='12345@testing', first_name="Testing")
        cls.profile = Profile.objects.get(user=cls.user)
        cls.setting = ProfileSetting.objects.get(profile=cls.profile)
        cls.emailaddress = EmailAddress.objects.create(
            user=cls.user, email=cls.user.email, verified=True)

    def test_profile_reporters(self):
        ruser = User.objects.create_user(
            email="testing2@knotters.org", password='12345@testing', first_name="Testing 2")
        reporter = Profile.objects.get(user=ruser)
        self.profile.reporters.add(reporter)
        report = ProfileReport.objects.get(
            profile=self.profile, reporter=reporter)
        report.delete()
        ProfileReport.objects.create(profile=reporter, reporter=self.profile)
        Profile.objects.get(user=ruser, reporters=self.profile)

    def test_profile_topics(self):
        Topic.objects.bulk_create(
            [Topic(name="Test topic"), Topic(name="Test topic2")])
        topic = Topic.objects.get(name="Test topic")
        self.profile.topics.add(topic)
        proftopic = ProfileTopic.objects.get(profile=self.profile, topic=topic)
        proftopic.delete()
        ProfileTopic.objects.create(profile=self.profile, topic=topic)
        Profile.objects.get(user=self.user, topics=topic)
