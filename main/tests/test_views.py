from django.db.models.query import QuerySet
from django.http.response import HttpResponseBadRequest
from django.test import TestCase, Client, tag
import json
from main.env import PUBNAME, BOTMAIL, SITE, VERSION
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseNotFound
from main.strings import Code, Template, setPathParams, url, template, COMPETE, PEOPLE, PROJECTS, DIVISIONS
from projects.models import LegalDoc
from moderation.models import LocalStorage
from auth2.tests.utils import getTestEmail, getTestName, getTestPassword
from .utils import root, docroot, authroot, getRandomStr, getLegalName, getLegalPseudonym, getLegalContent
from compete.methods import *


@tag(Code.Test.VIEW,Code.Test.REST)
class TestViews(TestCase):
    @classmethod
    def setUpTestData(self) -> None:
        self.legaldoc = LegalDoc.objects.create(
            name=getLegalName(), pseudonym=getLegalPseudonym(), content=getLegalContent())
        self.client = Client()
        self.bot, _ = User.objects.get_or_create(email=BOTMAIL, defaults=dict(
            first_name='knottersbot', email=BOTMAIL, password=getTestPassword()))
        return super().setUpTestData()

    def test_offline(self):
        resp = self.client.get(follow=True, path=root(url.OFFLINE))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.index)
        self.assertTemplateUsed(resp, template.offline)

    @tag('ss')
    def test_index(self):
        resp = self.client.get(follow=True, path=root())
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.index)
        self.assertEqual(
            resp.context['SERVICE_WORKER'], f'/{url.SERVICE_WORKER}')
        self.assertEqual(resp.context['MANIFESTURL'], f'/{url.MANIFEST}')
        self.assertEqual(resp.context['APPNAME'], PUBNAME)
        self.assertEqual(resp.context['CONTACTMAIL'], BOTMAIL)
        self.assertIsNotNone(resp.context['DESCRIPTION'])
        self.assertEqual(resp.context['SITE'], SITE)
        self.assertEqual(resp.context['VERSION'], VERSION)
        subapps = dict()
        for div in DIVISIONS:
            subapps[div] = div
        self.assertDictEqual(resp.context['SUBAPPS'], subapps)
        self.assertEqual(resp.context['SUBAPPSLIST'], DIVISIONS)
        # self.assertEqual(resp.context['knotbot'], self.bot.profile)

    def test_redirector(self):
        resp = self.client.get(path=root(url.redirector(to=root(url.OFFLINE))))
        self.assertEqual(resp.status_code, HttpResponseRedirect.status_code)
        self.assertRedirects(resp, root(url.OFFLINE))
        uri = 'https://github.com'
        resp = self.client.get(follow=True, path=root(url.redirector(to=uri)))
        self.assertTemplateUsed(resp, template.index)
        self.assertTemplateUsed(resp, template.forward)
        self.assertEqual(resp.context['next'], uri)

    def test_onboarding(self):
        resp = self.client.get(follow=True, path=root(url.ON_BOARDING))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.index)
        self.assertTemplateUsed(resp, template.auth.login)

    def test_docIndex(self):
        resp = self.client.get(follow=True, path=root(url.DOCS))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.index)
        self.assertTemplateUsed(resp, template.docs.index)
        # self.assertEqual(resp.context['docs'], LegalDoc.objects.all())

    def test_docs(self):
        resp = self.client.get(follow=True, path=docroot(
            url.docs.type(getRandomStr())))
        self.assertEqual(resp.status_code, HttpResponseNotFound.status_code)
        resp = self.client.get(follow=True, path=docroot(
            url.docs.type(self.legaldoc.pseudonym)))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.index)
        self.assertTemplateUsed(resp, template.docs.doc)
        self.assertEqual(resp.context['doc'], self.legaldoc)

    def test_landing(self):
        resp = self.client.get(follow=True, path=root(url.LANDING))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.index)
        self.assertTemplateUsed(resp, template.landing)

    @tag(Code.Test.STATIC)
    def test_robots(self):
        resp = self.client.get(follow=True, path=root(url.ROBOTS_TXT))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertEqual(resp['content-type'], Code.TEXT_PLAIN)
        self.assertTemplateUsed(resp, template.ROBOTS_TXT)
        self.assertIsInstance(resp.context['suspended'],QuerySet)
        self.assertFalse(resp.context['ISBETA'])

    @tag(Code.Test.STATIC)
    def test_manifest(self):
        resp = self.client.get(follow=True, path=root(url.MANIFEST))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertEqual(resp['content-type'], Code.APPLICATION_JSON)
        self.assertTemplateUsed(resp, template.MANIFEST_JSON)
        self.assertIsInstance(resp.context['icons'], list)
        self.assertTrue(len(resp.context['icons']) > 0)

    @tag(Code.Test.STATIC)
    def test_strings(self):
        resp = self.client.get(follow=True, path=root(setPathParams(url.SCRIPTS,template.script.STRINGS)))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertEqual(resp['content-type'], Code.APPLICATION_JS)
        self.assertTemplateUsed(resp, template.script.STRINGS)

    @tag(Code.Test.STATIC)
    def test_constants(self):
        resp = self.client.get(follow=True, path=root(setPathParams(url.SCRIPTS,template.script.CONSTANTS)))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertEqual(resp['content-type'], Code.APPLICATION_JS)
        self.assertTemplateUsed(resp, template.script.CONSTANTS)

    @tag(Code.Test.STATIC)
    def test_service_worker(self):
        resp = self.client.get(follow=True, path=root(url.SERVICE_WORKER))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertEqual(resp['content-type'], Code.APPLICATION_JS)
        self.assertTemplateUsed(resp, template.SW_JS)
        self.assertEqual(resp.context['OFFLINE'], f"/{url.OFFLINE}")
        store = LocalStorage.objects.get(key=Code.SWASSETS)
        self.assertEqual(json.loads(
            resp.context['assets']), json.loads(store.value))

    @tag('browse')
    def test_browser(self):
        resp = self.client.get(
            follow=True, path=root(url.browser(getRandomStr())))
        self.assertEqual(resp.status_code, HttpResponseBadRequest.status_code)


