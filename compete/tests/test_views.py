from json import loads as json_loads
from django.db.models import Sum
from compete.models import ParticipantCertificate, SubmissionTopicPoint
from django.http.response import HttpResponseNotFound, HttpResponseForbidden
from django.contrib.auth.hashers import make_password
from allauth.account.models import EmailAddress
from django.core.exceptions import ObjectDoesNotExist
from datetime import timedelta
from django.utils import timezone
from random import randint
from django.test import TestCase, Client, tag
from django.http import HttpResponse
from main.env import BOTMAIL
from main.strings import Code, url, template, Message, Action
from main.tests.utils import authroot, getRandomStr
from auth2.tests.utils import getTestEmail, getTestName, getTestPassword, getTestPasswords, getTestEmails, getTestNames
from people.tests.utils import getTestTopicsInst
from people.models import Profile, ProfileTopic, Topic
from moderation.models import Moderation
from moderation.methods import assignModeratorToObject, requestModerationForObject
from .utils import getCompTitle, root, getTestUrl
from compete.methods import *


@tag(Code.Test.VIEW, APPNAME)
class TestViews(TestCase):
    @classmethod
    def setUpTestData(self) -> None:
        self.bot, _ = User.objects.get_or_create(email=BOTMAIL, defaults=dict(
            first_name='knottersbot', email=BOTMAIL, password=getTestPassword()))
        self.email = getTestEmail()
        self.password = getTestPassword()
        self.user = User.objects.create_user(
            email=self.email, password=self.password, first_name=getTestName())
        self.profile = Profile.objects.get(user=self.user)
        self.judgeemail = getTestEmail()
        self.judgepassword = getTestPassword()
        self.judgeuser = User.objects.create_user(
            email=self.judgeemail, password=self.judgepassword, first_name=getTestName())
        self.judgeprofile = Profile.objects.get(user=self.judgeuser)
        self.modemail = getTestEmail()
        self.modpassword = getTestPassword()
        self.moduser = User.objects.create_user(
            email=self.modemail, password=self.modpassword, first_name=getTestName())
        self.modprofile = Profile.objects.get(user=self.moduser)
        self.modprofile.is_moderator = True
        self.modprofile.save()
        self.mgemail = getTestEmail()
        self.mgpassword = getTestPassword()
        self.mguser = User.objects.create_user(
            email=self.mgemail, password=self.mgpassword, first_name=getTestName())
        self.mgprofile = Profile.objects.get(user=self.mguser)
        self.mgprofile.convertToManagement()
        self.mgprofile.save()
        self.comp = Competition.objects.create(title=getCompTitle(
        ), creator=self.mgprofile, endAt=timezone.now()+timedelta(days=3), eachTopicMaxPoint=30)
        assignModeratorToObject(APPNAME, self.comp, self.modprofile)
        # requestModerationForObject(self.comp, APPNAME)
        self.comp.judges.add(self.judgeprofile)
        self.client = Client()
        self.topics = Topic.objects.bulk_create(getTestTopicsInst(5))
        for top in self.topics:
            self.comp.topics.add(top)
        mailaddrs = []
        for u in [self.mguser, self.moduser, self.judgeuser, self.user]:
            mailaddrs.append(EmailAddress(
                user=u,
                email=u.email,
                primary=True,
                verified=True
            ))
        EmailAddress.objects.bulk_create(mailaddrs)
        return super().setUpTestData()

    def test_index(self):
        response = self.client.get(follow=True, path=root(appendslash=True))
        self.assertEqual(response.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(response, template.index)
        self.assertTemplateUsed(response, template.compete.index)

    def test_indexTab(self):
        response = self.client.get(follow=True, path=root(
            url.compete.indexTab(tab=Compete.ACTIVE)))
        self.assertEqual(response.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(response, template.compete.active)

        response = self.client.get(follow=True, path=root(
            url.compete.indexTab(tab=Compete.UPCOMING)))
        self.assertEqual(response.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(response, template.compete.upcoming)

        response = self.client.get(follow=True, path=root(
            url.compete.indexTab(tab=Compete.HISTORY)))
        self.assertEqual(response.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(response, template.compete.history)

    @tag('afm')
    def test_competition(self):
        resp = self.client.get(follow=True, path=root(
            url.compete.compID(getRandomStr())))
        self.assertEqual(resp.status_code, HttpResponseNotFound.status_code)

        resp = self.client.get(follow=True, path=root(
            url.compete.compID(self.comp.getID())))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.index)
        self.assertTemplateUsed(resp, template.compete.index)
        self.assertTemplateUsed(resp, template.compete.profile)
        self.assertEqual(resp.context['compete'], self.comp)

        self.client.login(email=self.mgemail, password=self.mgpassword)
        resp = self.client.get(follow=True, path=root(
            url.compete.compID(self.comp.getID())))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.compete.profile)
        self.assertEqual(resp.context['compete'], self.comp)
        self.assertFalse(resp.context['isJudge'])
        self.assertFalse(resp.context['isMod'])
        self.assertTrue(resp.context['isManager'])
        self.client.logout()

        self.client.login(email=self.modemail, password=self.modpassword)
        resp = self.client.get(follow=True, path=root(
            url.compete.compID(self.comp.getID())))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.compete.profile)
        self.assertEqual(resp.context['compete'], self.comp)
        self.assertFalse(resp.context['isJudge'])
        self.assertTrue(resp.context['isMod'])
        self.assertFalse(resp.context['isManager'])
        self.client.logout()

        self.client.login(email=self.judgeemail, password=self.judgepassword)
        resp = self.client.get(follow=True, path=root(
            url.compete.compID(self.comp.getID())))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.compete.profile)
        self.assertEqual(resp.context['compete'], self.comp)
        self.assertTrue(resp.context['isJudge'])
        self.assertFalse(resp.context['isMod'])
        self.assertFalse(resp.context['isManager'])
        self.client.logout()

    def test_data(self):
        resp = self.client.post(follow=True, path=root(
            url.compete.data(getRandomStr())))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertDictEqual(json_loads(
            resp.content.decode(Code.UTF_8)), dict(code=Code.NO))

        resp = self.client.post(follow=True, path=root(
            url.compete.data(self.comp.getID())))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertEqual(json_loads(
            resp.content.decode(Code.UTF_8))['code'], Code.OK)
        self.assertTrue(json_loads(resp.content.decode(Code.UTF_8))[
                        'timeleft'] >= self.comp.secondsLeft())

        self.client.login(email=self.email, password=self.password)
        resp = self.client.post(follow=True, path=root(
            url.compete.data(self.comp.getID())))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertEqual(json_loads(
            resp.content.decode(Code.UTF_8))['code'], Code.OK)
        self.assertTrue(json_loads(resp.content.decode(Code.UTF_8))[
                        'timeleft'] >= self.comp.secondsLeft())
        self.assertFalse(json_loads(
            resp.content.decode(Code.UTF_8))['participated'])

        subm = Submission.objects.create(competition=self.comp)
        subm.members.add(self.profile)
        SubmissionParticipant.objects.filter(
            submission=subm, profile=self.profile).update(confirmed=True)
        resp = self.client.post(follow=True, path=root(
            url.compete.data(self.comp.getID())))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertEqual(json_loads(
            resp.content.decode(Code.UTF_8))['code'], Code.OK)
        self.assertTrue(json_loads(resp.content.decode(Code.UTF_8))[
                        'timeleft'] >= self.comp.secondsLeft())
        self.assertTrue(json_loads(
            resp.content.decode(Code.UTF_8))['participated'])
        self.assertEqual(json_loads(resp.content.decode(Code.UTF_8))
                         ['subID'], subm.getID())
        subm.delete()
        self.client.logout()

    def test_competitionTab(self):
        resp = self.client.get(follow=True, path=root(
            url.compete.competeTabSection(self.comp.getID(), Compete.OVERVIEW)))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.compete.profile_overview)
        self.assertEqual(resp.context['compete'], self.comp)
        resp = self.client.get(follow=True, path=root(
            url.compete.competeTabSection(self.comp.getID(), Compete.TASK)))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.compete.profile_task)
        self.assertEqual(resp.context['compete'], self.comp)
        resp = self.client.get(follow=True, path=root(url.compete.competeTabSection(
            self.comp.getID(), Compete.GUIDELINES)))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.compete.profile_guidelines)
        self.assertEqual(resp.context['compete'], self.comp)
        resp = self.client.get(follow=True, path=root(url.compete.competeTabSection(
            self.comp.getID(), Compete.SUBMISSION)))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.compete.profile_submission)
        self.assertEqual(resp.context['compete'], self.comp)
        self.assertIsNone(resp.context['submission'])
        resp = self.client.get(follow=True, path=root(
            url.compete.competeTabSection(self.comp.getID(), Compete.RESULT)))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.compete.profile_result)
        self.assertEqual(resp.context['compete'], self.comp)
        self.assertIsNone(resp.context['results'])

        subm = Submission.objects.create(competition=self.comp)
        subm.members.add(self.profile)
        SubmissionParticipant.objects.filter(
            submission=subm, profile=self.profile).update(confirmed=True)
        self.client.login(email=self.email, password=self.password)
        resp = self.client.get(follow=True, path=root(url.compete.competeTabSection(
            self.comp.getID(), Compete.SUBMISSION)))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.compete.profile_submission)
        self.assertEqual(resp.context['compete'], self.comp)
        self.assertIsInstance(resp.context['submission'], Submission)
        self.assertTrue(resp.context['confirmed'])
        resp = self.client.get(follow=True, path=root(
            url.compete.competeTabSection(self.comp.getID(), Compete.RESULT)))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.compete.profile_result)
        self.assertEqual(resp.context['compete'], self.comp)
        self.assertIsNone(resp.context['results'])
        subm.delete()
        self.client.logout()

    def test_createSubmission(self):
        self.client.login(email=self.email, password=self.password)
        resp = self.client.post(follow=True, path=root(
            url.compete.participate(self.comp.getID())))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertIsInstance(SubmissionParticipant.objects.get(
            submission__competition=self.comp, profile=self.profile, confirmed=True), SubmissionParticipant)
        self.assertTemplateUsed(resp, template.compete.profile)

        resp = self.client.post(follow=True, path=root(
            url.compete.participate(self.comp.getID())))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertEqual(SubmissionParticipant.objects.filter(
            submission__competition=self.comp, profile=self.profile, confirmed=True).count(), 1)
        self.assertTemplateUsed(resp, template.compete.profile)

        comp = Competition.objects.create(title=getCompTitle(
        ), creator=self.mgprofile, endAt=timezone.now()+timedelta(days=2))
        resp = self.client.post(follow=True, path=root(
            url.compete.participate(comp.getID())))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertIsInstance(SubmissionParticipant.objects.get(
            submission__competition=comp, profile=self.profile, confirmed=True), SubmissionParticipant)
        self.assertTemplateUsed(resp, template.compete.profile)
        resp = self.client.post(follow=True, path=root(
            url.compete.participate(comp.getID())))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertEqual(SubmissionParticipant.objects.filter(
            submission__competition=comp, profile=self.profile, confirmed=True).count(), 1)
        self.assertTemplateUsed(resp, template.compete.profile)

        comp = Competition.objects.create(
            title=getCompTitle(), creator=self.mgprofile, endAt=timezone.now())
        resp = self.client.post(follow=True, path=root(
            url.compete.participate(comp.getID())))
        self.assertEqual(resp.status_code, HttpResponseNotFound.status_code)
        with self.assertRaises(ObjectDoesNotExist):
            SubmissionParticipant.objects.get(
                submission__competition=comp, profile=self.profile, confirmed=True)
        Submission.objects.filter(competition=self.comp).delete()
        self.client.logout()

    @tag("tg")
    def test_invite(self):
        user = User.objects.create_user(email=getTestEmail(
        ), password=getTestPassword(), first_name=getTestName())
        P2 = getTestPassword()
        user2 = User.objects.create_user(
            email=getTestEmail(), password=P2, first_name=getTestName())
        EmailAddress.objects.create(
            user=user, email=user.email, primary=True, verified=True)
        EmailAddress.objects.create(
            user=user2, email=user2.email, primary=True, verified=True)

        self.client.login(email=self.email, password=self.password)
        resp = self.client.post(follow=True, path=root(
            url.compete.participate(self.comp.getID())))
        self.assertEqual(resp.status_code, HttpResponse.status_code)

        resp = self.client.post(follow=True, path=root(
            url.compete.data(self.comp.getID())))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        subID = json_loads(resp.content.decode(Code.UTF_8))['subID']

        resp = self.client.post(
            follow=True, path=root(url.compete.invite(subID)))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertDictEqual(json_loads(resp.content.decode(
            Code.UTF_8)), dict(code=Code.NO, error=Message.INVALID_ID))

        resp = self.client.post(follow=True, path=root(url.compete.invite(subID)), data={
            'userID': user.email,
        })
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertDictEqual(json_loads(
            resp.content.decode(Code.UTF_8)), dict(code=Code.OK))
        self.assertIsInstance(SubmissionParticipant.objects.get(
            submission=subID, profile=user.profile, confirmed=False), SubmissionParticipant)
        self.assertEqual(SubmissionParticipant.objects.filter(
            submission__id=subID).count(), 2)

        client2 = Client()
        client2.login(email=user2.email, password=P2)
        resp = client2.post(follow=True, path=root(
            url.compete.participate(self.comp.getID())))
        self.assertEqual(resp.status_code, HttpResponse.status_code)

        resp = client2.post(follow=True, path=root(
            url.compete.data(self.comp.getID())))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        subID2 = json_loads(resp.content.decode(Code.UTF_8))['subID']

        resp = client2.post(follow=True, path=root(url.compete.invite(subID2)), data={
            'userID': user.email,
        })
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertDictEqual(json_loads(resp.content.decode(
            Code.UTF_8)), dict(code=Code.NO, error=Message.USER_PARTICIPANT_OR_INVITED))

        comp2 = Competition.objects.create(title=getCompTitle(
        ), creator=self.mgprofile, endAt=timezone.now()+timedelta(days=2))
        resp = client2.post(follow=True, path=root(
            url.compete.participate(comp2.getID())))
        self.assertEqual(resp.status_code, HttpResponse.status_code)

        resp = client2.post(follow=True, path=root(
            url.compete.data(comp2.getID())))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        subID21 = json_loads(resp.content.decode(Code.UTF_8))['subID']
        resp = client2.post(follow=True, path=root(url.compete.invite(subID21)), data={
            'userID': user.email,
        })
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertDictEqual(json_loads(
            resp.content.decode(Code.UTF_8)), dict(code=Code.OK))
        self.assertIsInstance(SubmissionParticipant.objects.get(
            submission=subID21, profile=user.profile, confirmed=False), SubmissionParticipant)
        self.assertEqual(SubmissionParticipant.objects.filter(
            submission__id=subID21).count(), 2)

        Submission.objects.filter(competition=self.comp).delete()

    def test_invitation(self):
        P2 = getTestPassword()
        user = User.objects.create_user(
            email=getTestEmail(), password=P2, first_name=getTestName())
        EmailAddress.objects.create(
            user=user, email=user.email, primary=True, verified=True)
        self.client.login(email=self.email, password=self.password)
        resp = self.client.post(follow=True, path=root(
            url.compete.participate(self.comp.getID())))
        self.assertEqual(resp.status_code, HttpResponse.status_code)

        resp = self.client.post(follow=True, path=root(
            url.compete.data(self.comp.getID())))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        subID = json_loads(resp.content.decode(Code.UTF_8))['subID']

        resp = self.client.post(follow=True, path=root(url.compete.invite(subID)), data={
            'userID': user.email,
        })
        self.assertEqual(resp.status_code, HttpResponse.status_code)

        client = Client()
        self.assertTrue(client.login(email=user.email, password=P2))
        resp = client.get(follow=True, path=root(url.compete.invitation(
            getRandomStr(), self.user.getID())))
        self.assertEqual(resp.status_code, HttpResponseNotFound.status_code)

        resp = client.get(follow=True, path=root(url.compete.invitation(
            subID, user.getID())))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.index)
        self.assertTemplateUsed(resp, template.invitation)
        self.assertTemplateUsed(resp, template.compete.invitation)
        self.assertIsInstance(resp.context['submission'], Submission)

    def test_inviteAction(self):
        P2 = getTestPassword()
        user = User.objects.create_user(
            email=getTestEmail(), password=P2, first_name=getTestName())
        EmailAddress.objects.create(
            user=user, email=user.email, primary=True, verified=True)
        self.client.login(email=self.email, password=self.password)
        resp = self.client.post(follow=True, path=root(
            url.compete.participate(self.comp.getID())))
        self.assertEqual(resp.status_code, HttpResponse.status_code)

        resp = self.client.post(follow=True, path=root(
            url.compete.data(self.comp.getID())))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        subID = json_loads(resp.content.decode(Code.UTF_8))['subID']

        resp = self.client.post(follow=True, path=root(url.compete.invite(subID)), data={
            'userID': user.email,
        })
        self.assertEqual(resp.status_code, HttpResponse.status_code)

        client = Client()
        self.assertTrue(client.login(email=user.email, password=P2))
        resp = client.get(follow=True, path=root(url.compete.invitation(
            subID, user.getID())))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.invitation)
        self.assertTemplateUsed(resp, template.compete.invitation)

        resp = client.post(follow=True, path=root(url.compete.inviteAction(
            subID, user.getID(), getRandomStr())))
        self.assertEqual(resp.status_code, HttpResponseNotFound.status_code)

        resp = client.post(follow=True, path=root(url.compete.inviteAction(
            subID, user.getID(), Action.DECLINE)))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.invitation)
        self.assertTemplateUsed(resp, template.compete.invitation)
        self.assertIsInstance(resp.context['submission'], Submission)
        self.assertTrue(resp.context['declined'])
        self.assertEqual(SubmissionParticipant.objects.filter(
            submission__id=subID, confirmed=True).count(), 1)

        resp = self.client.post(follow=True, path=root(url.compete.invite(subID)), data={
            'userID': user.email,
        })
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertEqual(SubmissionParticipant.objects.filter(
            submission__id=subID, confirmed=False).count(), 1)

        resp = client.post(follow=True, path=root(url.compete.inviteAction(
            subID, user.getID(), Action.ACCEPT)))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.invitation)
        self.assertTemplateUsed(resp, template.compete.invitation)
        self.assertIsInstance(resp.context['submission'], Submission)
        self.assertTrue(resp.context['accepted'])
        self.assertEqual(SubmissionParticipant.objects.filter(
            submission__id=subID, confirmed=True).count(), 2)
        Submission.objects.filter(competition=self.comp).delete()

    def test_removeMember(self):
        P2 = getTestPassword()
        user = User.objects.create_user(
            email=getTestEmail(), password=P2, first_name=getTestName())
        EmailAddress.objects.create(
            user=user, email=user.email, primary=True, verified=True)
        self.client.login(email=self.email, password=self.password)
        resp = self.client.post(follow=True, path=root(
            url.compete.participate(self.comp.getID())))
        self.assertEqual(resp.status_code, HttpResponse.status_code)

        resp = self.client.post(follow=True, path=root(
            url.compete.data(self.comp.getID())))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        subID = json_loads(resp.content.decode(Code.UTF_8))['subID']

        resp = self.client.post(follow=True, path=root(url.compete.invite(subID)), data={
            'userID': user.email,
        })
        self.assertEqual(resp.status_code, HttpResponse.status_code)

        resp = self.client.post(follow=True, path=root(
            url.compete.removeMember(getRandomStr(), self.user.getID())))
        self.assertEqual(resp.status_code, HttpResponseNotFound.status_code)

        resp = self.client.post(follow=True, path=root(
            url.compete.removeMember(subID, user.getID())))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertEqual(SubmissionParticipant.objects.filter(
            submission__id=subID, confirmed=False).count(), 0)
        self.assertTemplateUsed(resp, template.compete.profile)

        resp = self.client.post(follow=True, path=root(url.compete.invite(subID)), data={
            'userID': user.email,
        })
        self.assertEqual(resp.status_code, HttpResponse.status_code)

        client = Client()
        self.assertTrue(client.login(email=user.email, password=P2))
        resp = client.get(follow=True, path=root(url.compete.invitation(
            subID, user.getID())))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.invitation)
        self.assertTemplateUsed(resp, template.compete.invitation)

        resp = client.post(follow=True, path=root(url.compete.inviteAction(
            subID, user.getID(), Action.ACCEPT)))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.invitation)
        self.assertTemplateUsed(resp, template.compete.invitation)
        self.assertIsInstance(resp.context['submission'], Submission)
        self.assertTrue(resp.context['accepted'])

        resp = self.client.post(follow=True, path=root(
            url.compete.removeMember(subID, user.getID())))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertEqual(SubmissionParticipant.objects.filter(
            submission__id=subID).count(), 1)
        self.assertTemplateUsed(resp, template.compete.profile)

        resp = self.client.post(follow=True, path=root(url.compete.invite(subID)), data={
            'userID': user.email,
        })
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertEqual(SubmissionParticipant.objects.filter(
            submission__id=subID, confirmed=False).count(), 1)

        resp = client.post(follow=True, path=root(url.compete.inviteAction(
            subID, user.getID(), Action.ACCEPT)))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.invitation)
        self.assertTemplateUsed(resp, template.compete.invitation)
        self.assertIsInstance(resp.context['submission'], Submission)
        self.assertTrue(resp.context['accepted'])

        resp = self.client.post(follow=True, path=root(
            url.compete.removeMember(subID, self.user.getID())))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertEqual(SubmissionParticipant.objects.filter(
            submission__id=subID).count(), 1)
        self.assertIsInstance(SubmissionParticipant.objects.get(
            submission__id=subID, profile=user.profile), SubmissionParticipant)
        self.assertTemplateUsed(resp, template.compete.profile)

        resp = client.post(follow=True, path=root(url.compete.invite(subID)), data={
            'userID': self.user.email,
        })
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertEqual(SubmissionParticipant.objects.filter(
            submission__id=subID, confirmed=False).count(), 1)

        resp = client.post(follow=True, path=root(
            url.compete.removeMember(subID, user.getID())))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.compete.profile)
        with self.assertRaises(ObjectDoesNotExist):
            Submission.objects.get(id=subID)

        Submission.objects.filter(competition=self.comp).delete()

    def test_save(self):
        self.client.login(email=self.email, password=self.password)
        resp = self.client.post(follow=True, path=root(
            url.compete.participate(self.comp.getID())))
        self.assertEqual(resp.status_code, HttpResponse.status_code)

        resp = self.client.post(follow=True, path=root(
            url.compete.data(self.comp.getID())))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        subID = json_loads(resp.content.decode(Code.UTF_8))['subID']

        resp = self.client.post(follow=True, path=root(url.compete.save(self.comp.getID(), subID)), data={
            'submissionurl': getTestUrl()
        })
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.compete.profile)

        Submission.objects.filter(competition=self.comp).delete()

    def test_finalSubmit(self):
        self.client.login(email=self.email, password=self.password)
        resp = self.client.post(follow=True, path=root(
            url.compete.participate(self.comp.getID())))
        self.assertEqual(resp.status_code, HttpResponse.status_code)

        resp = self.client.post(follow=True, path=root(
            url.compete.data(self.comp.getID())))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        subID = json_loads(resp.content.decode(Code.UTF_8))['subID']

        resp = self.client.post(follow=True, path=root(
            url.compete.submit(self.comp.getID(), subID)))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertDictEqual(json_loads(resp.content.decode(
            Code.UTF_8)), dict(code=Code.OK, message=Message.SUBMITTED_SUCCESS))

        comp = Competition.objects.create(title=getCompTitle(
        ), creator=self.mgprofile, endAt=timezone.now()+timedelta(seconds=3))
        resp = self.client.post(follow=True, path=root(
            url.compete.participate(comp.getID())))
        self.assertEqual(resp.status_code, HttpResponse.status_code)

        resp = self.client.post(follow=True, path=root(
            url.compete.data(comp.getID())))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        subID = json_loads(resp.content.decode(Code.UTF_8))['subID']

        comp.endAt = timezone.now()
        comp.save()

        resp = self.client.post(follow=True, path=root(
            url.compete.submit(comp.getID(), subID)))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertDictEqual(json_loads(resp.content.decode(
            Code.UTF_8)), dict(code=Code.OK, message=Message.SUBMITTED_LATE))

        Submission.objects.filter(competition=self.comp).delete()

    def TestSubmitPoints(self):
        self.comp.judges.remove(self.judgeprofile)
        Submission.objects.exclude(competition__creator=self.mguser.profile).exclude(
            competition__creator=self.bot.profile).delete()
        Moderation.objects.filter(competition=self.comp).delete()
        Competition.objects.exclude(creator=self.mguser.profile).exclude(
            creator=self.bot.profile).delete()
        Profile.objects.exclude(user=self.mguser).exclude(
            user=self.bot).delete()
        User.objects.exclude(email=self.mgemail).exclude(
            id=self.bot.id).delete()

        totalusers = 10
        useremails = getTestEmails(totalusers)
        userpasswords = getTestPasswords(totalusers)
        usernames = getTestNames(totalusers)
        users = []
        for i in range(totalusers):
            users.append(
                User(
                    email=useremails[i],
                    first_name=usernames[i],
                    password=make_password(userpasswords[i], None, 'md5'), is_active=True
                )
            )
        users = User.objects.bulk_create(users)
        profiles = []
        for u in users:
            profiles.append(Profile(user=u))
        profiles = Profile.objects.bulk_create(profiles)
        i = -1
        for _ in profiles:
            i += 1
            client = Client()
            self.assertTrue(client.login(
                email=useremails[i], password=userpasswords[i]))
            resp = client.post(follow=True, path=root(
                url.compete.participate(self.comp.getID())))
            self.assertEqual(resp.status_code, HttpResponse.status_code)
            resp = client.post(follow=True, path=root(
                url.compete.data(self.comp.getID())))
            self.assertEqual(resp.status_code, HttpResponse.status_code)
            subID = json_loads(resp.content.decode(Code.UTF_8))['subID']
            resp = client.post(follow=True, path=root(url.compete.save(self.comp.getID(), subID)), data={
                'submissionurl': getTestUrl()
            })
            self.assertEqual(resp.status_code, HttpResponse.status_code)
            resp = client.post(follow=True, path=root(
                url.compete.submit(self.comp.getID(), subID)))
            self.assertEqual(resp.status_code, HttpResponse.status_code)
            self.assertDictEqual(json_loads(resp.content.decode(
                Code.UTF_8)), dict(code=Code.OK, message=Message.SUBMITTED_SUCCESS))

        modemail = getTestEmail()
        modpassword = getTestPassword()
        moduser = User.objects.create_user(
            email=modemail, password=modpassword, first_name=getTestName())
        EmailAddress.objects.create(
            user=moduser, email=moduser.email, primary=True, verified=True)
        Profile.objects.filter(user=moduser).update(is_moderator=True)

        requestModerationForObject(self.comp, APPNAME, reassignIfApproved=True)
        Moderation.objects.filter(
            type=APPNAME, competition=self.comp, moderator=moduser.profile).update(resolved=True)
        totaljudges = 5
        judgeemails = getTestEmails(totaljudges)
        judgepasswords = getTestPasswords(totaljudges)
        judgenames = getTestNames(totaljudges)
        judges = []
        for j in range(totaljudges):
            judges.append(
                User(
                    email=judgeemails[j],
                    first_name=judgenames[j],
                    password=make_password(judgepasswords[j], None, 'md5'), is_active=True
                )
            )
        judges = User.objects.bulk_create(judges)
        judgeprofiles = []
        for ju in judges:
            judgeprofiles.append(Profile(user=ju, is_mentor=True))
        judgeprofiles = Profile.objects.bulk_create(judgeprofiles)

        for judge in judgeprofiles:
            self.comp.judges.add(judge)

        self.comp.endAt = timezone.now()
        self.comp.save()

        j = -1
        for judge in judgeprofiles:
            j += 1
            client = Client()
            self.assertTrue(client.login(
                email=judgeemails[j], password=judgepasswords[j]))
            submissions = []
            for subm in self.comp.getValidSubmissions():
                topics = []
                for top in self.comp.getTopics():
                    topics.append({
                        'topicID': top.getID(),
                        'points': randint(0, self.comp.eachTopicMaxPoint)
                    })
                submissions.append({
                    'subID': subm.getID(),
                    'topics': topics
                })
            resp = client.post(follow=True, path=root(url.compete.submitPoints(self.comp.getID())), data={
                               "submissions": submissions}, content_type='application/json')
            self.assertEqual(resp.status_code, HttpResponse.status_code)
            self.assertDictEqual(json_loads(
                resp.content.decode(Code.UTF_8)), dict(code=Code.OK))
        self.assertEqual(SubmissionTopicPoint.objects.filter(submission__competition=self.comp).count(
        ), self.comp.totalValidSubmissions()*self.comp.totalJudges()*self.comp.totalTopics())
        for judge in judgeprofiles:
            self.assertTrue(self.comp.allSubmissionsMarkedByJudge(judge))
        self.assertTrue(self.comp.allSubmissionsMarked())
        return useremails, userpasswords, profiles

    def TestDeclareResults(self):
        useremails, userpasswords, profiles = self.TestSubmitPoints()
        client = Client()
        resp = client.post(follow=True, path=authroot(url.auth.LOGIN), data=dict(
            login=self.mgemail, password=self.mgpassword))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTrue(resp.context['user'].is_authenticated)
        resp = client.post(follow=True, path=root(
            url.compete.declareResults(self.comp.getID())))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.index)
        self.assertTemplateUsed(resp, template.management.index)
        self.assertTemplateUsed(resp, template.management.comp_index)
        self.assertTemplateUsed(resp, template.management.comp_compete)
        return useremails, userpasswords, profiles

    @tag('cxp')
    def test_claimXP(self):
        useremails, userpasswords, profiles = self.TestDeclareResults()
        self.comp.declareResults()
        ProfileTopic.objects.filter().delete()
        i = -1
        for profile in profiles:
            i += 1
            client = Client()
            self.assertTrue(client.login(
                email=useremails[i], password=userpasswords[i]))
            resp = client.post(follow=True, path=root(
                url.compete.data(self.comp.getID())))
            self.assertEqual(resp.status_code, HttpResponse.status_code)
            subID = json_loads(resp.content.decode(Code.UTF_8))['subID']
            resp = client.post(follow=True, path=root(
                url.compete.claimXP(self.comp.getID(), subID)))
            self.assertEqual(resp.status_code, HttpResponse.status_code)
            self.assertTemplateUsed(resp, template.compete.profile)
            self.assertEqual(
                resp.context['request'].GET['a'], Message.XP_ADDED)
            resp = client.post(follow=True, path=root(
                url.compete.claimXP(self.comp.getID(), subID)))
            self.assertEqual(resp.status_code,
                             HttpResponseNotFound.status_code)
            topicpoints = SubmissionTopicPoint.objects.filter(
                submission__id=subID).values('topic').annotate(points=Sum('points'))
            for top in topicpoints:
                self.assertTrue(ProfileTopic.objects.filter(
                    profile=profile, topic__id=top['topic'], points=top['points']).exists())

    @tag('cert')
    def _test_certificates(self):
        self.comp.judges.remove(self.judgeprofile)
        Submission.objects.filter(competition=self.comp).delete()
        Moderation.objects.filter(competition=self.comp).delete()
        Competition.objects.exclude(creator=self.mguser.profile).exclude(
            creator=self.bot.profile).delete()
        Profile.objects.exclude(user=self.mguser).exclude(
            user=self.bot).delete()
        User.objects.exclude(email=self.mgemail).exclude(
            id=self.bot.id).delete()

        totalusers = 10
        useremails = getTestEmails(totalusers)
        userpasswords = getTestPasswords(totalusers)
        usernames = getTestNames(totalusers)
        users = []
        for i in range(totalusers):
            users.append(
                User(
                    email=useremails[i],
                    first_name=usernames[i],
                    password=make_password(userpasswords[i], None, 'md5'), is_active=True
                )
            )
        users = User.objects.bulk_create(users)
        profiles = []
        for u in users:
            profiles.append(Profile(user=u))
        profiles = Profile.objects.bulk_create(profiles)
        i = -1
        for _ in profiles:
            i += 1
            client = Client()
            self.assertTrue(client.login(
                email=useremails[i], password=userpasswords[i]))
            resp = client.post(follow=True, path=root(
                url.compete.participate(self.comp.getID())))
            self.assertEqual(resp.status_code, HttpResponse.status_code)
            resp = client.post(follow=True, path=root(
                url.compete.data(self.comp.getID())))
            self.assertEqual(resp.status_code, HttpResponse.status_code)
            subID = json_loads(resp.content.decode(Code.UTF_8))['subID']
            resp = client.post(follow=True, path=root(url.compete.save(self.comp.getID(), subID)), data={
                'submissionurl': getTestUrl()
            })
            self.assertEqual(resp.status_code, HttpResponse.status_code)
            resp = client.post(follow=True, path=root(
                url.compete.submit(self.comp.getID(), subID)))
            self.assertEqual(resp.status_code, HttpResponse.status_code)
            self.assertDictEqual(json_loads(resp.content.decode(
                Code.UTF_8)), dict(code=Code.OK, message=Message.SUBMITTED_SUCCESS))

        modemail = getTestEmail()
        modpassword = getTestPassword()
        moduser = User.objects.create_user(
            email=modemail, password=modpassword, first_name=getTestName())
        EmailAddress.objects.create(
            user=moduser, email=moduser.email, primary=True, verified=True)
        Profile.objects.filter(user=moduser).update(is_moderator=True)

        requestModerationForObject(self.comp, APPNAME, reassignIfApproved=True)
        Moderation.objects.filter(
            type=APPNAME, competition=self.comp, moderator=moduser.profile).update(resolved=True)
        totaljudges = 5
        judgeemails = getTestEmails(totaljudges)
        judgepasswords = getTestPasswords(totaljudges)
        judgenames = getTestNames(totaljudges)
        judges = []
        for j in range(totaljudges):
            judges.append(
                User(
                    email=judgeemails[j],
                    first_name=judgenames[j],
                    password=make_password(judgepasswords[j], None, 'md5'), is_active=True
                )
            )
        judges = User.objects.bulk_create(judges)
        judgeprofiles = []
        for ju in judges:
            judgeprofiles.append(Profile(user=ju, is_mentor=True))
        judgeprofiles = Profile.objects.bulk_create(judgeprofiles)

        for judge in judgeprofiles:
            self.comp.judges.add(judge)

        self.comp.endAt = timezone.now()
        self.comp.save()

        j = -1
        for judge in judgeprofiles:
            j += 1
            client = Client()
            self.assertTrue(client.login(
                email=judgeemails[j], password=judgepasswords[j]))
            submissions = []
            for subm in self.comp.getValidSubmissions():
                topics = []
                for top in self.comp.getTopics():
                    topics.append({
                        'topicID': top.getID(),
                        'points': randint(0, self.comp.eachTopicMaxPoint)
                    })
                submissions.append({
                    'subID': subm.getID(),
                    'topics': topics
                })
            resp = client.post(follow=True, path=root(url.compete.submitPoints(self.comp.getID())), data={
                               "submissions": submissions}, content_type='application/json')
            self.assertEqual(resp.status_code, HttpResponse.status_code)
            self.assertDictEqual(json_loads(
                resp.content.decode(Code.UTF_8)), dict(code=Code.OK))
        self.assertTrue(self.comp.allSubmissionsMarked())

        mgclient = Client()
        resp = mgclient.post(follow=True, path=authroot(url.auth.LOGIN), data=dict(
            login=self.mgemail, password=self.mgpassword))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        # resp = mgclient.post(follow=True,path=
        #     root(url.compete.declareResults(self.comp.getID())))
        # self.assertEqual(resp.status_code, HttpResponse.status_code)
        # self.assertEqual(
        #     resp.context['request'].GET['a'], Message.RESULT_DECLARING)
        self.comp.declareResults()
        ProfileTopic.objects.filter().delete()
        i = -1
        for profile in profiles:
            i += 1
            for top in self.comp.getTopics():
                profile.topics.add(top)
            client = Client()
            self.assertTrue(client.login(
                email=useremails[i], password=userpasswords[i]))
            resp = client.post(follow=True, path=root(
                url.compete.data(self.comp.getID())))
            self.assertEqual(resp.status_code, HttpResponse.status_code)
            subID = json_loads(resp.content.decode(Code.UTF_8))['subID']
            result = Result.objects.get(
                competition=self.comp, submission__id=subID)
            resp = client.get(follow=True, path=root(
                url.compete.certificate(result.getID(), getRandomStr())))
            self.assertEqual(resp.status_code,
                             HttpResponseNotFound.status_code)
            resp = client.get(follow=True, path=root(url.compete.certificate(
                getRandomStr(), profile.getUserID())))
            self.assertEqual(resp.status_code,
                             HttpResponseNotFound.status_code)
            resp = client.get(follow=True, path=root(url.compete.certificate(
                result.getID(), profile.getUserID())))
            self.assertEqual(resp.status_code, HttpResponse.status_code)
            self.assertTemplateUsed(resp, template.index)
            self.assertTemplateUsed(resp, template.compete.index)
            self.assertTemplateUsed(resp, template.compete.certificate)
            self.assertEqual(resp.context['result'], result)
            self.assertEqual(resp.context['member'], profile)
            self.assertFalse(resp.context['certpath'])
            self.assertTrue(resp.context['self'])
            resp = Client().get(root(url.compete.certificate(result.getID(), profile.getUserID())))
            self.assertEqual(resp.status_code, HttpResponse.status_code)
            self.assertTemplateUsed(resp, template.compete.certificate)
            self.assertEqual(resp.context['result'], result)
            self.assertEqual(resp.context['member'], profile)
            self.assertFalse(resp.context['certpath'])
            self.assertFalse(resp.context['self'])

        self.assertFalse(self.comp.certificatesGenerated())
        resp = mgclient.post(follow=True, path=root(
            url.compete.generateCert(self.comp.getID())))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.management.comp_compete)
        self.assertEqual(
            resp.context['request'].GET['a'], Message.CERTS_GENERATING)
        self.assertEqual(ParticipantCertificate.objects.filter(
            result__competition=self.comp).count(), self.comp.totalValidSubmissionParticipants())
        self.assertTrue(self.comp.certificatesGenerated())
        resp = mgclient.post(follow=True, path=root(
            url.compete.generateCert(self.comp.getID())))
        self.assertEqual(resp.status_code, HttpResponseForbidden.status_code)

        i = -1
        for profile in profiles:
            i += 1
            client = Client()
            self.assertTrue(client.login(
                email=useremails[i], password=userpasswords[i]))
            resp = client.post(follow=True, path=root(
                url.compete.data(self.comp.getID())))
            self.assertEqual(resp.status_code, HttpResponse.status_code)
            subID = json_loads(resp.content.decode(Code.UTF_8))['subID']
            result = Result.objects.get(
                competition=self.comp, submission__id=subID)
            resp = client.get(follow=True, path=root(
                url.compete.certificate(result.getID(), profile.getUserID())))
            self.assertEqual(resp.status_code, HttpResponse.status_code)
            self.assertTemplateUsed(resp, template.compete.certificate)
            self.assertEqual(resp.context['result'], result)
            self.assertEqual(resp.context['member'], profile)
            self.assertTrue(len(resp.context['certpath']) > 0)
            self.assertTrue(resp.context['self'])
