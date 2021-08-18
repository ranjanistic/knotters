"""
Tests for models & signal receivers of people subapplication.
"""

from django.test import TestCase, tag
from django.core.exceptions import ObjectDoesNotExist
from allauth.account.models import EmailAddress
from people.apps import APPNAME
from people.models import *
from .utils import TEST_DP, TEST_GHID, TEST_NAME, TEST_EMAIL, TEST_PASSWORD, getTestEmails, getTestNames, getTestPasswords, getTestTopics


@tag(Code.Test.MODEL, APPNAME)
class UserTest(TestCase):

    def test_setting_creation_fail(self):
        with self.assertRaises(ObjectDoesNotExist):
            settings = ProfileSetting.objects.create()
            self.assertIsNone(settings.profile)

    def test_profile_creation_fail(self):
        with self.assertRaises(AttributeError):
            Profile.objects.create(githubID=TEST_GHID)

    def test_superuser_creation_fail(self):
        with self.assertRaises(TypeError):
            User.objects.create_superuser(password=TEST_PASSWORD)
        with self.assertRaises(TypeError):
            User.objects.create_superuser(
                email=TEST_EMAIL, password=TEST_PASSWORD)

    def test_user_creation_fail(self):
        with self.assertRaises(ValueError):
            User.objects.create_user(
                password=TEST_PASSWORD, email=None, first_name=TEST_NAME)
        with self.assertRaises(TypeError):
            User.objects.create_user(
                email=TEST_EMAIL, password=TEST_PASSWORD)

    def test_user_creation_pass(self):
        user = User.objects.create_user(
            email=TEST_EMAIL, password=TEST_PASSWORD, first_name=TEST_NAME)
        profile = Profile.objects.get(user=user)
        settings = ProfileSetting.objects.get(profile=profile)

    def test_superuser_creation_pass(self):
        user = User.objects.create_superuser(
            email=TEST_EMAIL, password=TEST_PASSWORD, first_name=TEST_NAME)
        profile = Profile.objects.get(user=user)
        ProfileSetting.objects.get(profile=profile)

    def test_user_deletion(self):
        user = User.objects.create_user(
            email=TEST_EMAIL, password=TEST_PASSWORD, first_name=TEST_NAME)
        user.delete()
        profile = Profile.objects.get(id=user.profile.id)
        self.assertIsNone(profile.user)
        self.assertIsNone(profile.githubID)
        self.assertFalse(profile.is_moderator)
        self.assertTrue(profile.to_be_zombie)
        self.assertTrue(profile.is_zombie)
        self.assertFalse(profile.is_active)
        self.assertTrue(str(profile.getDP()).endswith(defaultImagePath()))
        self.assertEqual(profile.getFName(), Code.ZOMBIE)
        self.assertEqual(profile.getName(), Code.ZOMBIE)
        self.assertEqual(profile.getEmail(), Code.ZOMBIEMAIL)


