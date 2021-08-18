import json
from uuid import uuid4
from django.core.exceptions import ObjectDoesNotExist
from django.test import TestCase, Client, tag
from django.db.models import QuerySet
from django.http import HttpResponse, HttpResponseForbidden
from main.strings import Code, url, template, Message,Action
from main.tests.utils import authroot
from main.env import BOTMAIL
from people.apps import APPNAME
from people.methods import profileString
from people.models import Profile, User
from .utils import TEST_EMAIL, TEST_NAME, TEST_PASSWORD, root, getTestEmails, getTestNames, getTestPasswords

@tag(Code.Test.VIEW, APPNAME, 'aa')
class TestViews(TestCase):
    @classmethod
    def setUpTestData(self) -> None:
        self.client = Client()
        self.client.post(authroot(url.auth.SIGNUP), dict(
            email=TEST_EMAIL,
            first_name=TEST_NAME,
            password1=TEST_PASSWORD
        ))
        try:
            self.botuser = User.objects.create_user(email=BOTMAIL,password=TEST_PASSWORD,first_name=TEST_NAME)
            self.botprofile = Profile.objects.filter(user=self.botuser).update(githubID=uuid4().hex)
        except:
            self.botuser = User.objects.get(email=BOTMAIL)
            self.botprofile = Profile.objects.get(user=self.botuser)
        self.user = User.objects.get(email=TEST_EMAIL)
        Profile.objects.filter(user=self.user).update(githubID=uuid4().hex)
        self.profile = self.user.profile
        return super().setUpTestData()

    def setUp(self) -> None:
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
        E2 = getTestEmails()[0]
        client.post(authroot(url.auth.SIGNUP), dict(
            email=E2,
            first_name=TEST_NAME,
            password1=TEST_PASSWORD
        ),follow=True)
        client.login(email=E2,password=TEST_PASSWORD)
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
        
    def test_editProfile(self):
        resp = self.client.post(root(url.people.profileEdit('err')))
        self.assertEqual(resp.status_code,HttpResponseForbidden.status_code)
        resp = self.client.post(root(url.people.profileEdit('pallete')), follow=True)
        self.assertEqual(resp.status_code,HttpResponse.status_code)
        resp = self.client.post(root(url.people.profileEdit('pallete')), {
            'profilepic': 'alsdkjf'
        },follow=True)
        self.assertEqual(resp.status_code,HttpResponse.status_code)
        
    def test_accountprefs(self):
        resp = self.client.post(root(url.people.ACCOUNTPREFERENCES),follow=True)
        self.assertEqual(resp.status_code,HttpResponse.status_code)

    def test_topicsSearch(self):
        resp = self.client.post(root(url.people.TOPICSEARCH), {'query': 'a'})
        self.assertEqual(resp.status_code,HttpResponse.status_code)
        self.assertDictEqual(json.loads(resp.content.decode('utf-8')), dict(code=Code.OK,topics=[]))

    def test_topicsUpdate(self):
        resp = self.client.post(root(url.people.TOPICSUPDATE), {'addtopicIDs': ""}, follow=True)
        self.assertEqual(resp.status_code,HttpResponse.status_code)

    def test_accountActivation(self):
        resp = self.client.post(root(url.people.ACCOUNTACTIVATION), {'deactivate': True})
        self.assertEqual(resp.status_code,HttpResponse.status_code)
        self.assertDictEqual(json.loads(resp.content.decode('utf-8')), dict(code=Code.OK))
        self.assertIsInstance(Profile.objects.get(user__email=TEST_EMAIL,is_active=False),Profile)

        resp = self.client.post(root(url.people.ACCOUNTACTIVATION), {'activate': True})
        self.assertEqual(resp.status_code,HttpResponse.status_code)
        self.assertDictEqual(json.loads(resp.content.decode('utf-8')), dict(code=Code.OK))
        self.assertIsInstance(Profile.objects.get(user__email=TEST_EMAIL,is_active=True),Profile)
        user = User.objects.get(email=TEST_EMAIL)
        Profile.objects.filter(user=user).update(is_active=False,suspended=True)
        resp = self.client.post(root(url.people.ACCOUNTACTIVATION), {'activate': True})
        self.assertEqual(resp.status_code,HttpResponse.status_code)
        self.assertDictEqual(json.loads(resp.content.decode('utf-8')), dict(code=Code.NO))
        Profile.objects.filter(user=user).update(is_active=True,suspended=False)

    
    def test_profileSuccessor(self):
        resp = self.client.post(root(url.people.INVITESUCCESSOR))
        self.assertEqual(resp.status_code,HttpResponse.status_code)
        self.assertDictEqual(json.loads(resp.content.decode('utf-8')), dict(code=Code.NO))

        resp = self.client.post(root(url.people.INVITESUCCESSOR), {'useDefault': True, 'set': True })
        self.assertEqual(resp.status_code,HttpResponse.status_code)
        self.assertDictEqual(json.loads(resp.content.decode('utf-8')), dict(code=Code.OK))
        self.assertIsInstance(Profile.objects.get(user__email=TEST_EMAIL,successor_confirmed=True,successor=User.objects.get(email=BOTMAIL)),Profile)

        resp = self.client.post(root(url.people.INVITESUCCESSOR), {'unset': True })
        self.assertEqual(resp.status_code,HttpResponse.status_code)
        self.assertDictEqual(json.loads(resp.content.decode('utf-8')), dict(code=Code.OK))
        self.assertIsInstance(Profile.objects.get(user__email=TEST_EMAIL,successor_confirmed=False,successor=None),Profile)

        E2 = getTestEmails()[0]
        user = User.objects.create_user(email=E2,password=getTestPasswords()[0],first_name=getTestNames()[0])

        resp = self.client.post(root(url.people.INVITESUCCESSOR), {'set': True, 'userID': E2 })
        self.assertEqual(resp.status_code,HttpResponse.status_code)
        self.assertDictEqual(json.loads(resp.content.decode('utf-8')), dict(code=Code.NO,error=Message.SUCCESSOR_GH_UNLINKED))

        Profile.objects.filter(user=user).update(githubID=uuid4().hex)

        resp = self.client.post(root(url.people.INVITESUCCESSOR), {'set': True, 'userID': E2 })
        self.assertEqual(resp.status_code,HttpResponse.status_code)
        self.assertDictEqual(json.loads(resp.content.decode('utf-8')), dict(code=Code.OK))
        self.assertIsInstance(Profile.objects.get(user__email=TEST_EMAIL,successor_confirmed=False,successor=user),Profile)
        
        resp = self.client.post(root(url.people.INVITESUCCESSOR), {'unset': True })
        self.assertEqual(resp.status_code,HttpResponse.status_code)
        self.assertDictEqual(json.loads(resp.content.decode('utf-8')), dict(code=Code.OK))
        self.assertIsInstance(Profile.objects.get(user__email=TEST_EMAIL,successor_confirmed=False,successor=None),Profile)
        
        resp = self.client.post(root(url.people.INVITESUCCESSOR), {'set': True, 'userID': BOTMAIL })
        self.assertEqual(resp.status_code,HttpResponse.status_code)
        self.assertDictEqual(json.loads(resp.content.decode('utf-8')), dict(code=Code.OK))
        self.assertIsInstance(Profile.objects.get(user__email=TEST_EMAIL,successor_confirmed=True,successor=User.objects.get(email=BOTMAIL)),Profile)

    
    def test_getSuccessor(self):
        resp = self.client.post(root(url.people.INVITESUCCESSOR), {'set': True, 'userID': BOTMAIL })
        self.assertEqual(resp.status_code,HttpResponse.status_code)
        self.assertDictEqual(json.loads(resp.content.decode('utf-8')), dict(code=Code.OK))
        resp = self.client.post(root(url.people.GETSUCCESSOR))
        self.assertEqual(resp.status_code,HttpResponse.status_code)
        self.assertDictEqual(json.loads(resp.content.decode('utf-8')), dict(code=Code.OK,successorID=''))
        
    def test_successorInvitation(self):
        client = Client()
        E2 = getTestEmails()[0]
        N2 = getTestNames()[0]
        P2 = getTestPasswords()[0]
        client.post(authroot(url.auth.SIGNUP), dict(
            email=E2,
            first_name=N2,
            password1=P2
        ))
        client.login(email=E2,password=P2)
        resp = client.post(root(url.people.INVITESUCCESSOR), {'set': True, 'userID': self.user.email })
        self.assertEqual(resp.status_code,HttpResponse.status_code)
        self.assertDictEqual(json.loads(resp.content.decode('utf-8')), dict(code=Code.OK))
        profile = Profile.objects.get(user__email=E2,successor_confirmed=False,successor=self.user)
        self.assertIsInstance(profile,Profile)

        resp = self.client.get(root(url.people.successorInvite(profile.getUserID())))
        self.assertEqual(resp.status_code,HttpResponse.status_code)
        self.assertTemplateUsed(resp,template.index)
        self.assertTemplateUsed(resp,template.invitation)
        self.assertIsInstance(resp.context['predecessor'],User)
        self.assertEqual(resp.context['predecessor'],profile.user)
    
    
    def test_successorInviteAction(self):
        client = Client()
        E2 = getTestEmails()[0]
        N2 = getTestNames()[0]
        P2 = getTestPasswords()[0]
        client.post(authroot(url.auth.SIGNUP), dict(
            email=E2,
            first_name=N2,
            password1=P2
        ))
        client.login(email=E2,password=P2)
        resp = client.post(root(url.people.INVITESUCCESSOR), {'set': True, 'userID': self.user.email })
        self.assertEqual(resp.status_code,HttpResponse.status_code)
        self.assertDictEqual(json.loads(resp.content.decode('utf-8')), dict(code=Code.OK))
        profile = Profile.objects.get(user__email=E2,successor_confirmed=False,successor=self.user)
        self.assertIsInstance(profile,Profile)

        resp = self.client.get(root(url.people.successorInvite(profile.getUserID())))
        self.assertEqual(resp.status_code,HttpResponse.status_code)
        self.assertTemplateUsed(resp,template.index)
        self.assertTemplateUsed(resp,template.invitation)
        self.assertIsInstance(resp.context['predecessor'],User)
        self.assertEqual(resp.context['predecessor'],profile.user)

        resp = self.client.post(root(url.people.successorInviteAction(Action.DECLINE)))
        self.assertEqual(resp.status_code, HttpResponseForbidden.status_code)
        resp = self.client.post(root(url.people.successorInviteAction(Action.DECLINE)), {
            'predID': self.botuser.getID()
        })
        self.assertEqual(resp.status_code, HttpResponseForbidden.status_code)

        resp = self.client.post(root(url.people.successorInviteAction(Action.DECLINE)), {
            'predID': profile.getUserID()
        }, follow=True)
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertIsInstance(Profile.objects.get(user__email=E2,successor_confirmed=False,successor=None), Profile)
        self.assertTemplateUsed(resp,template.index)
        self.assertTemplateUsed(resp,template.people.index)
        self.assertTemplateUsed(resp,template.people.profile)

        resp = client.post(root(url.people.INVITESUCCESSOR), {'set': True, 'userID': self.user.email })
        self.assertEqual(resp.status_code,HttpResponse.status_code)

        resp = self.client.post(root(url.people.successorInviteAction(Action.ACCEPT)), {
            'predID': profile.getUserID()
        }, follow=True)
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertIsInstance(Profile.objects.get(user__email=E2,successor_confirmed=True,successor=self.user), Profile)
        self.assertTemplateUsed(resp,template.index)
        self.assertTemplateUsed(resp,template.people.index)
        self.assertTemplateUsed(resp,template.people.profile)

        resp = self.client.post(root(url.people.INVITESUCCESSOR), {'unset': True })
        self.assertEqual(resp.status_code,HttpResponse.status_code)

        resp = client.post(root(url.people.INVITESUCCESSOR), {'set': True, 'userID': self.user.email })
        self.assertEqual(resp.status_code,HttpResponse.status_code)

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
        E2 = getTestEmails()[0]
        N2 = getTestNames()[0]
        P2 = getTestPasswords()[0]
        client.post(authroot(url.auth.SIGNUP), dict(
            email=E2,
            first_name=N2,
            password1=P2
        ))
        client.login(email=E2,password=P2)
        resp = client.post(root(url.people.ACCOUNTDELETE))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertDictEqual(json.loads(resp.content.decode('utf-8')), dict(code=Code.NO))

        resp = client.post(root(url.people.ACCOUNTDELETE), {'confirmed': True})
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertDictEqual(json.loads(resp.content.decode('utf-8')), dict(code=Code.NO, error=Message.SUCCESSOR_UNSET))

        resp = client.post(root(url.people.INVITESUCCESSOR), {'useDefault': True, 'set': True })
        self.assertEqual(resp.status_code,HttpResponse.status_code)

        resp = client.post(root(url.people.ACCOUNTDELETE), {'confirmed': True})
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertDictEqual(json.loads(resp.content.decode('utf-8')), dict(code=Code.OK,message=Message.ACCOUNT_DELETED))

    def test_newbieProfiles(self):
        resp = self.client.get(root(url.people.NEWBIES))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertIsInstance(resp.context['profiles'],QuerySet)
        self.assertTemplateUsed(resp, template.people.browse_newbie)