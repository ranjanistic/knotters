from json import loads as json_loads, dumps as json_dumps

from allauth.account.models import EmailAddress
from auth2.apps import APPNAME
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from django.http.response import HttpResponseNotFound, HttpResponseRedirect
from django.test import Client, TestCase, tag
from main.env import BOTMAIL
from main.methods import testPathRegex
from main.strings import Action, Code, Message, template, url
from main.tests.utils import authroot, getRandomStr
from people.models import Profile, User
from auth2.models import Notification, EmailNotificationSubscriber
from main.constants import NotificationCode
from .utils import (getTestEmail, getTestGHID, getTestName, getTestPassword,
                    root)
from people.mailers import milestoneNotif


@tag(Code.Test.VIEW, APPNAME)
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
        return super().setUpTestData()


    def test_index(self):
        client = Client()
        resp = client.get(path=root(appendslash=True))
        self.assertEqual(resp.status_code, HttpResponseRedirect.status_code)
        self.assertTrue(testPathRegex(resp.url, root(url.auth.LOGIN)))
        resp = client.get(path=root(appendslash=True), follow=True)
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.auth.login)


    @tag('acctiv')
    def test_accountActivation(self):
        client = Client()
        email = getTestEmail()
        password = getTestPassword()
        client.post(follow=True, path=authroot(url.auth.SIGNUP), data=dict(
            email=email,
            first_name=getTestName(),
            password1=password
        ))
        EmailAddress.objects.filter(email=email).update(verified=True)
        resp = client.post(follow=True, path=root(
            url.auth.ACCOUNTACTIVATION), data={'deactivate': True})
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertDictEqual(json_loads(
            resp.content.decode(Code.UTF_8)), dict(code=Code.OK))
        self.assertIsInstance(Profile.objects.get(
            user__email=email, is_active=False), Profile)

        resp = client.post(follow=True, path=root(
            url.auth.ACCOUNTACTIVATION), data={'activate': True})
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertDictEqual(json_loads(
            resp.content.decode(Code.UTF_8)), dict(code=Code.OK))
        self.assertIsInstance(Profile.objects.get(
            user__email=email, is_active=True), Profile)
        user = User.objects.get(email=email)
        Profile.objects.filter(user=user).update(
            is_active=False, suspended=True)
        resp = client.post(follow=True, path=root(
            url.auth.ACCOUNTACTIVATION), data={'activate': True})
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertDictEqual(json_loads(
            resp.content.decode(Code.UTF_8)), dict(code=Code.NO, error=Message.INVALID_REQUEST))
        Profile.objects.filter(user=user).update(
            is_active=True, suspended=False)

    @tag("profsuc")
    def test_profileSuccessor(self):
        client = Client()
        email = getTestEmail()
        password = getTestPassword()
        client.post(follow=True, path=authroot(url.auth.SIGNUP), data=dict(
            email=email,
            first_name=getTestName(),
            password1=password
        ))
        EmailAddress.objects.filter(email=email).update(verified=True)
        resp = client.post(
            follow=True, path=root(url.auth.INVITESUCCESSOR))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertDictEqual(json_loads(
            resp.content.decode(Code.UTF_8)), dict(code=Code.NO))

        resp = client.post(follow=True, path=root(url.auth.INVITESUCCESSOR), data={
                                'useDefault': True, 'set': True})
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertDictEqual(json_loads(
            resp.content.decode(Code.UTF_8)), dict(code=Code.OK))
        self.assertIsInstance(Profile.objects.get(
            user__email=email, successor_confirmed=True, successor=User.objects.get(email=BOTMAIL)), Profile)

        resp = client.post(follow=True, path=root(
            url.auth.INVITESUCCESSOR), data={'unset': True})
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertDictEqual(json_loads(
            resp.content.decode(Code.UTF_8)), dict(code=Code.OK))
        self.assertIsInstance(Profile.objects.get(
            user__email=email, successor_confirmed=False, successor=None), Profile)

        E2 = getTestEmail()
        P2 = getTestPassword()
        user = User.objects.create_user(
            email=E2, password=P2, first_name=getTestName())
        EmailAddress.objects.create(
            user=user, email=user.email, primary=True, verified=True)
        resp = client.post(follow=True, path=root(url.auth.INVITESUCCESSOR), data={
                                'set': True, 'userID': E2})
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertDictEqual(json_loads(resp.content.decode(
            Code.UTF_8)), dict(code=Code.NO, error=Message.SUCCESSOR_GH_UNLINKED))

        Profile.objects.filter(user=user).update(githubID=getTestGHID())

        resp = client.post(follow=True, path=root(url.auth.INVITESUCCESSOR), data={
                                'set': True, 'userID': E2})
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertDictEqual(json_loads(
            resp.content.decode(Code.UTF_8)), dict(code=Code.OK))
        self.assertIsInstance(Profile.objects.get(
            user__email=email, successor_confirmed=False, successor=user), Profile)

        resp = client.post(follow=True, path=root(
            url.auth.INVITESUCCESSOR), data={'unset': True})
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertDictEqual(json_loads(
            resp.content.decode(Code.UTF_8)), dict(code=Code.OK))
        self.assertIsInstance(Profile.objects.get(
            user__email=email, successor_confirmed=False, successor=None), Profile)

        resp = client.post(follow=True, path=root(url.auth.INVITESUCCESSOR), data={
                                'set': True, 'userID': BOTMAIL})
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertDictEqual(json_loads(
            resp.content.decode(Code.UTF_8)), dict(code=Code.OK))
        self.assertIsInstance(Profile.objects.get(
            user__email=email, successor_confirmed=True, successor=User.objects.get(email=BOTMAIL)), Profile)

    def test_getSuccessor(self):
        client = Client()
        email = getTestEmail()
        password = getTestPassword()
        client.post(follow=True, path=authroot(url.auth.SIGNUP), data=dict(
            email=email,
            first_name=getTestName(),
            password1=password
        ))
        EmailAddress.objects.filter(email=email).update(verified=True)
        resp = client.post(follow=True, path=root(url.auth.INVITESUCCESSOR), data={
                                'set': True, 'useDefault': True})
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertDictEqual(json_loads(
            resp.content.decode(Code.UTF_8)), dict(code=Code.OK))
        resp = client.post(
            follow=True, path=root(url.auth.GETSUCCESSOR))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertDictEqual(json_loads(resp.content.decode(
            Code.UTF_8)), dict(code=Code.OK, successorID=str()))

    def TestSuccessorInvitation(self, client: Client):
        client2 = Client()
        E2 = getTestEmail()
        P2 = getTestPassword()
        client2.post(follow=True, path=authroot(url.auth.SIGNUP), data=dict(
            email=E2,
            first_name=getTestName(),
            password1=P2
        ))
        EmailAddress.objects.filter().update(verified=True)
        client2.post(follow=True, path=authroot(url.auth.LOGIN), data=dict(
            login=E2,
            password=P2
        ))
        resp = client2.post(follow=True, path=root(url.auth.INVITESUCCESSOR), data={
            'set': True, 'userID': self.user.email})
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertDictEqual(json_loads(
            resp.content.decode(Code.UTF_8)), dict(code=Code.OK))
        predprofile = Profile.objects.get(
            user__email=E2, successor_confirmed=False, successor=self.user)
        self.assertIsInstance(predprofile, Profile)

        resp = client.get(follow=True, path=root(
            url.auth.successorInvite(predprofile.get_userid)))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.index)
        self.assertTemplateUsed(resp, template.invitation)
        self.assertTemplateUsed(resp, template.auth.invitation)
        self.assertIsInstance(resp.context['predecessor'], User)
        self.assertEqual(resp.context['predecessor'], predprofile.user)
        return self.TestSuccessorInviteAction(predprofile, E2, P2, client)

    def TestSuccessorInviteAction(self, predprofile, useremail, userpass, client: Client):
        E2 = useremail
        P2 = userpass
        predprofile
        resp = client.get(follow=True, path=root(
            url.auth.successorInvite(predprofile.get_userid)))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.index)
        self.assertTemplateUsed(resp, template.invitation)
        self.assertTemplateUsed(resp, template.auth.invitation)
        self.assertIsInstance(resp.context['predecessor'], User)
        self.assertEqual(resp.context['predecessor'], predprofile.user)

        resp = client.post(follow=True, path=root(
            url.auth.successorInviteAction(Action.DECLINE)))
        self.assertEqual(resp.status_code, HttpResponseNotFound.status_code)
        resp = client.post(follow=True, path=root(url.auth.successorInviteAction(Action.DECLINE)), data={
            'predID': self.botuser.getID()
        })
        self.assertEqual(resp.status_code, HttpResponseNotFound.status_code)

        resp = client.post(follow=True, path=root(url.auth.successorInviteAction(Action.DECLINE)), data={
            'predID': predprofile.get_userid
        })
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertIsInstance(Profile.objects.get(
            user__email=E2, successor_confirmed=False, successor=None), Profile)
        self.assertTemplateUsed(resp, template.index)
        self.assertTemplateUsed(resp, template.people.index)
        self.assertTemplateUsed(resp, template.people.profile)

        client2 = Client()
        resp = client2.post(follow=True, path=authroot(url.auth.LOGIN), data=dict(
            login=E2,
            password=P2
        ))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        resp = client2.post(follow=True, path=root(url.auth.INVITESUCCESSOR), data={
                            'set': True, 'userID': self.user.email})
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertDictEqual(json_loads(
            resp.content.decode(Code.UTF_8)), dict(code=Code.OK))

        resp = client.post(follow=True, path=root(url.auth.successorInviteAction(Action.ACCEPT)), data={
            'predID': predprofile.get_userid
        })
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertIsInstance(Profile.objects.get(
            user__email=E2, successor_confirmed=True, successor=self.user), Profile)
        self.assertTemplateUsed(resp, template.index)
        self.assertTemplateUsed(resp, template.people.index)
        self.assertTemplateUsed(resp, template.people.profile)

        client3 = Client()
        client3.post(follow=True, path=authroot(url.auth.LOGIN), data=dict(
            login=E2,
            password=P2
        ))
        resp = client3.post(follow=True, path=root(
            url.auth.INVITESUCCESSOR), data={'unset': True})
        self.assertEqual(resp.status_code, HttpResponse.status_code)

        resp = client3.post(follow=True, path=root(url.auth.INVITESUCCESSOR), data={
                           'set': True, 'userID': self.user.email})
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        return predprofile, E2, P2

    @tag("accdel")
    def test_accountDelete(self):
        client = Client()
        resp = client.post(follow=True, path=authroot(url.auth.LOGIN), data=dict(
            login=self.email,
            password=self.password,
        ))
        clientx = Client()
        E3 = getTestEmail()
        P3 = getTestPassword()
        clientx.post(follow=True, path=authroot(url.auth.SIGNUP), data=dict(
            email=E3,
            first_name=getTestName(),
            password1=P3
        ))
        EmailAddress.objects.filter().update(verified=True)
        clientx.post(follow=True, path=authroot(url.auth.LOGIN), data=dict(
            login=E3,
            password=P3
        ))
        resp = clientx.post(follow=True, path=root(url.auth.ACCOUNTDELETE))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertDictEqual(json_loads(
            resp.content.decode(Code.UTF_8)), dict(code=Code.NO))

        resp = clientx.post(follow=True, path=root(
            url.auth.ACCOUNTDELETE), data={'confirmed': True})
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertDictEqual(json_loads(resp.content.decode(
            Code.UTF_8)), dict(code=Code.NO, error=Message.SUCCESSOR_UNSET))

        predprofile, E2, P2 = self.TestSuccessorInvitation(client)

        resp = client.post(follow=True, path=root(url.auth.successorInviteAction(Action.ACCEPT)), data={
            'predID': predprofile.get_userid
        })
        self.assertEqual(resp.status_code, HttpResponse.status_code)

        client2 = Client()
        client2.post(follow=True, path=authroot(url.auth.LOGIN), data=dict(
            login=E2,
            password=P2
        ))
        resp = client2.post(follow=True, path=root(
            url.auth.ACCOUNTDELETE), data={'confirmed': True})
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertDictEqual(json_loads(resp.content.decode(
            Code.UTF_8)), dict(code=Code.OK, message=Message.ACCOUNT_DELETED))
        with self.assertRaises(ObjectDoesNotExist):
            User.objects.get(email=E2)
    
    @tag("notif")
    def test_notifications(self):
        client = Client()
        email = getTestEmail()
        password = getTestPassword()
        resp = client.post(follow=True, path=authroot(url.auth.SIGNUP), data=dict(
            email=email,
            first_name=getTestName(),
            password1=password
        ))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTrue(resp.context['user'].is_authenticated)
        notif:Notification = Notification.objects.create(name=getRandomStr(), description=getRandomStr(), code=NotificationCode.MILESTONE_NOTIF)
        resp = client.post(follow=True, path=authroot(url.auth.notificationToggleEmail(notif.id)), data=dict(
            subscribe=True
        ), content_type=Code.APPLICATION_JSON)
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertDictEqual(json_loads(
            resp.content.decode(Code.UTF_8)), dict(code=Code.OK))
        profile = Profile.objects.get(user__email=email)
        device, email1 = milestoneNotif(profile)
        self.assertNotEqual(email1, False)
        self.assertFalse(device)
        resp = client.post(follow=True, path=authroot(url.auth.notificationToggleDevice(notif.id)), data=dict(
            subscribe=True
        ), content_type=Code.APPLICATION_JSON)
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertDictEqual(json_loads(
            resp.content.decode(Code.UTF_8)), dict(code=Code.OK))
        device, email1 = milestoneNotif(profile)
        self.assertNotEqual(device, False)
        self.assertNotEqual(email1, False)
        resp = client.post(follow=True, path=authroot(url.auth.notificationToggleEmail(notif.id)), data=dict(
            subscribe=False
        ), content_type=Code.APPLICATION_JSON)
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertDictEqual(json_loads(
            resp.content.decode(Code.UTF_8)), dict(code=Code.OK))
        device, email1 = milestoneNotif(profile)
        self.assertNotEqual(device, False)
        self.assertFalse(email1)

        
