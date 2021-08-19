from django.test import TestCase, Client, tag
from django.http import HttpResponse
from main.strings import Code, url, template
from people.tests.utils import getTestEmail, getTestName, getTestPassword
from people.models import Profile
from .utils import getCompTitle, root
from compete.methods import *


@tag(Code.Test.VIEW, APPNAME)
class TestViews(TestCase):
    @classmethod
    def setUpTestData(self) -> None:
        self.comp = Competition.objects.create(title=getCompTitle())
        self.user = User.objects.create_user(
            email=getTestEmail(), password=getTestPassword(), first_name=getTestName())
        self.profile = Profile.objects.get(user=self.user)
        self.client = Client()
        return super().setUpTestData()

    def test_index(self):
        response = self.client.get(root(appendslash=True))
        self.assertEqual(response.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(response, template.index)
        self.assertTemplateUsed(response, template.compete.index)

    def test_indexTab(self):
        response = self.client.get(
            root(url.compete.indexTab(tab=Compete.ACTIVE)))
        self.assertEqual(response.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(response, template.compete.active)

        response = self.client.get(
            root(url.compete.indexTab(tab=Compete.UPCOMING)))
        self.assertEqual(response.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(response, template.compete.upcoming)

        response = self.client.get(
            root(url.compete.indexTab(tab=Compete.HISTORY)))
        self.assertEqual(response.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(response, template.compete.history)
