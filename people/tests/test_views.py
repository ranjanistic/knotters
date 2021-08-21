import json
from django.core.exceptions import ObjectDoesNotExist
from django.test import TestCase, Client, tag
from django.db.models import QuerySet
from django.http import HttpResponse, HttpResponseForbidden
from main.strings import Code, url, template, Message, Action
from main.tests.utils import authroot, getRandomStr
from main.env import BOTMAIL
from people.apps import APPNAME
from people.methods import profileString
from people.models import Profile, Topic, User
from .utils import getTestDP, getTestEmail, getTestGHID, getTestName, getTestPassword, getTestTopicsInst, root


@tag(Code.Test.VIEW, APPNAME)
class TestViews(TestCase):
    def setUpTestData(self) -> None:
        self.client = Client()
        self.email = getTestEmail()
        self.password = getTestPassword()
        self.client.post(authroot(url.auth.SIGNUP), dict(
            email=self.email,
            first_name=getTestName(),
            password1=self.password
        ))
        try:
            self.botuser = User.objects.create_user(
                email=BOTMAIL, password=getTestPassword(), first_name=getTestName())
            self.botprofile = Profile.objects.filter(
                user=self.botuser).update(githubID=getRandomStr())
        except:
            self.botuser = User.objects.get(email=BOTMAIL)
            self.botprofile = Profile.objects.get(user=self.botuser)
        try:
            self.user = User.objects.get(email=self.email)
        except:
            self.user = User.objects.create_user(email=self.email,password=self.password,first_name=getTestName())

        Profile.objects.filter(user=self.user).update(githubID=getRandomStr())
        self.profile = self.user.profile
        return super().setUpTestData()

    def setUp(self) -> None:
        self.client.login(email=self.email, password=self.password)

    def test_index(self):
        resp = self.client.get(root(url.INDEX))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.index)
        self.assertTemplateUsed(resp, template.people.index)

    def test_profile(self):
        profile = Profile.objects.filter().first()
        resp = self.client.get(root(url.people.profile(
            userID=profile.getUserID())), follow=True)
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.index)
        self.assertTemplateUsed(resp, template.people.profile)

    def test_profileTab(self):
        profile = Profile.objects.filter().first()
        resp = self.client.get(root(url.people.profileTab(
            profile.getUserID(), section=profileString.OVERVIEW)))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.people.profile_overview)
        resp = self.client.get(root(url.people.profileTab(
            profile.getUserID(), section=profileString.PROJECTS)))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.people.profile_projects)
        resp = self.client.get(root(url.people.profileTab(
            profile.getUserID(), section=profileString.CONTRIBUTION)))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.people.profile_contribution)
        resp = self.client.get(root(url.people.profileTab(
            profile.getUserID(), section=profileString.ACTIVITY)))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.people.profile_activity)
        resp = self.client.get(root(url.people.profileTab(
            profile.getUserID(), section=profileString.MODERATION)))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.people.profile_moderation)

    def test_settingTab(self):
        resp = self.client.get(
            root(url.people.settingTab(profileString.Setting.ACCOUNT)))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.people.setting_account)
        resp = self.client.get(
            root(url.people.settingTab(profileString.Setting.PREFERENCE)))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.people.setting_preference)
        resp = self.client.get(
            root(url.people.settingTab(profileString.Setting.SECURITY)))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.people.setting_security)

        client = Client()
        E2 = getTestEmail()
        P2 = getTestPassword()
        client.post(authroot(url.auth.SIGNUP), dict(
            email=E2,
            first_name=getTestName(),
            password1=P2
        ), follow=True)
        client.logout()
        resp = client.get(root(url.people.settingTab(
            profileString.Setting.ACCOUNT)), follow=True)
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.index)
        self.assertTemplateUsed(resp, template.auth.login)
        resp = client.get(root(url.people.settingTab(
            profileString.Setting.PREFERENCE)), follow=True)
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.index)
        self.assertTemplateUsed(resp, template.auth.login)
        resp = client.get(root(url.people.settingTab(
            profileString.Setting.SECURITY)), follow=True)
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.index)
        self.assertTemplateUsed(resp, template.auth.login)

    def test_editProfile(self):
        resp = self.client.post(root(url.people.profileEdit(getRandomStr())))
        self.assertEqual(resp.status_code, HttpResponseForbidden.status_code)
        resp = self.client.post(
            root(url.people.profileEdit('pallete')), follow=True)
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        resp = self.client.post(root(url.people.profileEdit('pallete')), {
            'profilepic': getTestDP()
        }, follow=True)
        self.assertEqual(resp.status_code, HttpResponse.status_code)

    def test_accountprefs(self):
        resp = self.client.post(
            root(url.people.ACCOUNTPREFERENCES), follow=True)
        self.assertEqual(resp.status_code, HttpResponse.status_code)

    def test_topicsSearch(self):
        resp = self.client.post(root(url.people.TOPICSEARCH), {
                                'query': getRandomStr()})
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertDictEqual(json.loads(resp.content.decode(
            'utf-8')), dict(code=Code.OK, topics=[]))

    @tag('fa')
    def test_topicsUpdate(self):
        topics = Topic.objects.bulk_create(getTestTopicsInst(4))
        addTopicIDs = ''
        for top in topics:
            addTopicIDs = f"{addTopicIDs},{top.getID()}"
        resp = self.client.post(root(url.people.TOPICSUPDATE), {
                                'addtopicIDs': addTopicIDs}, follow=True)
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertEqual(self.profile.totalAllTopics(),4)

        removeTopicIDs = ''
        i = 0
        for top in topics:
            removeTopicIDs = f"{removeTopicIDs},{top.getID()}"
            i+=1
            if i > 1:
                break
        resp = self.client.post(root(url.people.TOPICSUPDATE), {
                                'removetopicIDs': removeTopicIDs}, follow=True)
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertEqual(self.profile.totalAllTopics(),4)
        self.assertEqual(self.profile.totalTopics(),2)
        self.assertEqual(self.profile.totalTrashedTopics(),2)


    def test_accountActivation(self):
        resp = self.client.post(
            root(url.people.ACCOUNTACTIVATION), {'deactivate': True})
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertDictEqual(json.loads(
            resp.content.decode('utf-8')), dict(code=Code.OK))
        self.assertIsInstance(Profile.objects.get(
            user__email=self.email, is_active=False), Profile)

        resp = self.client.post(
            root(url.people.ACCOUNTACTIVATION), {'activate': True})
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertDictEqual(json.loads(
            resp.content.decode('utf-8')), dict(code=Code.OK))
        self.assertIsInstance(Profile.objects.get(
            user__email=self.email, is_active=True), Profile)
        user = User.objects.get(email=self.email)
        Profile.objects.filter(user=user).update(
            is_active=False, suspended=True)
        resp = self.client.post(
            root(url.people.ACCOUNTACTIVATION), {'activate': True})
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertDictEqual(json.loads(
            resp.content.decode('utf-8')), dict(code=Code.NO))
        Profile.objects.filter(user=user).update(
            is_active=True, suspended=False)

    def test_profileSuccessor(self):
        resp = self.client.post(root(url.people.INVITESUCCESSOR))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertDictEqual(json.loads(
            resp.content.decode('utf-8')), dict(code=Code.NO))

        resp = self.client.post(root(url.people.INVITESUCCESSOR), {
                                'useDefault': True, 'set': True})
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertDictEqual(json.loads(
            resp.content.decode('utf-8')), dict(code=Code.OK))
        self.assertIsInstance(Profile.objects.get(user__email=self.email, successor_confirmed=True, successor=User.objects.get(email=BOTMAIL)), Profile)

        resp = self.client.post(
            root(url.people.INVITESUCCESSOR), {'unset': True})
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertDictEqual(json.loads(
            resp.content.decode('utf-8')), dict(code=Code.OK))
        self.assertIsInstance(Profile.objects.get(
            user__email=self.email, successor_confirmed=False, successor=None), Profile)

        E2 = getTestEmail()
        P2 = getTestPassword()
        user = User.objects.create_user(
            email=E2, password=P2, first_name=getTestName())

        resp = self.client.post(root(url.people.INVITESUCCESSOR), {
                                'set': True, 'userID': E2})
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertDictEqual(json.loads(resp.content.decode(
            'utf-8')), dict(code=Code.NO, error=Message.SUCCESSOR_GH_UNLINKED))

        Profile.objects.filter(user=user).update(githubID=getTestGHID())

        resp = self.client.post(root(url.people.INVITESUCCESSOR), {
                                'set': True, 'userID': E2})
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertDictEqual(json.loads(
            resp.content.decode('utf-8')), dict(code=Code.OK))
        self.assertIsInstance(Profile.objects.get(
            user__email=self.email, successor_confirmed=False, successor=user), Profile)

        resp = self.client.post(
            root(url.people.INVITESUCCESSOR), {'unset': True})
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertDictEqual(json.loads(
            resp.content.decode('utf-8')), dict(code=Code.OK))
        self.assertIsInstance(Profile.objects.get(
            user__email=self.email, successor_confirmed=False, successor=None), Profile)

        resp = self.client.post(root(url.people.INVITESUCCESSOR), {
                                'set': True, 'userID': BOTMAIL})
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertDictEqual(json.loads(
            resp.content.decode('utf-8')), dict(code=Code.OK))
        self.assertIsInstance(Profile.objects.get(user__email=self.email, successor_confirmed=True, successor=User.objects.get(email=BOTMAIL)), Profile)

    def test_getSuccessor(self):
        resp = self.client.post(root(url.people.INVITESUCCESSOR), {
                                'set': True, 'userID': BOTMAIL})
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertDictEqual(json.loads(
            resp.content.decode('utf-8')), dict(code=Code.OK))
        resp = self.client.post(root(url.people.GETSUCCESSOR))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertDictEqual(json.loads(resp.content.decode(
            'utf-8')), dict(code=Code.OK, successorID=str()))

    def test_successorInvitation(self):
        client = Client()
        E2 = getTestEmail()
        P2 = getTestPassword()
        client.post(authroot(url.auth.SIGNUP), dict(
            email=E2,
            first_name=getTestName(),
            password1=P2
        ))
        client.logout()
        self.assertTrue(client.login(email=E2, password=P2))
        resp = client.post(root(url.people.INVITESUCCESSOR), {
                           'set': True, 'userID': self.user.email})
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertDictEqual(json.loads(
            resp.content.decode('utf-8')), dict(code=Code.OK))
        profile = Profile.objects.get(
            user__email=E2, successor_confirmed=False, successor=self.user)
        self.assertIsInstance(profile, Profile)

        resp = self.client.get(
            root(url.people.successorInvite(profile.getUserID())))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.index)
        self.assertTemplateUsed(resp, template.invitation)
        self.assertIsInstance(resp.context['predecessor'], User)
        self.assertEqual(resp.context['predecessor'], profile.user)

    def test_successorInviteAction(self):
        client = Client()
        E2 = getTestEmail()
        P2 = getTestPassword()
        client.post(authroot(url.auth.SIGNUP), dict(
            email=E2,
            first_name=getTestName(),
            password1=P2
        ))
        self.assertTrue(client.login(email=E2, password=P2))
        resp = client.post(root(url.people.INVITESUCCESSOR), {
                           'set': True, 'userID': self.user.email})
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertDictEqual(json.loads(
            resp.content.decode('utf-8')), dict(code=Code.OK))
        profile = Profile.objects.get(
            user__email=E2, successor_confirmed=False, successor=self.user)
        self.assertIsInstance(profile, Profile)

        resp = self.client.get(
            root(url.people.successorInvite(profile.getUserID())))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.index)
        self.assertTemplateUsed(resp, template.invitation)
        self.assertIsInstance(resp.context['predecessor'], User)
        self.assertEqual(resp.context['predecessor'], profile.user)

        resp = self.client.post(
            root(url.people.successorInviteAction(Action.DECLINE)))
        self.assertEqual(resp.status_code, HttpResponseForbidden.status_code)
        resp = self.client.post(root(url.people.successorInviteAction(Action.DECLINE)), {
            'predID': self.botuser.getID()
        })
        self.assertEqual(resp.status_code, HttpResponseForbidden.status_code)

        resp = self.client.post(root(url.people.successorInviteAction(Action.DECLINE)), {
            'predID': profile.getUserID()
        }, follow=True)
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertIsInstance(Profile.objects.get(
            user__email=E2, successor_confirmed=False, successor=None), Profile)
        self.assertTemplateUsed(resp, template.index)
        self.assertTemplateUsed(resp, template.people.index)
        self.assertTemplateUsed(resp, template.people.profile)

        resp = client.post(root(url.people.INVITESUCCESSOR), {
                           'set': True, 'userID': self.user.email})
        self.assertEqual(resp.status_code, HttpResponse.status_code)

        resp = self.client.post(root(url.people.successorInviteAction(Action.ACCEPT)), {
            'predID': profile.getUserID()
        }, follow=True)
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertIsInstance(Profile.objects.get(
            user__email=E2, successor_confirmed=True, successor=self.user), Profile)
        self.assertTemplateUsed(resp, template.index)
        self.assertTemplateUsed(resp, template.people.index)
        self.assertTemplateUsed(resp, template.people.profile)

        resp = self.client.post(
            root(url.people.INVITESUCCESSOR), {'unset': True})
        self.assertEqual(resp.status_code, HttpResponse.status_code)

        resp = client.post(root(url.people.INVITESUCCESSOR), {
                           'set': True, 'userID': self.user.email})
        self.assertEqual(resp.status_code, HttpResponse.status_code)

        profile.to_be_zombie = True
        profile.save()

        resp = self.client.post(root(url.people.successorInviteAction(Action.ACCEPT)), {
            'predID': profile.getUserID()
        }, follow=True)
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        with self.assertRaises(ObjectDoesNotExist):
            User.objects.get(email=E2)

    def test_accountDelete(self):
        client = Client()
        E2 = getTestEmail()
        P2 = getTestPassword()
        client.post(authroot(url.auth.SIGNUP), dict(
            email=E2,
            first_name=getTestName(),
            password1=P2
        ))
        client.login(email=E2, password=P2)
        resp = client.post(root(url.people.ACCOUNTDELETE))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertDictEqual(json.loads(
            resp.content.decode('utf-8')), dict(code=Code.NO))

        resp = client.post(root(url.people.ACCOUNTDELETE), {'confirmed': True})
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertDictEqual(json.loads(resp.content.decode(
            'utf-8')), dict(code=Code.NO, error=Message.SUCCESSOR_UNSET))

        resp = client.post(root(url.people.INVITESUCCESSOR),
                           {'useDefault': True, 'set': True})
        self.assertEqual(resp.status_code, HttpResponse.status_code)

        resp = client.post(root(url.people.ACCOUNTDELETE), {'confirmed': True})
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertDictEqual(json.loads(resp.content.decode('utf-8')), dict(code=Code.OK, message=Message.ACCOUNT_DELETED))
        with self.assertRaises(ObjectDoesNotExist):
            User.objects.get(email=E2)


    def test_newbieProfiles(self):
        resp = self.client.get(root(url.people.NEWBIES))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertIsInstance(resp.context['profiles'], QuerySet)
        self.assertTemplateUsed(resp, template.people.browse_newbie)
