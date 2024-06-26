from uuid import uuid4
from auth2.tests.utils import getTestEmail, getTestName, getTestPassword
from django.http.response import (HttpResponse, HttpResponseNotFound,
                                  HttpResponseRedirect)
from django.test import TestCase, tag
from main.env import BOTMAIL
from main.strings import Code, Template, url
from main.tests.utils import authroot
from management.apps import APPNAME
from people.models import Profile, User
from django.test.client import Client

from .utils import root


@tag(Code.Test.VIEW, APPNAME)
class TestViews(TestCase):

    @classmethod
    def setUpTestData(self) -> None:
        self.bot, created = User.objects.get_or_create(email=BOTMAIL, defaults=dict(
            first_name='knottersbot', email=BOTMAIL, password=getTestPassword()))
        self.email = getTestEmail()
        self.password = getTestPassword()
        self.user = User.objects.create_user(
            email=self.email, password=self.password, first_name=getTestName())
        self.profile = Profile.objects.get(user=self.user)
        return
    
    def setUp(self) -> None:
        Profile.KNOTBOT()
        return super().setUp()

    def test_index(self) -> None:
        client = Client()
        response = client.get(path=root(appendslash=True))
        self.assertEqual(response.status_code,
                         HttpResponseRedirect.status_code)
        response = client.get(path=root(appendslash=True), follow=True)
        self.assertEqual(response.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(response, Template.auth.login)

    def test_competition(self) -> None:
        client = Client()
        response = client.get(root(url.management.COMPETITIONS))
        self.assertEqual(response.status_code,
                         HttpResponseRedirect.status_code)
        response = self.client.get(
            root(url.management.COMPETITIONS), follow=True)
        self.assertEqual(response.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(response, Template.auth.login)

    def test_competition_view(self):
        client = Client()
        response = client.get(
            root(url.management.COMPETITIONS), follow=True)
        self.assertEqual(response.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(response, Template.auth.login)
        response = client.post(authroot(url.auth.LOGIN), data=dict(
            login=self.email, password=self.password), follow=True)
        self.assertEqual(response.status_code, HttpResponse.status_code)
        self.assertTrue(response.context["user"].is_authenticated)
        response = client.get(
            root(url.management.competition(uuid4())), follow=True)
        self.assertEqual(response.status_code,
                         HttpResponseNotFound.status_code)

