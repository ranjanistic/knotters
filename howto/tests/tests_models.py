from django.test import TestCase, tag
from allauth.account.models import EmailAddress
from django.core.exceptions import ObjectDoesNotExist
from django.db.utils import DatabaseError
from auth2.tests.utils import (getTestEmail, getTestGHID, getTestName,
                               getTestPassword)
from howto.models import Article, Section, ArticleUserRating, ArticleAdmirer, sectionMediaPath
from howto.views import section
from management.models import Management
from main.strings import Action, Code, Message, template, url
from main.tests.utils import getRandomFloat, getRandomStr
from people.models import Profile, Topic, User
from main.env import BOTMAIL
from howto.apps import APPNAME
from people.tests.utils import getTestTopicsInst
from .utils import *

@tag(Code.Test.MODEL, APPNAME)
class ArticleTest(TestCase):
    @classmethod
    def setUpTestData(self) -> None:
        self.bot, _ = User.objects.get_or_create(email=BOTMAIL, defaults=dict(
            first_name='knottersbot', email=BOTMAIL, password=getTestPassword()))
        self.user = User.objects.create_user(
            email=getTestEmail(), password=getTestPassword(), first_name=getTestName())
        self.profile = Profile.objects.get(user=self.user)
        self.management_user: User = User.objects.create_user(
            email=getTestEmail(), password=getTestPassword(), first_name=getTestName())
        self.management_profile: Profile = Profile.objects.get(
            user=self.management_user)
        self.management_profile.convertToManagement()
        return super().setUpTestData()


    def test_create_article_invalid(self):
        with self.assertRaises(DatabaseError):
            Article.objects.create()
        with self.assertRaises(DatabaseError):
            Article.objects.create(heading=getArticleHeading(), subheading=getArticleSubHeading())


    def test_create_article_valid(self):
        article = Article.objects.create(author=self.management_profile)
        self.assertTrue(article.is_draft)
        self.assertTrue(self.management_profile.articles.filter(id=article.get_id).exists())

        
@tag(Code.Test.MODEL, APPNAME)
class ArticleAttributeTest(TestCase):
    @classmethod
    def setUpTestData(self) -> None:
        self.bot, _ = User.objects.get_or_create(email=BOTMAIL, defaults=dict(
            first_name='knottersbot', email=BOTMAIL, password=getTestPassword()))
        self.user = User.objects.create_user(
            email=getTestEmail(), password=getTestPassword(), first_name=getTestName())
        self.profile = Profile.objects.get(user=self.user)
        self.management_user: User = User.objects.create_user(
            email=getTestEmail(), password=getTestPassword(), first_name=getTestName())
        self.management_profile: Profile = Profile.objects.get(
            user=self.management_user)
        self.management_profile.convertToManagement()
        self.article: Article = Article.objects.create(heading=getArticleHeading(
        ), subheading=getArticleSubHeading(), author=self.management_profile)
        return super().setUpTestData()


    @tag('article_methods')
    def test_article_methods(self):
        self.assertEqual(self.article.__str__(), self.article.nickname if self.article.nickname else self.article.id)

        self.assertFalse(Article.canCreateArticle(self.profile))
        self.assertTrue(Article.canCreateArticle(self.management_profile))
        
        self.article.admirers.add(self.profile)
        self.assertTrue(self.article.isAdmirer(self.profile))
        self.assertFalse(self.article.isAdmirer(self.management_profile))
        self.assertTrue(self.profile in self.article.get_admirers())
        self.assertEqual(self.article.total_admirers(), 1)

        topics = Topic.objects.bulk_create(getTestTopicsInst(2))
        for topic in topics:
            self.article.topics.add(topic)
        self.assertEqual(topics, list(self.article.getTopics()))
        self.assertEqual(self.article.totalTopics(), 2)

        tags = Tag.objects.bulk_create(getTestTagsInst(4))
        for tag in tags:
            self.article.tags.add(tag)
        self.assertEqual(tags, list(self.article.getTags()))
        self.assertEqual(self.article.totalTags(), 4)

        self.assertTrue(self.article.isEditable())

        score = getRandomFloat(1.0, 10.0)
        ArticleUserRating.objects.create(article=self.article, profile=self.profile, score=score)
        self.assertTrue(self.article.is_rated_by(self.profile))
        self.assertFalse(self.article.is_rated_by(self.management_profile))
        self.assertEqual(self.article.total_ratings(), 1)
        self.assertEqual(self.article.get_avg_rating(), round(score/2, 1))
        self.assertEqual(self.article.rating_by_user(self.profile), score)
        self.assertEqual(self.article.rating_by_user(self.management_profile), 0)

        self.assertEqual(self.article.getImage(), self.article.author.get_dp)
        section: Section = Section.objects.create(article=self.article, image=getTestImage())
        self.assertEqual(section.image.url, self.article.getImage())
        self.assertFalse(self.article.getVideo())
        section: Section = Section.objects.create(article=self.article, video=getTestVideo())
        self.assertEqual(section.video.url, self.article.getVideo())