@tag(Code.Test.MODEL, APPNAME)
class UserAttributeTest(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.user = User.objects.create_user(
            email=TEST_EMAIL, password=TEST_PASSWORD, first_name=TEST_NAME)
        cls.profile = Profile.objects.get(user=cls.user)
        cls.setting = ProfileSetting.objects.get(profile=cls.profile)
        cls.emailaddress = EmailAddress.objects.create(
            user=cls.user, email=cls.user.email)

    def test_user_methods(self):
        self.assertEqual(self.user.__str__(), self.user.email)
        self.assertEqual(self.user.getID(), self.user.id.hex)
        self.assertFalse(self.user.has_perm(perm=None))
        self.assertTrue(self.user.has_module_perms(app_label=APPNAME))
        self.assertEqual(self.user.getName(), TEST_NAME)
        self.assertEqual(self.user.getName(), self.user.first_name)
        self.user.last_name = TEST_NAME
        self.user.save()
        self.assertEqual(self.user.getName(),
                         f"{self.user.first_name} {self.user.last_name}")
        self.assertTrue(self.user.getLink().endswith(self.user.getID()))

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


@tag(Code.Test.MODEL, APPNAME)
class ProfileAttributeTest(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.user = User.objects.create_user(
            email=TEST_EMAIL, password=TEST_PASSWORD, first_name=TEST_NAME)
        cls.profile = Profile.objects.get(user=cls.user)
        cls.setting = ProfileSetting.objects.get(profile=cls.profile)
        cls.emailaddress = EmailAddress.objects.create(
            user=cls.user, email=cls.user.email, verified=True)

    def test_profile_methods(self):
        self.assertEqual(self.profile.getID(), self.profile.id.hex)
        self.assertEqual(self.profile.__str__(), self.profile.getEmail())
        self.assertEqual(self.profile.getUserID(), self.user.getID())
        self.assertEqual(self.profile.getUserID(), self.profile.user.getID())
        self.assertTrue(str(self.profile.getDP()).endswith(defaultImagePath()))
        self.assertEquals(self.profile.getFName(), self.user.first_name)
        self.assertEquals(self.profile.getEmail(), self.user.email)
        self.assertFalse(self.profile.isRemoteDp())
        self.assertEqual(self.profile.getBio(), '')
        self.assertEqual(self.profile.getSubtitle(), '')
        self.assertEqual(self.profile.getGhUrl(), '')
        self.assertTrue(self.profile.getLink().endswith(
            self.profile.getUserID()))
        self.profile.githubID = TEST_GHID
        self.profile.save()
        self.assertTrue(self.profile.getLink().endswith(self.profile.githubID))
        self.profile.is_zombie = True
        self.assertTrue(self.profile.getLink().endswith(self.profile.getID()))
        self.profile.is_zombie = False
        self.assertTrue(self.profile.getSuccessorInviteLink().endswith(
            self.profile.getUserID()))
        self.assertTrue(profileImagePath(
            self.profile, TEST_DP).__contains__(self.profile.getID()))
        self.profile.picture = profileImagePath(self.profile, TEST_DP)
        self.profile.save()
        self.profile.picture = defaultImagePath()
        self.profile.save()

    def test_profile_settings_methods(self):
        self.assertEqual(self.setting.__str__(), self.profile.getID())
        self.assertFalse(self.setting.savePreferencesLink().endswith(
            self.profile.getUserID()))


@tag(Code.Test.MODEL, APPNAME)
class ProfileM2MTest(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.user = User.objects.create_user(
            email=TEST_EMAIL, password=TEST_PASSWORD, first_name=TEST_NAME)
        cls.profile = Profile.objects.get(user=cls.user)
        cls.setting = ProfileSetting.objects.get(profile=cls.profile)
        cls.emailaddress = EmailAddress.objects.create(
            user=cls.user, email=cls.user.email, verified=True)

    def test_profile_reporters(self):
        ruser = User.objects.create_user(
            email=getTestEmails()[0], password=getTestPasswords()[0], first_name=getTestNames()[0])
        reporter = Profile.objects.get(user=ruser)
        self.profile.reporters.add(reporter)
        report = ProfileReport.objects.get(
            profile=self.profile, reporter=reporter)
        report.delete()
        self.assertFalse(self.profile.isReporter(reporter))
        ProfileReport.objects.create(profile=reporter, reporter=self.profile)
        prof = Profile.objects.get(user=ruser, reporters=self.profile)
        self.assertTrue(prof.isReporter(self.profile))

    def test_profile_topics(self):
        topicnames = getTestTopics(3)
        topics = []
        for name in topicnames:
            topics.append(Topic(name=name))
        Topic.objects.bulk_create(topics)
        topic = Topic.objects.get(name=topicnames[0])
        self.profile.topics.add(topic)
        proftopic = ProfileTopic.objects.get(profile=self.profile, topic=topic)
        proftopic.delete()
        ProfileTopic.objects.create(profile=self.profile, topic=topic)
        Profile.objects.get(user=self.user, topics=topic)


@tag(Code.Test.MODEL, APPNAME)
class TopicTest(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.topicnames = getTestTopics(3)
        topics = []
        for name in cls.topicnames:
            topics.append(Topic(name=name))
        Topic.objects.bulk_create(topics)
        cls.topics = Topic.objects.filter()

    def test_topic_methods(self):
        self.assertEqual(self.topics.first().__str__(),
                         self.topics.first().name)
        self.assertEqual(self.topics.first().getID(),
                         self.topics.first().id.hex)
