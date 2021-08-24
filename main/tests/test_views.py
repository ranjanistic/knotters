from django.http.response import HttpResponseBadRequest
from django.test import TestCase, Client, tag
import json
from main.env import PUBNAME, BOTMAIL, SITE, VERSION
from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseNotFound
from main.strings import Code, url, template, COMPETE, PEOPLE, PROJECTS, DIVISIONS
from projects.models import LegalDoc
from moderation.models import LocalStorage
from people.tests.utils import getTestEmail, getTestName, getTestPassword
from .utils import root, docroot, authroot, getRandomStr, getLegalName, getLegalPseudonym, getLegalContent
from compete.methods import *


@tag(Code.Test.VIEW)
class TestViews(TestCase):
    @classmethod
    def setUpTestData(self) -> None:
        self.legaldoc = LegalDoc.objects.create(
            name=getLegalName(), pseudonym=getLegalPseudonym(), content=getLegalContent())
        self.client = Client()
        return super().setUpTestData()

    def test_offline(self):
        resp = self.client.get(root(url.OFFLINE))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.index)
        self.assertTemplateUsed(resp, template.offline)

    def test_index(self):
        resp = self.client.get(root())
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.index)
        self.assertEqual(resp.context['SERVICE_WORKER'], f'/{url.SERVICE_WORKER}')
        self.assertEqual(resp.context['MANIFESTURL'], f'/{url.MANIFEST}')
        self.assertEqual(resp.context['APPNAME'],PUBNAME)
        self.assertEqual(resp.context['CONTACTMAIL'],BOTMAIL)
        self.assertIsNotNone(resp.context['DESCRIPTION'],)
        self.assertEqual(resp.context['SITE'],SITE)
        self.assertEqual(resp.context['VERSION'],VERSION)
        subapps = dict()
        for div in DIVISIONS:
            subapps[div] = div
        self.assertDictEqual(resp.context['SUBAPPS'],subapps)
        self.assertEqual(resp.context['SUBAPPSLIST'], DIVISIONS)
        self.assertEqual(resp.context['ICON'],f"{settings.STATIC_URL}graphics/self/icon.svg")

    def test_redirector(self):
        resp = self.client.get(root(url.redirector(to=root(url.OFFLINE))))
        self.assertEqual(resp.status_code, HttpResponseRedirect.status_code)
        self.assertRedirects(resp, root(url.OFFLINE))
        uri = 'https://github.com'
        resp = self.client.get(root(url.redirector(to=uri)))
        self.assertTemplateUsed(resp, template.index)
        self.assertTemplateUsed(resp, template.forward)
        self.assertEqual(resp.context['next'], uri)

    def test_docIndex(self):
        resp = self.client.get(root(url.DOCS))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.index)
        self.assertTemplateUsed(resp, template.docs.index)
        # self.assertEqual(resp.context['docs'], LegalDoc.objects.all())

    def test_docs(self):
        resp = self.client.get(docroot(url.docs.type(getRandomStr())))
        self.assertEqual(resp.status_code, HttpResponseNotFound.status_code)
        resp = self.client.get(docroot(url.docs.type(self.legaldoc.pseudonym)))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.index)
        self.assertTemplateUsed(resp, template.docs.doc)
        self.assertEqual(resp.context['doc'],self.legaldoc)

    def test_landing(self):
        resp = self.client.get(root(url.LANDING))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.index)
        self.assertTemplateUsed(resp, template.landing)

    def test_applanding(self):
        resp = self.client.get(root(url.applanding(getRandomStr())))
        self.assertEqual(resp.status_code, HttpResponseNotFound.status_code)

        resp = self.client.get(root(url.applanding(COMPETE)))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.index)
        self.assertTemplateUsed(resp, template.compete.landing)

        resp = self.client.get(root(url.applanding(PEOPLE)))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.index)
        self.assertTemplateUsed(resp, template.people.landing)

        resp = self.client.get(root(url.applanding(PROJECTS)))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.index)
        self.assertTemplateUsed(resp, template.projects.landing)

    def test_robots(self):
        resp = self.client.get(root(url.ROBOTS_TXT))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertEqual(resp['content-type'],Code.TEXT_PLAIN)
        self.assertTemplateUsed(resp, template.ROBOTS_TXT)
        self.assertEqual(resp.context['static'],settings.STATIC_URL)
        self.assertEqual(resp.context['media'],settings.MEDIA_URL)

    
    def test_manifest(self):
        resp = self.client.get(root(url.MANIFEST))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertEqual(resp['content-type'],Code.APPLICATION_JSON)
        self.assertTemplateUsed(resp, template.MANIFEST_JSON)
        self.assertIsInstance(resp.context['icons'],list)
        self.assertTrue(len(resp.context['icons'])>0)

    def test_service_worker(self):
        resp = self.client.get(root(url.SERVICE_WORKER))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertEqual(resp['content-type'],Code.APPLICATION_JS)
        self.assertTemplateUsed(resp, template.SW_JS)
        self.assertEqual(resp.context['OFFLINE'],f"/{url.OFFLINE}")
        store = LocalStorage.objects.get(key=Code.SWASSETS)
        self.assertEqual(json.loads(resp.context['assets']),json.loads(store.value))



