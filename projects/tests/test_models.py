from django.test import TestCase, tag
from django.db.utils import DatabaseError
from django.core.exceptions import ObjectDoesNotExist
from people.models import Topic, User, Profile
from main.env import BOTMAIL
from moderation.methods import requestModerationForObject
from people.tests.utils import getTestName, getTestPassword, getTestEmail, getTestTopicsInst, getTestUsersInst
from projects.models import *
from .utils import getLicDesc, getLicName, getProjCategory, getProjImage, getProjName, getProjRepo, getTag, getTestTagsInst


@tag(Code.Test.MODEL, APPNAME)
class ProjectTest(TestCase):
    @classmethod
    def setUpTestData(self) -> None:
        self.bot, _ = User.objects.get_or_create(email=BOTMAIL, defaults=dict(
            first_name='knottersbot', email=BOTMAIL, password=getTestPassword()))
        user = User.objects.create_user(
            first_name=getTestName(), password=getTestPassword(), email=getTestEmail())
        self.creator = Profile.objects.get(user=user)
        self.category = Category.objects.create(name=getProjCategory())
        self.license = License.objects.create(name=getLicName(), description=getLicDesc())

    def test_project_create_invalid(self):
        with self.assertRaises(ObjectDoesNotExist):
            Project.objects.create(name=getProjName(),reponame=getProjRepo(),)
        with self.assertRaises(ObjectDoesNotExist):
            Project.objects.create(name=getProjName(), reponame=getProjRepo(),creator=self.creator)
        with self.assertRaises(ObjectDoesNotExist):
            Project.objects.create(name=getProjName(),reponame=getProjRepo(), creator=self.creator,category=self.category)
        with self.assertRaises(AssertionError):
            Project.objects.create(name=getProjName(), creator=self.creator,category=self.category, license=self.license)

    def test_project_create_valid(self):
        prevxp = self.creator.xp
        proj = Project.objects.create(name=getProjName(), creator=self.creator, reponame=getProjRepo(),category=self.category, license=self.license)
        self.assertEqual(proj.status, Code.MODERATION)
        self.assertTrue(proj.creator.xp > prevxp)


@tag(Code.Test.MODEL, APPNAME)
class ProjectAttributeTest(TestCase):
    @classmethod
    def setUpTestData(self) -> None:
        self.bot, _ = User.objects.get_or_create(email=BOTMAIL, defaults=dict(
            first_name='knottersbot', email=BOTMAIL, password=getTestPassword()))
        user = User.objects.create_user(
            first_name=getTestName(), password=getTestPassword(), email=getTestEmail())
        self.creator = Profile.objects.get(user=user)
        self.category = Category.objects.create(name=getProjCategory())
        self.license = License.objects.create(name=getLicName(), description=getLicDesc())
        self.project = Project.objects.create(name=getProjName(), creator=self.creator, reponame=getProjRepo(),category=self.category, license=self.license)

    def test_project_default_methods(self):
        self.assertEqual(self.project.__str__(), self.project.name)
        self.assertEqual(self.project.getID(), self.project.id.hex)
        self.assertTrue(projectImagePath(
            self.project, getProjImage()).__contains__(self.project.getID()))
        self.assertTrue(self.project.getDP().endswith(str(self.project.image)))
        self.assertTrue(self.project.underModeration())
        self.assertFalse(self.project.rejected())
        self.project.status = Code.APPROVED
        self.project.save()
        self.assertTrue(self.project.isApproved())
        self.assertEqual(self.project.isApproved(), self.project.isLive())
        self.assertTrue(self.project.getRepoLink().endswith(
            self.project.reponame))
        self.assertTrue(self.project.getLink().endswith(self.project.reponame))
        self.assertEqual(self.project.moderationRetriesLeft(), 0)
        self.assertFalse(self.project.canRetryModeration())

    def test_project_modified_methods(self):
        self.project.image = projectImagePath(self.project, getProjImage())
        self.project.save()
        self.project.image = defaultImagePath()
        self.project.save()
        users = User.objects.bulk_create(getTestUsersInst())
        Profile.objects.create(user=users[0], is_moderator=True)
        requestModerationForObject(self.project, APPNAME)
        self.assertEqual(self.project.getLink(), self.project.getModLink())
        self.assertTrue(self.project.moderationRetriesLeft() > 0)
        self.assertTrue(self.project.canRetryModeration())


@tag(Code.Test.MODEL, APPNAME)
class TagTest(TestCase):
    @classmethod
    def setUpTestData(self) -> None:
        self.bot, _ = User.objects.get_or_create(email=BOTMAIL, defaults=dict(
            first_name='knottersbot', email=BOTMAIL, password=getTestPassword()))
        user = User.objects.create_user(
            first_name=getTestName(), password=getTestPassword(), email=getTestEmail())
        self.creator = Profile.objects.get(user=user)
        self.category = Category.objects.create(name=getProjCategory())
        self.license = License.objects.create(name=getLicName(), description=getLicDesc())
        self.project = Project.objects.create(name=getProjName(), creator=self.creator, reponame=getProjRepo(),category=self.category, license=self.license)
        return super().setUpTestData()

    def test_tag_create(self):
        Tag.objects.create(name=getTag())

    def test_tag_assign_project(self):
        tags = Tag.objects.bulk_create(getTestTagsInst(4))
        for tag in tags:
            self.project.tags.add(tag)
        self.assertEqual(len(tags), ProjectTag.objects.filter(
            project=self.project, tag__in=tags).count())
        ProjectTag.objects.filter(project=self.project, tag__in=tags).delete()
        self.assertEqual(self.project.tags.count(), 0)
        projecttags = []
        for tag in tags:
            projecttags.append(
                ProjectTag(project=self.project, tag=tag)
            )
        ProjectTag.objects.bulk_create(projecttags)
        self.assertEqual(self.project.tags.count(), len(tags))
        with self.assertRaises(DatabaseError):
            ProjectTag.objects.create(project=self.project, tag=tags[0])


