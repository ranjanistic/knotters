"""
Tests for models & signal receivers of people subapplication.
"""

from allauth.account.models import EmailAddress
from auth2.tests.utils import (getTestEmail, getTestGHID, getTestName,
                               getTestPassword)
from django.core.exceptions import ObjectDoesNotExist
from django.db.utils import IntegrityError
from django.test import TestCase, tag
from main.env import BOTMAIL
from people.apps import APPNAME
from people.models import *

from .utils import getTestDP, getTestTopics


@tag(Code.Test.MODEL, APPNAME)
class UserTest(TestCase):

    def test_setting_creation_fail(self):
        with self.assertRaises((ObjectDoesNotExist, IntegrityError)):
            settings = ProfileSetting.objects.create()
            self.assertIsNone(settings.profile)

    def test_profile_creation_fail(self):
        with self.assertRaises(AttributeError):
            Profile.objects.create(githubID=getTestGHID())

    def test_superuser_creation_fail(self):
        with self.assertRaises(TypeError):
            User.objects.create_superuser(password=getTestPassword())
        with self.assertRaises(TypeError):
            User.objects.create_superuser(
                email=getTestEmail(), password=getTestPassword())

    def test_user_creation_fail(self):
        with self.assertRaises(ValueError):
            User.objects.create_user(
                password=getTestPassword(), email=None, first_name=getTestName())
        with self.assertRaises(TypeError):
            User.objects.create_user(
                email=getTestEmail(), password=getTestPassword())

    def test_user_creation_pass(self):
        user = User.objects.create_user(
            email=getTestEmail(), password=getTestPassword(), first_name=getTestName())
        profile = Profile.objects.get(user=user)
        settings = ProfileSetting.objects.get(profile=profile)

    def test_superuser_creation_pass(self):
        user = User.objects.create_superuser(
            email=getTestEmail(), password=getTestPassword(), first_name=getTestName())
        profile = Profile.objects.get(user=user)
        ProfileSetting.objects.get(profile=profile)

    def test_user_deletion(self):
        user = User.objects.create_user(
            email=getTestEmail(), password=getTestPassword(), first_name=getTestName())
        user.delete()
        profile = Profile.objects.get(id=user.profile.id)
        self.assertIsNone(profile.user)
        self.assertIsNone(profile.githubID)
        self.assertFalse(profile.is_moderator)
        self.assertTrue(profile.to_be_zombie)
        self.assertTrue(profile.is_zombie)
        self.assertFalse(profile.is_active)
        self.assertFalse(isPictureDeletable(profile.picture))
        self.assertEqual(profile.getFName(), Code.ZOMBIE)
        self.assertEqual(profile.getName(), Code.ZOMBIE)
        self.assertEqual(profile.getEmail(), Code.ZOMBIEMAIL)


@tag(Code.Test.MODEL, APPNAME)
class UserAttributeTest(TestCase):
    @classmethod
    def setUpTestData(self) -> None:
        self.bot, _ = User.objects.get_or_create(email=BOTMAIL, defaults=dict(
            first_name='knottersbot', email=BOTMAIL, password=getTestPassword()))
        self.name = getTestName()
        self.user = User.objects.create_user(
            email=getTestEmail(), password=getTestPassword(), first_name=self.name)
        self.profile = Profile.objects.get(user=self.user)
        self.setting = ProfileSetting.objects.get(profile=self.profile)
        self.emailaddress = EmailAddress.objects.create(
            user=self.user, email=self.user.email)
        
    def setUp(self) -> None:
        Profile.KNOTBOT()
        return super().setUp()

    def test_user_methods(self):
        self.assertEqual(self.user.__str__(), self.user.email)
        self.assertEqual(self.user.getID(), self.user.id.hex)
        self.assertFalse(self.user.has_perm(perm=None))
        self.assertTrue(self.user.has_module_perms(app_label=APPNAME))
        self.assertEqual(self.user.getName(), self.name)
        self.assertEqual(self.user.getName(), self.user.first_name)
        self.user.last_name = getTestName()
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
        self.assertTrue(self.setting.privatemail)

    def test_email_verification(self):
        self.assertFalse(self.emailaddress.verified)
        EmailAddress.objects.filter(user=self.user).update(verified=True)
        EmailAddress.objects.get(user=self.user, verified=True)