@tag(Code.Test.MODEL, APPNAME)
class SectionTest(TestCase):
    @classmethod
    def setUpTestData(self) -> None:
        self.bot, _ = User.objects.get_or_create(email=BOTMAIL, defaults=dict(
            first_name='knottersbot', email=BOTMAIL, password=getTestPassword()))
        self.email = getTestEmail()
        self.ghID = getTestGHID()
        self.password = getTestPassword()
        self.user = User.objects.create_user(
            email=self.email, password=self.password, first_name=getTestName())
        self.profile = Profile.objects.get(user=self.user)
        self.m_email = getTestEmail()
        self.m_password = getTestPassword()
        self.management_user: User = User.objects.create_user(
            email=self.m_email, password=self.m_password, first_name=getTestName())
        self.management_profile: Profile = Profile.objects.get(
            user=self.management_user)
        self.management_profile.convertToManagement()
        self.article: Article = Article.objects.create(heading=getArticleHeading(
        ), subheading=getArticleSubHeading(), author=self.management_profile)
        return super().setUpTestData()

    
    def test_create_section_invalid(self):
        with self.assertRaises(ObjectDoesNotExist):
            Section.objects.create()
        with self.assertRaises(ObjectDoesNotExist):
            Section.objects.create(subheading=getTestSubhHeading(), paragraph=getTestParagraph())


    def test_create_section_valid(self):
        section = Section.objects.create(article=self.article, subheading=getTestSubhHeading(), paragraph=getTestParagraph())
        self.assertTrue(self.article.sections.filter(id=section.get_id).exists())
    

@tag(Code.Test.MODEL, APPNAME)
class SectionAttributeTest(TestCase):
    @classmethod
    def setUpTestData(self) -> None:
        self.bot, _ = User.objects.get_or_create(email=BOTMAIL, defaults=dict(
            first_name='knottersbot', email=BOTMAIL, password=getTestPassword()))
        self.user = User.objects.create_user(
            email=getTestEmail(), password=getTestPassword(), first_name=getTestName())
        self.profile = Profile.objects.get(user=self.user)
        self.management_user: User = User.objects.create_user(
            email=getTestEmail(), password=getTestPassword(), first_name=getTestName())
        self.management_profile: Profile = Profile.objects.get(
            user=self.management_user)
        self.management_profile.convertToManagement()
        self.article: Article = Article.objects.create(heading=getArticleHeading(
        ), subheading=getArticleSubHeading(), author=self.management_profile)
        self.section = Section.objects.create(article=self.article, subheading=getTestSubhHeading(), paragraph=getTestParagraph())
        return super().setUpTestData()

    
    @tag('section_methods')
    def test_section_methods(self):
        self.assertTrue(sectionMediaPath(
            self.section, getTestImage()).__contains__(self.section.get_id))

        self.section.image = getTestImage()
        self.section.video = getTestVideo()
        self.section.save()
        self.assertEqual(self.section.image.url, self.section.get_image())
        self.assertEqual(self.section.video.url, self.section.get_video())