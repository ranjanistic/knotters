from json import loads as json_loads
from django.http.response import HttpResponseNotFound
from django.test import TestCase, Client, tag
from django.http import HttpResponse
from main.strings import Code, url, template
from allauth.account.models import EmailAddress
from main.tests.utils import authroot, getRandomStr
from main.env import BOTMAIL
from people.apps import APPNAME
from people.methods import profileString
from people.models import Profile, Topic, User
from auth2.tests.utils import getTestEmail, getTestName, getTestPassword
from .utils import getTestDP, getTestTopicsInst, root


@tag(Code.Test.VIEW, APPNAME, 'aha')
class TestViews(TestCase):

    @classmethod
    def setUpTestData(self) -> None:
        self.client = Client()
        self.botuser, _ = User.objects.get_or_create(email=BOTMAIL, defaults=dict(
            first_name=getTestName(), email=BOTMAIL, password=getTestPassword()))
        self.email = getTestEmail()
        self.password = getTestPassword()
        self.client.post(follow=True, path=authroot(url.auth.SIGNUP), data=dict(
            email=self.email,
            first_name=getTestName(),
            password1=self.password
        ))
        try:
            Profile.objects.filter(
                user=self.botuser).update(githubID=getRandomStr())
        except:
            self.botuser = User.objects.create_user(
                email=BOTMAIL, password=getTestPassword(), first_name=getTestName())
            Profile.objects.filter(
                user=self.botuser).update(githubID=getRandomStr())
        self.botprofile = Profile.objects.get(user=self.botuser)
        try:
            self.user = User.objects.get(email=self.email)
        except:
            self.user = User.objects.create_user(
                email=self.email, password=self.password, first_name=getTestName())
        EmailAddress.objects.filter(email=self.email).update(verified=True)
        Profile.objects.filter(user=self.user).update(githubID=getRandomStr())
        self.profile = self.user.profile
        # mail, created = EmailAddress.objects.get_or_create(user=self.user,defaults=dict(
        #     email=self.user.email,
        #     verified=True,
        #     primary=True
        # ))
        # if not created:
        #     mail.verified=True
        #     mail.primary=True
        #     mail.save()
        return super().setUpTestData()

    def setUp(self) -> None:
        resp = self.client.post(follow=True, path=authroot(url.auth.LOGIN), data=dict(
            login=self.email,
            password=self.password,
        ))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTrue(resp.context['user'].is_authenticated)

    def test_index(self):
        resp = self.client.get(follow=True, path=root(url.INDEX))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.index)
        self.assertTemplateUsed(resp, template.people.index)

    @tag("gg")
    def test_profile(self):
        resp = self.client.get(follow=True, path=root(url.people.profile(
            userID=self.profile.getUserID())))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.index)
        self.assertTemplateUsed(resp, template.people.profile)

    @tag("aag")
    def test_profileTab(self):
        resp = self.client.get(follow=True, path=root(url.people.profileTab(
            self.profile.getUserID(), section=profileString.OVERVIEW)))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.people.profile_overview)
        resp = self.client.get(follow=True, path=root(url.people.profileTab(
            self.profile.getUserID(), section=profileString.PROJECTS)))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.people.profile_projects)
        resp = self.client.get(follow=True, path=root(url.people.profileTab(
            self.profile.getUserID(), section=profileString.CONTRIBUTION)))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.people.profile_contribution)
        resp = self.client.get(follow=True, path=root(url.people.profileTab(
            self.profile.getUserID(), section=profileString.ACTIVITY)))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.people.profile_activity)
        resp = self.client.get(follow=True, path=root(url.people.profileTab(
            self.profile.getUserID(), section=profileString.MODERATION)))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.people.profile_moderation)

    def test_settingTab(self):
        resp = self.client.get(follow=True, path=root(
            url.people.settingTab(profileString.Setting.ACCOUNT)))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.people.setting_account)
        resp = self.client.get(follow=True, path=root(
            url.people.settingTab(profileString.Setting.PREFERENCE)))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.people.setting_preference)
        resp = self.client.get(follow=True, path=root(
            url.people.settingTab(profileString.Setting.SECURITY)))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.people.setting_security)

        client = Client()
        E2 = getTestEmail()
        P2 = getTestPassword()
        client.post(follow=True, path=authroot(url.auth.SIGNUP), data=dict(
            email=E2,
            first_name=getTestName(),
            password1=P2
        ))
        client.logout()
        resp = client.get(follow=True, path=root(url.people.settingTab(
            profileString.Setting.ACCOUNT)))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.index)
        self.assertTemplateUsed(resp, template.auth.login)
        resp = client.get(follow=True, path=root(url.people.settingTab(
            profileString.Setting.PREFERENCE)))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.index)
        self.assertTemplateUsed(resp, template.auth.login)
        resp = client.get(follow=True, path=root(url.people.settingTab(
            profileString.Setting.SECURITY)))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.index)
        self.assertTemplateUsed(resp, template.auth.login)

    @tag("editprof")
    def test_editProfile(self):
        resp = self.client.post(follow=True, path=root(
            url.people.profileEdit(getRandomStr())))
        self.assertEqual(resp.status_code, HttpResponseNotFound.status_code)
        resp = self.client.post(follow=True, path=root(
            url.people.profileEdit('pallete')))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        resp = self.client.post(follow=True, path=root(url.people.profileEdit('pallete')), data={
            'profilepic': getTestDP()
        })
        self.assertEqual(resp.status_code, HttpResponse.status_code)

    @tag("gg")
    def test_accountprefs(self):
        resp = self.client.post(follow=True, path=root(
            url.people.ACCOUNTPREFERENCES))
        self.assertEqual(resp.status_code, HttpResponse.status_code)

    def test_topicsSearch(self):
        resp = self.client.post(follow=True, path=root(url.people.TOPICSEARCH), data={
                                'query': getRandomStr()})
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertDictEqual(json_loads(resp.content.decode(
            Code.UTF_8)), dict(code=Code.OK, topics=[]))

    def test_topicsUpdate(self):
        topics = Topic.objects.bulk_create(getTestTopicsInst(4))
        addTopicIDs = ''
        for top in topics:
            addTopicIDs = f"{addTopicIDs},{top.getID()}"
        resp = self.client.post(follow=True, path=root(url.people.TOPICSUPDATE), data={
                                'addtopicIDs': addTopicIDs})
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertEqual(self.profile.totalAllTopics(), 4)

        removeTopicIDs = ''
        i = 0
        for top in topics:
            removeTopicIDs = f"{removeTopicIDs},{top.getID()}"
            i += 1
            if i > 1:
                break
        resp = self.client.post(follow=True, path=root(url.people.TOPICSUPDATE), data={
                                'removetopicIDs': removeTopicIDs})
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertEqual(self.profile.totalAllTopics(), 4)
        self.assertEqual(self.profile.totalTopics(), 2)
        self.assertEqual(self.profile.totalTrashedTopics(), 2)