@tag(Code.Test.MODEL, APPNAME)
class ProfileAttributeTest(TestCase):
    @classmethod
    def setUpTestData(self) -> None:
        self.bot, _ = User.objects.get_or_create(email=BOTMAIL, defaults=dict(
            first_name='knottersbot', email=BOTMAIL, password=getTestPassword()))
        self.user = User.objects.create_user(
            email=getTestEmail(), password=getTestPassword(), first_name=getTestName())
        self.profile = Profile.objects.get(user=self.user)
        self.setting = ProfileSetting.objects.get(profile=self.profile)
        self.emailaddress = EmailAddress.objects.create(
            user=self.user, email=self.user.email, verified=True)
        
    def setUp(self) -> None:
        Profile.KNOTBOT()
        return super().setUp()

    @tag('testprofilemethods')
    def test_profile_methods(self):
        self.assertEqual(self.profile.getID(), self.profile.id.hex)
        self.assertEqual(self.profile.__str__(), self.profile.getEmail())
        self.assertEqual(self.profile.getUserID(), self.user.getID())
        self.assertEqual(self.profile.getUserID(), self.profile.user.getID())

        self.assertFalse(isPictureDeletable(self.profile.picture))
        self.assertEquals(self.profile.getFName(), self.user.first_name)
        self.assertEquals(self.profile.getEmail(), self.user.email)
        self.assertFalse(self.profile.isRemoteDp())
        self.assertEqual(self.profile.getBio(), str())
        self.assertEqual(self.profile.getSubtitle(), str())
        self.assertTrue(self.profile.getLink().endswith(
            self.profile.get_nickname()))
        self.profile.is_zombie = True
        self.assertTrue(self.profile.getLink().endswith(self.profile.getID()))
        self.profile.is_zombie = False
        self.assertTrue(self.profile.getSuccessorInviteLink().endswith(
            self.profile.getUserID()))
        self.assertTrue(profileImagePath(
            self.profile, getTestDP()).__contains__(self.profile.getUserID()))
        self.profile.picture = profileImagePath(self.profile, getTestDP())
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
    def setUpTestData(self) -> None:
        self.bot, _ = User.objects.get_or_create(email=BOTMAIL, defaults=dict(
            first_name='knottersbot', email=BOTMAIL, password=getTestPassword()))
        self.user = User.objects.create_user(
            email=getTestEmail(), password=getTestPassword(), first_name=getTestName())
        self.profile = Profile.objects.get(user=self.user)
        self.setting = ProfileSetting.objects.get(profile=self.profile)
        self.emailaddress = EmailAddress.objects.create(
            user=self.user, email=self.user.email, verified=True)
        
    def setUp(self) -> None:
        Profile.KNOTBOT()
        return super().setUp()

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
    def setUpTestData(self) -> None:
        self.bot, _ = User.objects.get_or_create(email=BOTMAIL, defaults=dict(
            first_name='knottersbot', email=BOTMAIL, password=getTestPassword()))
        self.topicnames = getTestTopics(3)
        topics = []
        for name in self.topicnames:
            topics.append(Topic(name=name))
        Topic.objects.bulk_create(topics)
        self.topics = Topic.objects.filter()
    
    def setUp(self) -> None:
        Profile.KNOTBOT()
        return super().setUp()

    def test_topic_methods(self):
        self.assertEqual(self.topics.first().__str__(),
                         self.topics.first().name)
        self.assertEqual(self.topics.first().getID(),
                         self.topics.first().id.hex)
