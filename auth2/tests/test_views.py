import json
from django.core.exceptions import ObjectDoesNotExist
from django.http.response import HttpResponseNotFound
from django.test import TestCase, Client, tag
from django.http import HttpResponse, HttpResponseForbidden
from main.strings import Code, url, template, Message, Action
from allauth.account.models import EmailAddress
from main.tests.utils import authroot, getRandomStr
from main.env import BOTMAIL
from people.models import Profile, User
from auth2.apps import APPNAME
from .utils import getTestEmail, getTestGHID, getTestName, getTestPassword, root


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

    def setUp(self) -> None:
        resp = self.client.post(follow=True, path=authroot(url.auth.LOGIN), data=dict(
            login=self.email,
            password=self.password,
        ))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTrue(resp.context['user'].is_authenticated)

    @tag('acctiv')
    def test_accountActivation(self):
        resp = self.client.post(follow=True, path=root(
            url.auth.ACCOUNTACTIVATION), data={'deactivate': True})
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertDictEqual(json.loads(
            resp.content.decode(Code.UTF_8)), dict(code=Code.OK))
        self.assertIsInstance(Profile.objects.get(
            user__email=self.email, is_active=False), Profile)

        resp = self.client.post(follow=True, path=root(
            url.auth.ACCOUNTACTIVATION), data={'activate': True})
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertDictEqual(json.loads(
            resp.content.decode(Code.UTF_8)), dict(code=Code.OK))
        self.assertIsInstance(Profile.objects.get(
            user__email=self.email, is_active=True), Profile)
        user = User.objects.get(email=self.email)
        Profile.objects.filter(user=user).update(
            is_active=False, suspended=True)
        resp = self.client.post(follow=True, path=root(
            url.auth.ACCOUNTACTIVATION), data={'activate': True})
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertDictEqual(json.loads(
            resp.content.decode(Code.UTF_8)), dict(code=Code.NO, error=Message.INVALID_REQUEST))
        Profile.objects.filter(user=user).update(
            is_active=True, suspended=False)

    @tag("profsuc")
    def test_profileSuccessor(self):
        resp = self.client.post(
            follow=True, path=root(url.auth.INVITESUCCESSOR))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertDictEqual(json.loads(
            resp.content.decode(Code.UTF_8)), dict(code=Code.NO))

        resp = self.client.post(follow=True, path=root(url.auth.INVITESUCCESSOR), data={
                                'useDefault': True, 'set': True})
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertDictEqual(json.loads(
            resp.content.decode(Code.UTF_8)), dict(code=Code.OK))
        self.assertIsInstance(Profile.objects.get(
            user__email=self.email, successor_confirmed=True, successor=User.objects.get(email=BOTMAIL)), Profile)

        resp = self.client.post(follow=True, path=root(
            url.auth.INVITESUCCESSOR), data={'unset': True})
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertDictEqual(json.loads(
            resp.content.decode(Code.UTF_8)), dict(code=Code.OK))
        self.assertIsInstance(Profile.objects.get(
            user__email=self.email, successor_confirmed=False, successor=None), Profile)

        E2 = getTestEmail()
        P2 = getTestPassword()
        user = User.objects.create_user(
            email=E2, password=P2, first_name=getTestName())
        EmailAddress.objects.create(user=user,email=user.email,primary=True,verified=True)
        resp = self.client.post(follow=True, path=root(url.auth.INVITESUCCESSOR), data={
                                'set': True, 'userID': E2})
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertDictEqual(json.loads(resp.content.decode(
            Code.UTF_8)), dict(code=Code.NO, error=Message.SUCCESSOR_GH_UNLINKED))

        Profile.objects.filter(user=user).update(githubID=getTestGHID())

        resp = self.client.post(follow=True, path=root(url.auth.INVITESUCCESSOR), data={
                                'set': True, 'userID': E2})
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertDictEqual(json.loads(
            resp.content.decode(Code.UTF_8)), dict(code=Code.OK))
        self.assertIsInstance(Profile.objects.get(
            user__email=self.email, successor_confirmed=False, successor=user), Profile)

        resp = self.client.post(follow=True, path=root(
            url.auth.INVITESUCCESSOR), data={'unset': True})
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertDictEqual(json.loads(
            resp.content.decode(Code.UTF_8)), dict(code=Code.OK))
        self.assertIsInstance(Profile.objects.get(
            user__email=self.email, successor_confirmed=False, successor=None), Profile)

        resp = self.client.post(follow=True, path=root(url.auth.INVITESUCCESSOR), data={
                                'set': True, 'userID': BOTMAIL})
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertDictEqual(json.loads(
            resp.content.decode(Code.UTF_8)), dict(code=Code.OK))
        self.assertIsInstance(Profile.objects.get(
            user__email=self.email, successor_confirmed=True, successor=User.objects.get(email=BOTMAIL)), Profile)

    def test_getSuccessor(self):
        resp = self.client.post(follow=True, path=root(url.auth.INVITESUCCESSOR), data={
                                'set': True, 'useDefault': True})
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertDictEqual(json.loads(
            resp.content.decode(Code.UTF_8)), dict(code=Code.OK))
        resp = self.client.post(
            follow=True, path=root(url.auth.GETSUCCESSOR))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertDictEqual(json.loads(resp.content.decode(
            Code.UTF_8)), dict(code=Code.OK, successorID=str()))

    @tag("aga")
    def _test_successorInvitation(self):
        client2 = Client()
        E2 = getTestEmail()
        P2 = getTestPassword()
        client2.post(follow=True, path=authroot(url.auth.SIGNUP), data=dict(
            email=E2,
            first_name=getTestName(),
            password1=P2
        ))
        EmailAddress.objects.filter(email=E2).update(verified=True)
        client2.post(follow=True, path=authroot(url.auth.LOGIN), data=dict(
            email=E2,
            password=P2
        ))
        resp = client2.post(follow=True, path=root(url.auth.INVITESUCCESSOR), data={
                           'set': True, 'userID': self.user.email})
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        print(resp.content)
        self.assertDictEqual(json.loads(
            resp.content.decode(Code.UTF_8)), dict(code=Code.OK))
        profile = Profile.objects.get(
            user__email=E2, successor_confirmed=False, successor=self.user)
        self.assertIsInstance(profile, Profile)

        resp = self.client.get(follow=True, path=root(
            url.auth.successorInvite(profile.getUserID())))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.index)
        self.assertTemplateUsed(resp, template.invitation)
        self.assertTemplateUsed(resp, template.auth.invitation)
        self.assertIsInstance(resp.context['predecessor'], User)
        self.assertEqual(resp.context['predecessor'], profile.user)

    def _test_successorInviteAction(self):
        client = Client()
        E2 = getTestEmail()
        P2 = getTestPassword()
        client.post(follow=True, path=authroot(url.auth.SIGNUP), data=dict(
            email=E2,
            first_name=getTestName(),
            password1=P2
        ))
        EmailAddress.objects.filter(email=E2).update(verified=True)
        client.post(follow=True, path=authroot(url.auth.LOGIN), data=dict(
            email=E2,
            password=P2
        ))
        resp = client.post(follow=True, path=root(url.auth.INVITESUCCESSOR), data={
                           'set': True, 'userID': self.user.email})
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertDictEqual(json.loads(
            resp.content.decode(Code.UTF_8)), dict(code=Code.OK))
        profile = Profile.objects.get(
            user__email=E2, successor_confirmed=False, successor=self.user)
        self.assertIsInstance(profile, Profile)

        resp = self.client.get(follow=True, path=root(
            url.auth.successorInvite(profile.getUserID())))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.index)
        self.assertTemplateUsed(resp, template.invitation)
        self.assertTemplateUsed(resp, template.auth.invitation)
        self.assertIsInstance(resp.context['predecessor'], User)
        self.assertEqual(resp.context['predecessor'], profile.user)

        resp = self.client.post(follow=True, path=root(
            url.auth.successorInviteAction(Action.DECLINE)))
        self.assertEqual(resp.status_code, HttpResponseForbidden.status_code)
        resp = self.client.post(follow=True, path=root(url.auth.successorInviteAction(Action.DECLINE)), data={
            'predID': self.botuser.getID()
        })
        self.assertEqual(resp.status_code, HttpResponseForbidden.status_code)

        resp = self.client.post(follow=True, path=root(url.auth.successorInviteAction(Action.DECLINE)), data={
            'predID': profile.getUserID()
        })
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertIsInstance(Profile.objects.get(
            user__email=E2, successor_confirmed=False, successor=None), Profile)
        self.assertTemplateUsed(resp, template.index)
        self.assertTemplateUsed(resp, template.people.index)
        self.assertTemplateUsed(resp, template.people.profile)

        resp = client.post(follow=True, path=root(url.auth.INVITESUCCESSOR), data={
                           'set': True, 'userID': self.user.email})
        self.assertEqual(resp.status_code, HttpResponse.status_code)

        resp = self.client.post(follow=True, path=root(url.auth.successorInviteAction(Action.ACCEPT)), data={
            'predID': profile.getUserID()
        })
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertIsInstance(Profile.objects.get(
            user__email=E2, successor_confirmed=True, successor=self.user), Profile)
        self.assertTemplateUsed(resp, template.index)
        self.assertTemplateUsed(resp, template.people.index)
        self.assertTemplateUsed(resp, template.people.profile)

        resp = client.post(follow=True, path=root(
            url.auth.INVITESUCCESSOR), data={'unset': True})
        self.assertEqual(resp.status_code, HttpResponse.status_code)

        resp = client.post(follow=True, path=root(url.auth.INVITESUCCESSOR), data={
                           'set': True, 'userID': self.user.email})
        self.assertEqual(resp.status_code, HttpResponse.status_code)

        profile.to_be_zombie = True
        profile.save()

        resp = self.client.post(follow=True, path=root(url.auth.successorInviteAction(Action.ACCEPT)), data={
            'predID': profile.getUserID()
        })
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        with self.assertRaises(ObjectDoesNotExist):
            User.objects.get(email=E2)

    def _test_accountDelete(self):
        clientx = Client()
        E2 = getTestEmail()
        P2 = getTestPassword()
        clientx.post(follow=True, path=authroot(url.auth.SIGNUP), data=dict(
            email=E2,
            first_name=getTestName(),
            password1=P2
        ))
        EmailAddress.objects.filter(email=E2).update(verified=True)
        clientx.post(follow=True, path=authroot(url.auth.LOGIN), data=dict(
            email=E2,
            password=P2
        ))
        resp = clientx.post(follow=True, path=root(url.auth.ACCOUNTDELETE))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertDictEqual(json.loads(
            resp.content.decode(Code.UTF_8)), dict(code=Code.NO))

        resp = clientx.post(follow=True, path=root(
            url.auth.ACCOUNTDELETE), data={'confirmed': True})
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertDictEqual(json.loads(resp.content.decode(
            Code.UTF_8)), dict(code=Code.NO, error=Message.SUCCESSOR_UNSET))

        resp = clientx.post(follow=True, path=root(url.auth.INVITESUCCESSOR),
                           data={'useDefault': True, 'set': True})
        self.assertEqual(resp.status_code, HttpResponse.status_code)

        resp = clientx.post(follow=True, path=root(
            url.auth.ACCOUNTDELETE), data={'confirmed': True})
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertDictEqual(json.loads(resp.content.decode(
            Code.UTF_8)), dict(code=Code.OK, message=Message.ACCOUNT_DELETED))
        with self.assertRaises(ObjectDoesNotExist):
            User.objects.get(email=E2)
