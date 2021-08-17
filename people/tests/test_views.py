from django.test import TestCase, Client, tag
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseNotFound
from main.strings import Code, url, template
from main.tests.utils import authroot
from people.apps import APPNAME
from people.methods import profileString
from people.models import Profile, User
from .utils import TEST_EMAIL, TEST_NAME, TEST_PASSWORD, root

@tag(Code.Test.VIEW, APPNAME, 'aa')
class TestViews(TestCase):
    def setUp(self) -> None:
        self.client = Client()
        self.client.post(authroot(url.auth.SIGNUP), dict(
            email=TEST_EMAIL,
            first_name=TEST_NAME,
            password1=TEST_PASSWORD
        ),follow=True)
        self.client.login(email=TEST_EMAIL,password=TEST_PASSWORD)
        
    def test_index(self):
        resp = self.client.get(root(url.INDEX))
        self.assertEqual(resp.status_code,HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.index)
        self.assertTemplateUsed(resp, template.people.index)

    def test_profile(self):
        profile = Profile.objects.filter().first()
        resp = self.client.get(root(url.people.profile(userID=profile.getUserID())))
        self.assertEqual(resp.status_code,HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.index)
        self.assertTemplateUsed(resp, template.people.profile)
        
    def test_profileTab(self):
        profile = Profile.objects.filter().first()
        resp = self.client.get(root(url.people.profileTab(profile.getUserID(),section=profileString.OVERVIEW)))
        self.assertEqual(resp.status_code,HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.people.profile_overview)
        resp = self.client.get(root(url.people.profileTab(profile.getUserID(),section=profileString.PROJECTS)))
        self.assertEqual(resp.status_code,HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.people.profile_projects)
        resp = self.client.get(root(url.people.profileTab(profile.getUserID(),section=profileString.CONTRIBUTION)))
        self.assertEqual(resp.status_code,HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.people.profile_contribution)
        resp = self.client.get(root(url.people.profileTab(profile.getUserID(),section=profileString.ACTIVITY)))
        self.assertEqual(resp.status_code,HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.people.profile_activity)
        resp = self.client.get(root(url.people.profileTab(profile.getUserID(),section=profileString.MODERATION)))
        self.assertEqual(resp.status_code,HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.people.profile_moderation)
        
    def test_settingTab(self):
        resp = self.client.get(root(url.people.settingTab(profileString.Setting.ACCOUNT)))
        self.assertEqual(resp.status_code,HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.people.setting_account)
        resp = self.client.get(root(url.people.settingTab(profileString.Setting.PREFERENCE)))
        self.assertEqual(resp.status_code,HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.people.setting_preference)
        resp = self.client.get(root(url.people.settingTab(profileString.Setting.SECURITY)))
        self.assertEqual(resp.status_code,HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.people.setting_security)

        client = Client()
        client.post(authroot(url.auth.SIGNUP), dict(
            email=TEST_EMAIL,
            first_name=TEST_NAME,
            password1=TEST_PASSWORD
        ),follow=True)
        client.login(email=TEST_EMAIL,password=TEST_PASSWORD)
        client.logout()
        resp = client.get(root(url.people.settingTab(profileString.Setting.ACCOUNT)),follow=True)
        self.assertEqual(resp.status_code,HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.index)
        self.assertTemplateUsed(resp, template.auth.login)
        resp = client.get(root(url.people.settingTab(profileString.Setting.PREFERENCE)),follow=True)
        self.assertEqual(resp.status_code,HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.index)
        self.assertTemplateUsed(resp, template.auth.login)
        resp = client.get(root(url.people.settingTab(profileString.Setting.SECURITY)),follow=True)
        self.assertEqual(resp.status_code,HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.index)
        self.assertTemplateUsed(resp, template.auth.login)
        
