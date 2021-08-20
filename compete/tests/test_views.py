from django.http.response import HttpResponseNotFound
from django.core.exceptions import ObjectDoesNotExist
from datetime import timedelta
from django.utils import timezone
import json
from django.test import TestCase, Client, tag
from django.http import HttpResponse
from main.strings import Code, url, template, Message, Action
from main.tests.utils import getRandomStr
from people.tests.utils import getTestEmail, getTestName, getTestPassword
from people.models import Profile
from moderation.methods import requestModerationForObject
from .utils import getCompTitle, root
from compete.methods import *


@tag(Code.Test.VIEW, APPNAME)
class TestViews(TestCase):
    @classmethod
    def setUpTestData(self) -> None:
        self.email = getTestEmail()
        self.password = getTestPassword()
        self.user = User.objects.create_user(email=self.email, password=self.password, first_name=getTestName())
        self.profile = Profile.objects.get(user=self.user)
        self.judgeemail = getTestEmail()
        self.judgepassword = getTestPassword()
        self.judgeuser = User.objects.create_user(email=self.judgeemail, password=self.judgepassword, first_name=getTestName())
        self.judgeprofile = Profile.objects.get(user=self.judgeuser)
        self.modemail = getTestEmail()
        self.modpassword = getTestPassword()
        self.moduser = User.objects.create_user(email=self.modemail, password=self.modpassword, first_name=getTestName())
        self.modprofile = Profile.objects.get(user=self.moduser)
        self.modprofile.is_moderator = True
        self.modprofile.save()
        self.mgemail = getTestEmail()
        self.mgpassword = getTestPassword()
        self.mguser = User.objects.create_user(email=self.mgemail, password=self.mgpassword, first_name=getTestName())
        self.mgprofile = Profile.objects.get(user=self.mguser)
        self.mgprofile.is_manager = True
        self.mgprofile.save()
        self.comp = Competition.objects.create(title=getCompTitle(),creator=self.mgprofile,endAt=timezone.now()+timedelta(days=3))
        requestModerationForObject(self.comp,APPNAME)
        self.comp.judges.add(self.judgeprofile)
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

    def test_competition(self):
        resp = self.client.get(root(url.compete.compID(getRandomStr())))
        self.assertEqual(resp.status_code, HttpResponseNotFound.status_code)

        resp = self.client.get(root(url.compete.compID(self.comp.getID())))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.index)
        self.assertTemplateUsed(resp, template.compete.index)
        self.assertTemplateUsed(resp, template.compete.profile)
        self.assertEqual(resp.context['compete'], self.comp)

        self.client.login(email=self.mgemail,password=self.mgpassword)
        resp = self.client.get(root(url.compete.compID(self.comp.getID())))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.compete.profile)
        self.assertEqual(resp.context['compete'], self.comp)
        self.assertFalse(resp.context['isJudge'])
        self.assertFalse(resp.context['isMod'])
        self.assertTrue(resp.context['isManager'])
        self.client.logout()

        self.client.login(email=self.modemail,password=self.modpassword)
        resp = self.client.get(root(url.compete.compID(self.comp.getID())))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.compete.profile)
        self.assertEqual(resp.context['compete'], self.comp)
        self.assertFalse(resp.context['isJudge'])
        self.assertTrue(resp.context['isMod'])
        self.assertFalse(resp.context['isManager'])
        self.client.logout()

        self.client.login(email=self.judgeemail,password=self.judgepassword)
        resp = self.client.get(root(url.compete.compID(self.comp.getID())))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.compete.profile)
        self.assertEqual(resp.context['compete'], self.comp)
        self.assertTrue(resp.context['isJudge'])
        self.assertFalse(resp.context['isMod'])
        self.assertFalse(resp.context['isManager'])
        self.client.logout()
    
    def test_data(self):
        resp = self.client.post(root(url.compete.data(getRandomStr())))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertDictEqual(json.loads(resp.content.decode('utf-8')), dict(code=Code.NO))

        resp = self.client.post(root(url.compete.data(self.comp.getID())))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertEqual(json.loads(resp.content.decode('utf-8'))['code'],Code.OK)
        self.assertTrue(json.loads(resp.content.decode('utf-8'))['timeleft'] - self.comp.secondsLeft() < 1)

        self.client.login(email=self.email,password=self.password)
        resp = self.client.post(root(url.compete.data(self.comp.getID())))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertEqual(json.loads(resp.content.decode('utf-8'))['code'],Code.OK)
        self.assertTrue(json.loads(resp.content.decode('utf-8'))['timeleft'] - self.comp.secondsLeft() < 1)
        self.assertFalse(json.loads(resp.content.decode('utf-8'))['participated'])

        subm = Submission.objects.create(competition=self.comp)
        subm.members.add(self.profile)
        SubmissionParticipant.objects.filter(submission=subm,profile=self.profile).update(confirmed=True)
        resp = self.client.post(root(url.compete.data(self.comp.getID())))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertEqual(json.loads(resp.content.decode('utf-8'))['code'],Code.OK)
        self.assertTrue(json.loads(resp.content.decode('utf-8'))['timeleft'] - self.comp.secondsLeft() < 1)
        self.assertTrue(json.loads(resp.content.decode('utf-8'))['participated'])
        self.assertEqual(json.loads(resp.content.decode('utf-8'))['subID'], subm.getID())
        subm.delete()
        self.client.logout()
    
    def test_competitionTab(self):
        resp = self.client.get(root(url.compete.competeTabSection(self.comp.getID(),Compete.OVERVIEW)))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.compete.profile_overview)
        self.assertEqual(resp.context['compete'], self.comp)
        resp = self.client.get(root(url.compete.competeTabSection(self.comp.getID(),Compete.TASK)))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.compete.profile_task)
        self.assertEqual(resp.context['compete'], self.comp)
        resp = self.client.get(root(url.compete.competeTabSection(self.comp.getID(),Compete.GUIDELINES)))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.compete.profile_guidelines)
        self.assertEqual(resp.context['compete'], self.comp)
        resp = self.client.get(root(url.compete.competeTabSection(self.comp.getID(),Compete.SUBMISSION)))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.compete.profile_submission)
        self.assertEqual(resp.context['compete'], self.comp)
        self.assertIsNone(resp.context['submission'])
        resp = self.client.get(root(url.compete.competeTabSection(self.comp.getID(),Compete.RESULT)))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.compete.profile_result)
        self.assertEqual(resp.context['compete'], self.comp)
        self.assertIsNone(resp.context['results'])

        subm = Submission.objects.create(competition=self.comp)
        subm.members.add(self.profile)
        SubmissionParticipant.objects.filter(submission=subm,profile=self.profile).update(confirmed=True)
        self.client.login(email=self.email,password=self.password)
        resp = self.client.get(root(url.compete.competeTabSection(self.comp.getID(),Compete.SUBMISSION)))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.compete.profile_submission)
        self.assertEqual(resp.context['compete'], self.comp)
        self.assertIsInstance(resp.context['submission'], Submission)
        self.assertTrue(resp.context['confirmed'])
        resp = self.client.get(root(url.compete.competeTabSection(self.comp.getID(),Compete.RESULT)))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.compete.profile_result)
        self.assertEqual(resp.context['compete'], self.comp)
        self.assertIsNone(resp.context['results'])
        subm.delete()
        self.client.logout()

    
    def test_createSubmission(self):
        self.client.login(email=self.email,password=self.password)
        resp = self.client.post(root(url.compete.participate(self.comp.getID())),follow=True)
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertIsInstance(SubmissionParticipant.objects.get(submission__competition=self.comp,profile=self.profile,confirmed=True),SubmissionParticipant)
        self.assertTemplateUsed(resp, template.compete.profile)

        resp = self.client.post(root(url.compete.participate(self.comp.getID())),follow=True)
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertEqual(SubmissionParticipant.objects.filter(submission__competition=self.comp,profile=self.profile,confirmed=True).count(),1)
        self.assertTemplateUsed(resp, template.compete.profile)


        comp = Competition.objects.create(title=getCompTitle(),creator=self.mgprofile,endAt=timezone.now()+timedelta(days=2))
        resp = self.client.post(root(url.compete.participate(comp.getID())),follow=True)
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertIsInstance(SubmissionParticipant.objects.get(submission__competition=comp,profile=self.profile,confirmed=True),SubmissionParticipant)
        self.assertTemplateUsed(resp, template.compete.profile)
        resp = self.client.post(root(url.compete.participate(comp.getID())),follow=True)
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertEqual(SubmissionParticipant.objects.filter(submission__competition=comp,profile=self.profile,confirmed=True).count(),1)
        self.assertTemplateUsed(resp, template.compete.profile)
        
        comp = Competition.objects.create(title=getCompTitle(),creator=self.mgprofile,endAt=timezone.now())
        resp = self.client.post(root(url.compete.participate(comp.getID())),follow=True)
        self.assertEqual(resp.status_code, HttpResponseNotFound.status_code)
        with self.assertRaises(ObjectDoesNotExist):
            SubmissionParticipant.objects.get(submission__competition=comp,profile=self.profile,confirmed=True)
        Submission.objects.filter(competition=self.comp).delete()
        self.client.logout()
        
    
    def test_invite(self):
        self.client.login(email=self.email,password=self.password)
        resp = self.client.post(root(url.compete.participate(self.comp.getID())),follow=True)
        self.assertEqual(resp.status_code, HttpResponse.status_code)

        resp = self.client.post(root(url.compete.data(self.comp.getID())))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        subID = json.loads(resp.content.decode('utf-8'))['subID']

        resp = self.client.post(root(url.compete.invite(subID)),follow=True)
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertDictEqual(json.loads(resp.content.decode('utf-8')), dict(code=Code.NO,error=Message.INVALID_ID))

        E2 = getTestEmail()
        P2 = getTestPassword()
        user = User.objects.create_user(email=E2, password=P2, first_name=getTestName())
        resp = self.client.post(root(url.compete.invite(subID)),{
            'userID':user.email,
        },follow=True)
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertDictEqual(json.loads(resp.content.decode('utf-8')), dict(code=Code.OK))
        self.assertIsInstance(SubmissionParticipant.objects.get(submission=subID,profile=user.profile,confirmed=False),SubmissionParticipant)
        self.assertEqual(SubmissionParticipant.objects.filter(submission__id=subID).count(),2)
        Submission.objects.filter(competition=self.comp).delete()

    def test_invitation(self):
        self.client.login(email=self.email,password=self.password)
        resp = self.client.post(root(url.compete.participate(self.comp.getID())),follow=True)
        self.assertEqual(resp.status_code, HttpResponse.status_code)

        resp = self.client.post(root(url.compete.data(self.comp.getID())))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        subID = json.loads(resp.content.decode('utf-8'))['subID']

        E2 = getTestEmail()
        P2 = getTestPassword()
        user = User.objects.create_user(email=E2, password=P2, first_name=getTestName())
        resp = self.client.post(root(url.compete.invite(subID)),{
            'userID':user.email,
        },follow=True)
        self.assertEqual(resp.status_code, HttpResponse.status_code)

        client = Client()
        self.assertTrue(client.login(email=E2,password=P2))
        resp = client.get(root(url.compete.invitation(getRandomStr(),self.user.getID())),follow=True)
        self.assertEqual(resp.status_code, HttpResponseNotFound.status_code)
        resp = client.get(root(url.compete.invitation(subID,user.getID())),follow=True)
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.index)
        self.assertTemplateUsed(resp, template.invitation)
        self.assertIsInstance(resp.context['submission'], Submission)
        
    def test_inviteAction(self):
        self.client.login(email=self.email,password=self.password)
        resp = self.client.post(root(url.compete.participate(self.comp.getID())),follow=True)
        self.assertEqual(resp.status_code, HttpResponse.status_code)

        resp = self.client.post(root(url.compete.data(self.comp.getID())))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        subID = json.loads(resp.content.decode('utf-8'))['subID']

        E2 = getTestEmail()
        P2 = getTestPassword()
        user = User.objects.create_user(email=E2, password=P2, first_name=getTestName())
        resp = self.client.post(root(url.compete.invite(subID)),{
            'userID':user.email,
        },follow=True)
        self.assertEqual(resp.status_code, HttpResponse.status_code)

        client = Client()
        self.assertTrue(client.login(email=E2,password=P2))
        resp = client.get(root(url.compete.invitation(subID,user.getID())),follow=True)
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.invitation)

        resp = client.post(root(url.compete.inviteAction(subID,user.getID(),getRandomStr())),follow=True)
        self.assertEqual(resp.status_code, HttpResponseNotFound.status_code)

        resp = client.post(root(url.compete.inviteAction(subID,user.getID(),Action.DECLINE)),follow=True)
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.invitation)
        self.assertIsInstance(resp.context['submission'], Submission)
        self.assertTrue(resp.context['declined'])
        self.assertEqual(SubmissionParticipant.objects.filter(submission__id=subID,confirmed=True).count(),1)

        resp = self.client.post(root(url.compete.invite(subID)),{
            'userID':user.email,
        },follow=True)
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertEqual(SubmissionParticipant.objects.filter(submission__id=subID,confirmed=False).count(),1)

        resp = client.post(root(url.compete.inviteAction(subID,user.getID(),Action.ACCEPT)),follow=True)
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.invitation)
        self.assertIsInstance(resp.context['submission'], Submission)
        self.assertTrue(resp.context['accepted'])
        self.assertEqual(SubmissionParticipant.objects.filter(submission__id=subID,confirmed=True).count(),2)
        Submission.objects.filter(competition=self.comp).delete()

    def test_removeMember(self):
        self.client.login(email=self.email,password=self.password)
        resp = self.client.post(root(url.compete.participate(self.comp.getID())),follow=True)
        self.assertEqual(resp.status_code, HttpResponse.status_code)

        resp = self.client.post(root(url.compete.data(self.comp.getID())))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        subID = json.loads(resp.content.decode('utf-8'))['subID']

        E2 = getTestEmail()
        P2 = getTestPassword()
        user = User.objects.create_user(email=E2, password=P2, first_name=getTestName())
        resp = self.client.post(root(url.compete.invite(subID)),{
            'userID':user.email,
        },follow=True)
        self.assertEqual(resp.status_code, HttpResponse.status_code)

        resp = self.client.post(root(url.compete.removeMember(getRandomStr(),self.user.getID())))
        self.assertEqual(resp.status_code, HttpResponseNotFound.status_code)
        
        resp = self.client.post(root(url.compete.removeMember(subID,user.getID())),follow=True)
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertEqual(SubmissionParticipant.objects.filter(submission__id=subID,confirmed=False).count(),0)
        self.assertTemplateUsed(resp, template.compete.profile)

        resp = self.client.post(root(url.compete.invite(subID)),{
            'userID':user.email,
        },follow=True)
        self.assertEqual(resp.status_code, HttpResponse.status_code)

        client = Client()
        self.assertTrue(client.login(email=E2,password=P2))
        resp = client.get(root(url.compete.invitation(subID,user.getID())),follow=True)
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.invitation)

        resp = client.post(root(url.compete.inviteAction(subID,user.getID(),Action.ACCEPT)),follow=True)
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.invitation)
        self.assertIsInstance(resp.context['submission'], Submission)
        self.assertTrue(resp.context['accepted'])

        resp = self.client.post(root(url.compete.removeMember(subID,user.getID())),follow=True)
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertEqual(SubmissionParticipant.objects.filter(submission__id=subID).count(),1)
        self.assertTemplateUsed(resp, template.compete.profile)

        resp = self.client.post(root(url.compete.invite(subID)),{
            'userID':user.email,
        },follow=True)
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertEqual(SubmissionParticipant.objects.filter(submission__id=subID,confirmed=False).count(),1)

        resp = client.post(root(url.compete.inviteAction(subID,user.getID(),Action.ACCEPT)),follow=True)
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.invitation)
        self.assertIsInstance(resp.context['submission'], Submission)
        self.assertTrue(resp.context['accepted'])

        resp = self.client.post(root(url.compete.removeMember(subID,self.user.getID())),follow=True)
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertEqual(SubmissionParticipant.objects.filter(submission__id=subID).count(),1)
        self.assertIsInstance(SubmissionParticipant.objects.get(submission__id=subID,profile=user.profile),SubmissionParticipant)
        self.assertTemplateUsed(resp, template.compete.profile)

        resp = client.post(root(url.compete.invite(subID)),{
            'userID':self.user.email,
        },follow=True)
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertEqual(SubmissionParticipant.objects.filter(submission__id=subID,confirmed=False).count(),1)
        
        resp = client.post(root(url.compete.removeMember(subID,user.getID())),follow=True)
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.compete.profile)
        with self.assertRaises(ObjectDoesNotExist):
            Submission.objects.get(id=subID)

        Submission.objects.filter(competition=self.comp).delete()

    