@tag(Code.Test.VIEW, Code.Test.REST, APPNAME)
class TestViewsAuth(TestCase):
    @classmethod
    def setUpTestData(self) -> None:
        self.client = Client()
        self.bot, _ = User.objects.get_or_create(email=BOTMAIL, defaults=dict(
            first_name='knottersbot', email=BOTMAIL, password=getTestPassword()))
        return super().setUpTestData()
    
    def test_signup(self):
        client = Client()
        resp = client.get(follow=True, path=authroot(url.auth.SIGNUP))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.index)
        self.assertTemplateUsed(resp, template.auth.signup)

    def test_login(self):
        client = Client()
        resp = client.get(follow=True, path=authroot(url.auth.LOGIN))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.index)
        self.assertTemplateUsed(resp, template.auth.login)

    @tag('test-logout')
    def test_logout(self):
        client = Client()
        resp = client.get(path=authroot(url.auth.LOGOUT))
        self.assertEqual(resp.status_code, HttpResponseRedirect.status_code)
        resp = client.get(path=authroot(url.auth.LOGOUT), follow=True)
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.index)

    @tag("signup_post")
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
        
        client = Client()
        resp = client.post(follow=True, path=authroot(url.auth.SIGNUP), data=dict(
            email=getTestEmail(),
            first_name=getTestName(),
            password1=getTestPassword()
        ))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTrue(resp.context['user'].is_authenticated)
        self.assertTemplateUsed(resp, template.index)
        self.assertTemplateUsed(resp, template.on_boarding)

    @tag("login_post")
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
        self.assertTrue(resp.context['user'].is_authenticated)
        resp = client.post(follow=True, path=authroot(url.auth.LOGOUT))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertFalse(resp.context['user'].is_authenticated)

        resp = client.post(follow=True, path=authroot(url.auth.LOGIN))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertFalse(resp.context['user'].is_authenticated)

        resp = client.post(follow=True, path=authroot(url.auth.LOGIN), data=dict(
            login=str(),
            password=str(),
        ))
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
        self.assertTrue(resp.context['user'].is_authenticated)

    @tag("logout_post")
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
        self.assertTrue(resp.context['user'].is_authenticated)

        resp = client.post(follow=True, path=authroot(url.auth.LOGOUT))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertFalse(resp.context['user'].is_authenticated)

        resp = client.post(follow=True, path=authroot(url.auth.LOGIN), data=dict(
            login=email,
            password=password,
        ))
        self.assertTrue(resp.context['user'].is_authenticated)
        resp = client.post(follow=True, path=authroot(url.auth.LOGOUT))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertFalse(resp.context['user'].is_authenticated)