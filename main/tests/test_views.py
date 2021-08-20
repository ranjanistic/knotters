from django.test import TestCase, Client, tag
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseNotFound
from main.strings import Code, url, template, COMPETE, PEOPLE, PROJECTS
from projects.models import LegalDoc
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

    def test_redirector(self):
        resp = self.client.get(root(url.redirector(to=root(url.OFFLINE))))
        self.assertEqual(resp.status_code, HttpResponseRedirect.status_code)
        self.assertRedirects(resp, root(url.OFFLINE))
        resp = self.client.get(root(url.redirector(to='https://github.com')))
        self.assertTemplateUsed(resp, template.index)
        self.assertTemplateUsed(resp, template.forward)

    def test_docIndex(self):
        resp = self.client.get(root(url.DOCS))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.index)
        self.assertTemplateUsed(resp, template.docs.index)

    def test_docs(self):
        resp = self.client.get(docroot(url.docs.type(getRandomStr())))
        self.assertEqual(resp.status_code, HttpResponseNotFound.status_code)
        resp = self.client.get(docroot(url.docs.type(self.legaldoc.pseudonym)))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.index)
        self.assertTemplateUsed(resp, template.docs.doc)

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
        self.assertTemplateUsed(resp, template.ROBOTS_TXT)

    def test_manifest(self):
        resp = self.client.get(root(url.MANIFEST))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.MANIFEST_JSON)

    def test_service_worker(self):
        resp = self.client.get(root(url.SERVICE_WORKER))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.SW_JS)


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
        self.client.logout()
        resp = self.client.post(authroot(url.auth.SIGNUP))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.index)
        self.assertTemplateUsed(resp, template.auth.signup)

        resp = self.client.post(authroot(url.auth.SIGNUP), dict(
            username=str(),
            email=str(),
            password=str(),
        ), follow=True)
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.index)
        self.assertTemplateUsed(resp, template.auth.signup)

        resp = self.client.post(authroot(url.auth.SIGNUP), dict(
            email=getTestEmail(),
            first_name=getTestName(),
            password1=getTestPassword()
        ), follow=True)
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.index)
        self.assertIsNotNone(self.client.session._SessionBase__session_key)

    def test_login_post(self):
        email = getTestEmail()
        password = getTestPassword()
        resp = self.client.post(authroot(url.auth.SIGNUP), dict(
            email=email,
            first_name=getTestName(),
            password1=password
        ), follow=True)
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.index)
        resp = self.client.post(authroot(url.auth.LOGOUT))

        resp = self.client.get(authroot(url.auth.LOGIN), follow=True)
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.index)
        self.assertTemplateUsed(resp, template.auth.login)
        resp = self.client.post(authroot(url.auth.LOGOUT))

        resp = self.client.post(authroot(url.auth.LOGIN), dict(
            login=str(),
            password=str(),
        ))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.index)
        self.assertTemplateUsed(resp, template.auth.login)
        resp = self.client.post(authroot(url.auth.LOGOUT))
        resp = self.client.post(authroot(url.auth.LOGIN), dict(
            login=email,
            password=getRandomStr(),
        ))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.index)
        self.assertTemplateUsed(resp, template.auth.login)

        resp = self.client.post(authroot(url.auth.LOGIN), dict(
            login=email,
            password=password,
        ), follow=True)
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.index)
        self.assertIsNotNone(self.client.session._SessionBase__session_key)
        self.client.logout()
        self.assertTrue(self.client.login(email=email, password=password))
        self.assertIsNotNone(self.client.session._SessionBase__session_key)

    def test_logout_post(self):
        email = getTestEmail()
        password = getTestPassword()
        resp = self.client.post(authroot(url.auth.SIGNUP), dict(
            email=email,
            first_name=getTestName(),
            password1=password
        ), follow=True)
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.index)
        self.assertIsNotNone(self.client.session._SessionBase__session_key)

        resp = self.client.post(authroot(url.auth.LOGOUT))
        self.assertEqual(resp.status_code, HttpResponseRedirect.status_code)

        self.client.login(email=email, password=password)
        self.assertIsNotNone(self.client.session._SessionBase__session_key)
        resp = self.client.post(authroot(url.auth.LOGOUT))
        self.assertIsNone(self.client.session._SessionBase__session_key)
