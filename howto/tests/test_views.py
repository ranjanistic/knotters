from json import loads as json_loads
from django.test import TestCase, Client, tag
from django.http import HttpResponse, HttpResponseNotAllowed
from django.http.response import HttpResponseNotFound, HttpResponseRedirect, HttpResponseForbidden
from allauth.account.models import EmailAddress
from auth2.tests.utils import (getTestEmail, getTestGHID, getTestName,
                               getTestPassword)
from howto.models import Article, Section, ArticleUserRating
from management.models import Management
from main.strings import Action, Code, Message, template, url
from main.tests.utils import getRandomFloat
from people.models import Profile, Topic, User
from main.env import BOTMAIL
from howto.apps import APPNAME
from people.tests.utils import getTestTopicsInst
from .utils import (getArticleHeading, getArticleSubHeading, getTestImage, getTestParagraph, getTestSubhHeading,
                    getTestTags, getTestTagsInst, getTestVideo, root)


@tag(Code.Test.VIEW, APPNAME)
class TestViews(TestCase):
    @classmethod
    def setUpTestData(self) -> None:
        self.bot, _ = User.objects.get_or_create(email=BOTMAIL, defaults=dict(
            first_name='knottersbot', email=BOTMAIL, password=getTestPassword()))
        self.management: Management = Management.objects.create(
            profile=Profile.KNOTBOT())
        self.client = Client()
        self.email = getTestEmail()
        self.ghID = getTestGHID()
        self.password = getTestPassword()
        self.user = User.objects.create_user(
            email=self.email, password=self.password, first_name=getTestName())
        self.profile = Profile.objects.get(user=self.user)
        self.moduser: User = User.objects.create_user(
            email=getTestEmail(), password=self.password, first_name=getTestName())
        self.modprofile = Profile.objects.get(user=self.moduser)
        self.modprofile.is_moderator = True
        self.modprofile.save()
        self.m_email = getTestEmail()
        self.m_password = getTestPassword()
        self.management_user: User = User.objects.create_user(
            email=self.m_email, password=self.m_password, first_name=getTestName())
        self.management_profile: Profile = Profile.objects.get(
            user=self.management_user)
        self.management.people.add(self.management_profile)
        EmailAddress.objects.get_or_create(
            user=self.user, email=self.email, verified=True, primary=True)
        EmailAddress.objects.get_or_create(
            user=self.management_user, email=self.m_email, verified=True, primary=True)
        return super().setUpTestData()


    def test_index(self):
        client = Client()
        resp = client.get(path=root(''))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.index)
        self.assertTemplateUsed(resp, template.howto.index)


    def test_createArticle(self):
        client = Client()
        resp = client.get(path=root(url.howto.CREATE))
        self.assertEqual(resp.status_code, HttpResponseRedirect.status_code)
        resp = client.get(path=root(url.howto.CREATE), follow=True)
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.auth.login)

        client.login(email=self.email, password=self.password)
        resp = client.get(follow=True, path=root(url.howto.CREATE))
        self.assertEqual(resp.status_code, HttpResponseNotFound.status_code)
        client.logout()

        client.login(email=self.m_email, password=self.m_password)
        resp = client.get(follow=True, path=root(url.howto.CREATE))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTrue(Article.objects.filter(
            author=self.management_profile).exists())
        self.assertTemplateUsed(resp, template.index)
        self.assertTemplateUsed(resp, template.howto.index)
        self.assertTemplateUsed(resp, template.howto.articleEdit)


    def test_viewArticle(self):
        client = Client()
        article: Article = Article.objects.create(heading=getArticleHeading(
        ), subheading=getArticleSubHeading(), author=self.management_profile)
        published_article: Article = Article.objects.create(heading=getArticleHeading(
        ), subheading=getArticleSubHeading(), author=self.management_profile, is_draft=False)

        resp = client.get(path=root(url.howto.view(article.get_nickname)))
        self.assertEqual(resp.status_code, HttpResponseRedirect.status_code)
        resp = client.get(path=root(url.howto.view(
            article.get_nickname)), follow=True)
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.howto.index)

        resp = client.get(
            path=root(url.howto.view(published_article.get_nickname)))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.howto.article)

        client.login(email=self.m_email, password=self.m_password)
        resp = client.get(path=root(url.howto.view(article.get_nickname)))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.howto.article)
        resp = client.get(
            path=root(url.howto.view(published_article.get_nickname)))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.howto.article)


    def test_editArticle(self):
        client = Client()
        article: Article = Article.objects.create(heading=getArticleHeading(
        ), subheading=getArticleSubHeading(), author=self.management_profile)

        resp = client.get(path=root(url.howto.edit(article.get_nickname)))
        self.assertEqual(resp.status_code, HttpResponseRedirect.status_code)
        resp = client.get(path=root(url.howto.edit(
            article.get_nickname)), follow=True)
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.auth.login)

        client.login(email=self.email, password=self.password)
        resp = client.get(path=root(url.howto.edit(article.get_nickname)))
        self.assertEqual(resp.status_code, HttpResponseNotFound.status_code)
        client.logout()

        client.login(email=self.m_email, password=self.m_password)
        resp = client.get(path=root(url.howto.edit(article.get_nickname)))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.howto.articleEdit)


    def test_saveArticle(self):
        client = Client()
        article: Article = Article.objects.create(heading=getArticleHeading(
        ), subheading=getArticleSubHeading(), author=self.management_profile)

        client.login(email=self.email, password=self.password)
        resp = client.post(path=root(url.howto.save(article.get_nickname)), data=dict(
            heading=getArticleHeading(), subheading=getArticleSubHeading()), content_type=Code.APPLICATION_JSON)
        self.assertDictEqual(json_loads(
            resp.content.decode(Code.UTF_8)), dict(code=Code.NO, error=Message.ERROR_OCCURRED))
        client.logout()

        client.login(email=self.m_email, password=self.m_password)
        resp = client.post(path=root(url.howto.save(article.get_nickname)), data=dict(
            heading=getArticleHeading()), content_type=Code.APPLICATION_JSON)
        self.assertDictEqual(json_loads(
            resp.content.decode(Code.UTF_8)), dict(code=Code.NO, error=Message.ERROR_OCCURRED))
        resp = client.post(path=root(url.howto.save(article.get_nickname)), data=dict(
            heading=getArticleHeading(), subheading=getArticleSubHeading()), content_type=Code.APPLICATION_JSON)
        self.assertDictEqual(json_loads(
            resp.content.decode(Code.UTF_8)), dict(code=Code.OK, success=Message.ARTICLE_UPDATED))


    def test_publishArticle(self):
        client = Client()
        article: Article = Article.objects.create(heading=getArticleHeading(
        ), subheading=getArticleSubHeading(), author=self.management_profile)

        client.login(email=self.email, password=self.password)
        resp = client.post(path=root(url.howto.publish(article.get_id)), content_type=Code.APPLICATION_JSON)
        self.assertDictEqual(json_loads(
            resp.content.decode(Code.UTF_8)), dict(code=Code.NO, error=Message.ARTICLE_NOT_FOUND))
        article: Article = Article.objects.get(id=article.get_id)
        self.assertTrue(article.is_draft)
        client.logout()

        client.login(email=self.m_email, password=self.m_password)
        resp = client.post(path=root(url.howto.publish(article.get_id)), content_type=Code.APPLICATION_JSON)
        article: Article = Article.objects.get(id=article.get_id)
        self.assertDictEqual(json_loads(
            resp.content.decode(Code.UTF_8)), dict(code=Code.OK, nickname=article.get_nickname))
        self.assertFalse(article.is_draft)

    
    def test_deleteArticle(self):
        client= Client()
        article: Article = Article.objects.create(heading=getArticleHeading(
        ), subheading=getArticleSubHeading(), author=self.management_profile)

        client.login(email=self.email, password=self.password)
        resp = client.post(path=root(url.howto.delete(article.get_id)), data=dict(confirm = True), content_type=Code.APPLICATION_JSON)
        self.assertDictEqual(json_loads(
            resp.content.decode(Code.UTF_8)), dict(code=Code.NO, error=Message.INVALID_REQUEST))
        self.assertTrue(Article.objects.filter(id=article.get_id).exists())
        client.logout()

        client.login(email=self.m_email, password=self.m_password)
        resp = client.post(path=root(url.howto.delete(article.get_id)), content_type=Code.APPLICATION_JSON)
        self.assertDictEqual(json_loads(
            resp.content.decode(Code.UTF_8)), dict(code=Code.NO, error=Message.INVALID_REQUEST))
        self.assertTrue(Article.objects.filter(id=article.get_id).exists())
        resp = client.post(path=root(url.howto.delete(article.get_id)), data=dict(confirm=True),content_type=Code.APPLICATION_JSON)
        self.assertDictEqual(json_loads(
            resp.content.decode(Code.UTF_8)), dict(code=Code.OK))
        self.assertFalse(Article.objects.filter(id=article.get_id).exists())


    def test_section(self):
        client = Client()
        article: Article = Article.objects.create(heading=getArticleHeading(
        ), subheading=getArticleSubHeading(), author=self.management_profile)
        section: Section = Section.objects.create(article=article, subheading=getTestSubhHeading(),paragraph=getTestParagraph())

        client.login(email=self.email, password=self.password)
        resp = client.post(path=root(url.howto.section(article.get_id, Action.CREATE)), data=dict(paragraph=getTestParagraph()), content_type=Code.APPLICATION_JSON)
        self.assertDictEqual(json_loads(
            resp.content.decode(Code.UTF_8)), dict(code=Code.NO, error=Message.INVALID_REQUEST))
        resp = client.post(path=root(url.howto.section(article.get_id, Action.UPDATE)), data=dict(sectionid=section.get_id, paragraph=getTestParagraph()), content_type=Code.APPLICATION_JSON)
        self.assertDictEqual(json_loads(
            resp.content.decode(Code.UTF_8)), dict(code=Code.NO, error=Message.INVALID_REQUEST))
        resp = client.post(path=root(url.howto.section(article.get_id, Action.REMOVE)), data=dict(sectionid=section.get_id), content_type=Code.APPLICATION_JSON)
        self.assertDictEqual(json_loads(
            resp.content.decode(Code.UTF_8)), dict(code=Code.NO, error=Message.INVALID_REQUEST))
        client.logout()

        client.login(email=self.m_email, password=self.m_password)
        resp = client.post(path=root(url.howto.section(article.get_id, Action.CREATE)), content_type=Code.APPLICATION_JSON)
        self.assertDictEqual(json_loads(
            resp.content.decode(Code.UTF_8)), dict(code=Code.NO, error=Message.INVALID_REQUEST))

        subheading = getTestSubhHeading()
        paragraph = getTestParagraph()
        resp = client.post(path=root(url.howto.section(article.get_id, Action.CREATE)), data=dict(subheading=subheading, paragraph=paragraph), content_type=Code.APPLICATION_JSON)
        resp_data = json_loads(
            resp.content.decode(Code.UTF_8))
        code, sectionid = resp_data['code'], resp_data['sectionID']
        self.assertEqual(code, Code.OK)
        self.assertTrue(Section.objects.filter(id=sectionid, subheading=subheading, paragraph=paragraph).exists())

        resp = client.post(path=root(url.howto.section(article.get_id, Action.CREATE)), data=dict(paragraph=paragraph), content_type=Code.APPLICATION_JSON)
        resp_data = json_loads(
            resp.content.decode(Code.UTF_8))
        code, sectionid = resp_data['code'], resp_data['sectionID']
        self.assertEqual(code, Code.OK)
        self.assertTrue(Section.objects.filter(id=sectionid, subheading='Untitled Section', paragraph=paragraph).exists())

        new_subheading = getTestSubhHeading()
        new_paragraph = getTestParagraph() 
        resp = client.post(path=root(url.howto.section(article.get_id, Action.UPDATE)), content_type=Code.APPLICATION_JSON)
        self.assertDictEqual(json_loads(
            resp.content.decode(Code.UTF_8)), dict(code=Code.NO, error=Message.INVALID_REQUEST))
        resp = client.post(path=root(url.howto.section(article.get_id, Action.UPDATE)), data=dict(subheading=new_subheading), content_type=Code.APPLICATION_JSON)
        self.assertDictEqual(json_loads(
            resp.content.decode(Code.UTF_8)), dict(code=Code.NO, error=Message.INVALID_REQUEST))
        resp = client.post(path=root(url.howto.section(article.get_id, Action.UPDATE)), data=dict(sectionid=section.get_id, subheading=new_subheading), content_type=Code.APPLICATION_JSON)
        self.assertDictEqual(json_loads(
            resp.content.decode(Code.UTF_8)), dict(code=Code.OK, message=Message.SECTION_UPDATED))
        self.assertTrue(Section.objects.filter(id=section.get_id, subheading=new_subheading).exists())
        resp = client.post(path=root(url.howto.section(article.get_id, Action.UPDATE)), data=dict(sectionid=section.get_id, paragraph=new_paragraph), content_type=Code.APPLICATION_JSON)
        self.assertDictEqual(json_loads(
            resp.content.decode(Code.UTF_8)), dict(code=Code.OK, message=Message.SECTION_UPDATED))
        self.assertTrue(Section.objects.filter(id=section.get_id, paragraph=new_paragraph).exists())

        resp = client.post(path=root(url.howto.section(article.get_id, Action.REMOVE)), content_type=Code.APPLICATION_JSON)
        self.assertDictEqual(json_loads(
            resp.content.decode(Code.UTF_8)), dict(code=Code.NO, error=Message.INVALID_REQUEST))
        resp = client.post(path=root(url.howto.section(article.get_id, Action.REMOVE)), data=dict(sectionid=section.get_id), content_type=Code.APPLICATION_JSON)
        self.assertDictEqual(json_loads(
            resp.content.decode(Code.UTF_8)), dict(code=Code.OK, message=Message.SECTION_DELETED))
        self.assertFalse(Section.objects.filter(id=section.get_id).exists())


    def test_submitArticleRating(self):
        client = Client()
        article: Article = Article.objects.create(heading=getArticleHeading(
        ), subheading=getArticleSubHeading(), author=self.management_profile)

        client.login(email=self.email, password=self.password)
        resp = client.post(path=root(
            url.howto.rating(article.get_id)), content_type=Code.APPLICATION_JSON)
        self.assertDictEqual(json_loads(
            resp.content.decode(Code.UTF_8)), dict(code=Code.NO, error=Message.INVALID_REQUEST))
        
        resp = client.post(path=root(
            url.howto.rating(article.get_id)), data=dict(action=Action.CREATE ), content_type=Code.APPLICATION_JSON)
        self.assertDictEqual(json_loads(
            resp.content.decode(Code.UTF_8)), dict(code=Code.NO, error=Message.INVALID_REQUEST))
        
        score = getRandomFloat(11.0)
        resp = client.post(path=root(
            url.howto.rating(article.get_id)), data=dict(action =Action.CREATE , score=score), content_type=Code.APPLICATION_JSON)
        self.assertDictEqual(json_loads(
            resp.content.decode(Code.UTF_8)), dict(code=Code.NO, error=Message.INVALID_REQUEST))
        
        score = getRandomFloat(1.0,4.0)
        resp = client.post(path=root(
            url.howto.rating(article.get_id)), data=dict(action =Action.CREATE , score=score), content_type=Code.APPLICATION_JSON)
        self.assertDictEqual(json_loads(
            resp.content.decode(Code.UTF_8)), dict(code=Code.OK))
        self.assertTrue(ArticleUserRating.objects.filter(profile=self.profile, article=article, score=score).exists())
        
        score = getRandomFloat(4.0,10.0)
        resp = client.post(path=root(
            url.howto.rating(article.get_id)), data=dict(action =Action.CREATE , score=score), content_type=Code.APPLICATION_JSON)
        self.assertDictEqual(json_loads(
            resp.content.decode(Code.UTF_8)), dict(code=Code.OK))
        self.assertTrue(ArticleUserRating.objects.filter(profile=self.profile, article=article, score=score).exists())