@tag(Code.Test.VIEW)
class TestViewsAuth(TestCase):
    @classmethod
    def setUpTestData(self) -> None:
        self.client = Client()
        return super().setUpTestData()

    def test_signup(self):
        resp = self.client.get(authroot(url.auth.SIGNUP))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.index)
        self.assertTemplateUsed(resp, template.auth.signup)

    def test_login(self):
        resp = self.client.get(authroot(url.auth.LOGIN))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.index)
        self.assertTemplateUsed(resp, template.auth.login)

    def test_logout(self):
        resp = self.client.get(authroot(url.auth.LOGOUT))
        self.assertEqual(resp.status_code, HttpResponseRedirect.status_code)

    def test_signup_post(self):
        client = Client()
        resp = client.post(authroot(url.auth.SIGNUP),follow=True)
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.index)
        self.assertTemplateUsed(resp, template.auth.signup)
        self.assertFalse(resp.context['user'].is_authenticated)

        resp = client.post(authroot(url.auth.SIGNUP), dict(
            first_name=str(),
            email=str(),
            password=str(),
        ), follow=True)
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.index)
        self.assertTemplateUsed(resp, template.auth.signup)
        self.assertFalse(resp.context['user'].is_authenticated)

        resp = client.post(authroot(url.auth.SIGNUP), dict(
            email=getTestEmail(),
            first_name=getTestName(),
            password1=getTestPassword()
        ), follow=True)
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.index)

    def test_login_post(self):
        client = Client()
        email = getTestEmail()
        password = getTestPassword()
        resp = client.post(authroot(url.auth.SIGNUP), dict(
            email=email,
            first_name=getTestName(),
            password1=password
        ), follow=True)
        self.assertEqual(resp.status_code, HttpResponse.status_code)

        resp = client.post(authroot(url.auth.LOGOUT), follow=True)
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertFalse(resp.context['user'].is_authenticated)

        resp = client.post(authroot(url.auth.LOGIN), follow=True)
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertFalse(resp.context['user'].is_authenticated)
        resp = client.post(authroot(url.auth.LOGOUT), follow=True)
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertFalse(resp.context['user'].is_authenticated)

        resp = client.post(authroot(url.auth.LOGIN), dict(
            login=str(),
            password=str(),
        ), follow=True)
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertFalse(resp.context['user'].is_authenticated)

        resp = client.post(authroot(url.auth.LOGOUT), follow=True)
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertFalse(resp.context['user'].is_authenticated)

        resp = client.post(authroot(url.auth.LOGIN), dict(
            login=email,
            password=getRandomStr(),
        ), follow=True)
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertFalse(resp.context['user'].is_authenticated)

        resp = client.post(authroot(url.auth.LOGIN), dict(
            login=email,
            password=password,
        ), follow=True)
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTrue(resp.context['user'].is_authenticated)

    def test_logout_post(self):
        client = Client()
        email = getTestEmail()
        password = getTestPassword()
        resp = client.post(authroot(url.auth.SIGNUP), dict(
            email=email,
            first_name=getTestName(),
            password1=password
        ), follow=True)
        self.assertEqual(resp.status_code, HttpResponse.status_code)

        resp = client.post(authroot(url.auth.LOGOUT), follow=True)
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertFalse(resp.context['user'].is_authenticated)

        resp = client.post(authroot(url.auth.LOGIN), dict(
            login=email,
            password=password,
        ), follow=True)
        self.assertTrue(resp.context['user'].is_authenticated)
        resp = client.post(authroot(url.auth.LOGOUT), follow=True)
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertFalse(resp.context['user'].is_authenticated)

    def test_browser(self):
        resp = self.client.get(root(url.browser(getRandomStr())),follow=True)
        self.assertEqual(resp.status_code, HttpResponseBadRequest.status_code)