@tag(Code.Test.MODEL, APPNAME)
class TagAttributeTest(TestCase):
    @classmethod
    def setUpTestData(self) -> None:
        self.bot, _ = User.objects.get_or_create(email=BOTMAIL, defaults=dict(
            first_name='knottersbot', email=BOTMAIL, password=getTestPassword()))
        self.tag = Tag.objects.create(name=getTag())
        return super().setUpTestData()

    def test_category_methods(self):
        self.assertEqual(self.tag.__str__(), self.tag.name)


@tag(Code.Test.MODEL, APPNAME)
class CategoryTest(TestCase):
    @classmethod
    def setUpTestData(self) -> None:
        self.bot, _ = User.objects.get_or_create(email=BOTMAIL, defaults=dict(
            first_name='knottersbot', email=BOTMAIL, password=getTestPassword()))
        user = User.objects.create_user(
            first_name=getTestName(), password=getTestPassword(), email=getTestEmail())
        self.creator = Profile.objects.get(user=user)
        self.license = License.objects.create(name=getLicName(), description=getLicDesc())
        self.category = Category.objects.create(name=getProjCategory())
        return super().setUpTestData()

    def test_create_category(self):
        Category.objects.create(name=getProjCategory())

    def test_category_assign_project(self):
        category = Category.objects.create(name=getProjCategory())
        proj = Project.objects.create(name=getProjName(), creator=self.creator, reponame=getProjRepo(),category=category, license=self.license)
        self.assertEqual(proj.category.getID(), category.getID())

    @tag('cat')
    def test_category_assign_tags(self):
        category = Category.objects.create(name=getProjCategory())
        proj = Project.objects.create(name=getProjName(), creator=self.creator, reponame=getProjRepo(),category=category, license=self.license)
        tags = Tag.objects.bulk_create(getTestTagsInst(4))
        for tag in tags:
            proj.category.tags.add(tag)
        self.assertEqual(len(tags), CategoryTag.objects.filter(category=category,tag__in=tags).count())
        for tag in tags:
            category.tags.add(tag)
        self.assertEqual(len(tags), CategoryTag.objects.filter(
            category=category, tag__in=tags).count())
        with self.assertRaises(DatabaseError):
            CategoryTag.objects.create(category=category, tag=tags[0])


@tag(Code.Test.MODEL, APPNAME)
class CategoryAttributeTest(TestCase):
    @classmethod
    def setUpTestData(self) -> None:
        self.bot, _ = User.objects.get_or_create(email=BOTMAIL, defaults=dict(
            first_name='knottersbot', email=BOTMAIL, password=getTestPassword()))
        self.category = Category.objects.create(name=getProjCategory())
        return super().setUpTestData()

    def test_category_methods(self):
        self.assertEqual(self.category.__str__(), self.category.name)


@tag(Code.Test.MODEL, APPNAME)
class TopicTest(TestCase):
    @classmethod
    def setUpTestData(self) -> None:
        self.bot, _ = User.objects.get_or_create(email=BOTMAIL, defaults=dict(
            first_name='knottersbot', email=BOTMAIL, password=getTestPassword()))
        user = User.objects.create_user(
            first_name=getTestName(), password=getTestPassword(), email=getTestEmail())
        self.creator = Profile.objects.get(user=user)
        self.category = Category.objects.create(name=getProjCategory())
        self.license = License.objects.create(name=getLicName(), description=getLicDesc())
        self.project = Project.objects.create(name=getProjName(), creator=self.creator, reponame=getProjRepo(),category=self.category, license=self.license)
        return super().setUpTestData()

    def test_topic_assign_project(self):
        topics = Topic.objects.bulk_create(getTestTopicsInst(4))
        for topic in topics:
            self.project.topics.add(topic)
        self.assertEqual(len(topics), ProjectTopic.objects.filter(
            project=self.project, topic__in=topics).count())
        ProjectTopic.objects.filter(
            project=self.project, topic__in=topics).delete()
        self.assertEqual(self.project.topics.count(), 0)
        projecttags = []
        for topic in topics:
            projecttags.append(
                ProjectTopic(project=self.project, topic=topic)
            )
        ProjectTopic.objects.bulk_create(projecttags)
        self.assertEqual(self.project.topics.count(), len(topics))
        with self.assertRaises(DatabaseError):
            ProjectTopic.objects.create(project=self.project, topic=topics[0])