@tag(Code.Test.VIEW,Code.Test.REST)
class TestViewsAuth(TestCase):
    @classmethod
    def setUpTestData(self) -> None:
        self.client = Client()
        self.bot, _ = User.objects.get_or_create(email=BOTMAIL, defaults=dict(
            first_name='knottersbot', email=BOTMAIL, password=getTestPassword()))
        return super().setUpTestData()

    def test_signup(self):
        resp = self.client.get(follow=True, path=authroot(url.auth.SIGNUP))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.index)
        self.assertTemplateUsed(resp, template.auth.signup)

    def test_login(self):
        resp = self.client.get(follow=True, path=authroot(url.auth.LOGIN))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.index)
        self.assertTemplateUsed(resp, template.auth.login)

    def test_logout(self):
        resp = self.client.get(path=authroot(url.auth.LOGOUT))
        self.assertEqual(resp.status_code, HttpResponseRedirect.status_code)

    def test_signup_post(self):
        client = Client()
        resp = client.post(follow=True, path=authroot(url.auth.SIGNUP))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.index)
        self.assertTemplateUsed(resp, template.auth.signup)
        self.assertFalse(resp.context['user'].is_authenticated)

        resp = client.post(follow=True, path=authroot(url.auth.SIGNUP), data=dict(
            first_name=str(),
            email=str(),
            password=str(),
        ))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.index)
        self.assertTemplateUsed(resp, template.auth.signup)
        self.assertFalse(resp.context['user'].is_authenticated)

        resp = client.post(follow=True, path=authroot(url.auth.SIGNUP), data=dict(
            email=getTestEmail(),
            first_name=getTestName(),
            password1=getTestPassword()
        ))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.index)

    def test_login_post(self):
        client = Client()
        email = getTestEmail()
        password = getTestPassword()
        resp = client.post(follow=True, path=authroot(url.auth.SIGNUP), data=dict(
            email=email,
            first_name=getTestName(),
            password1=password
        ))
        self.assertEqual(resp.status_code, HttpResponse.status_code)

        resp = client.post(follow=True, path=authroot(url.auth.LOGOUT))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertFalse(resp.context['user'].is_authenticated)

        resp = client.post(follow=True, path=authroot(url.auth.LOGIN))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertFalse(resp.context['user'].is_authenticated)
        resp = client.post(follow=True, path=authroot(url.auth.LOGOUT))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertFalse(resp.context['user'].is_authenticated)

        resp = client.post(follow=True, path=authroot(url.auth.LOGIN), data=dict(
            login=str(),
            password=str(),
        ))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertFalse(resp.context['user'].is_authenticated)

        resp = client.post(follow=True, path=authroot(url.auth.LOGOUT))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertFalse(resp.context['user'].is_authenticated)

        resp = client.post(follow=True, path=authroot(url.auth.LOGIN), data=dict(
            login=email,
            password=getRandomStr(),
        ))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertFalse(resp.context['user'].is_authenticated)

        resp = client.post(follow=True, path=authroot(url.auth.LOGIN), data=dict(
            login=email,
            password=password,
        ))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        # self.assertTrue(resp.context['user'].is_authenticated)

    def test_logout_post(self):
        client = Client()
        email = getTestEmail()
        password = getTestPassword()
        resp = client.post(follow=True, path=authroot(url.auth.SIGNUP), data=dict(
            email=email,
            first_name=getTestName(),
            password1=password
        ))
        self.assertEqual(resp.status_code, HttpResponse.status_code)

        resp = client.post(follow=True, path=authroot(url.auth.LOGOUT))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertFalse(resp.context['user'].is_authenticated)

        resp = client.post(follow=True, path=authroot(url.auth.LOGIN), data=dict(
            login=email,
            password=password,
        ))
        # self.assertTrue(resp.context['user'].is_authenticated)
        resp = client.post(follow=True, path=authroot(url.auth.LOGOUT))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertFalse(resp.context['user'].is_authenticated)
