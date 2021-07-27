from datetime import timedelta
from django.test import TestCase, tag
from django.utils import timezone
from main.strings import Code
from people.models import User
from moderation.methods import requestModerationForObject
from people.tests.utils import getTestUsersInst, getTestTopicsInst
from compete.models import *
from .utils import TEST_COMP_TITLE, TEST_COMP_PERKS, TEST_BANNER, getSubmissionRepos
from random import randint


@tag(Code.Test.MODEL, APPNAME)
class CompetitionTest(TestCase):
    def test_comp_creation_pass(self):
        comp = Competition.objects.create(title=TEST_COMP_TITLE)
        self.assertIsNotNone(comp.title)


@tag(Code.Test.MODEL, APPNAME)
class CompetitionM2MTest(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.comp = Competition.objects.create(title=TEST_COMP_TITLE)
        users = User.objects.bulk_create(getTestUsersInst(3))
        profiles = []
        for user in users:
            profiles.append(Profile(
                user=user
            ))
        Profile.objects.bulk_create(profiles)
        cls.judges = Profile.objects.filter(user__in=users)
        cls.topics = Topic.objects.bulk_create(getTestTopicsInst(4))

    def test_comp_assign_judges(self):
        for judge in self.judges:
            self.comp.judges.add(judge)
        count = CompetitionJudge.objects.filter(competition=self.comp).count()
        self.assertEqual(count, len(self.judges))

    def test_comp_unassign_judges(self):
        CompetitionJudge.objects.filter(competition=self.comp).delete()
        comp = Competition.objects.get(id=self.comp.getID())
        self.assertEqual(comp.judges.count(), 0)

    def test_comp_assign_topics(self):
        for topic in self.topics:
            self.comp.topics.add(topic)
        count = CompetitionTopic.objects.filter(competition=self.comp).count()
        self.assertEqual(count, len(self.topics))

    def test_comp_unassign_topics(self):
        CompetitionTopic.objects.filter(competition=self.comp).delete()
        comp = Competition.objects.get(id=self.comp.getID())
        self.assertEqual(comp.topics.count(), 0)


@tag(Code.Test.MODEL, APPNAME)
class CompetitionAttributeTest(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.comp = Competition.objects.create(
            title=TEST_COMP_TITLE, endAt=timezone.now()+timedelta(days=3))

    def test_default_comp_methods(self):
        self.assertTrue(competeBannerPath(self.comp, TEST_BANNER).__contains__(self.comp.getID()))
        self.assertEqual(self.comp.__str__(), self.comp.title)
        self.assertEqual(self.comp.getID(), self.comp.id.hex)
        self.assertTrue(self.comp.getBanner().endswith(str(self.comp.banner)))
        self.assertTrue(self.comp.getLink().endswith(self.comp.getID()))
        self.assertTrue(self.comp.participationLink().endswith(url.compete.participate(compID=self.comp.getID())))
        self.assertTrue(self.comp.isActive())
        self.assertFalse(self.comp.isUpcoming())
        self.assertFalse(self.comp.isHistory())
        self.assertAlmostEqual(
            self.comp.secondsLeft(), self.comp.secondsLeft(), delta=3)
        self.assertCountEqual(self.comp.getTopics(), [])
        self.assertCountEqual(self.comp.getPerks(), [])
        self.assertEqual(self.comp.totalTopics(), 0)
        self.assertFalse(self.comp.isModerator(profile=None))
        self.assertIsNone(self.comp.getModerator())
        self.assertFalse(self.comp.moderated())
        self.assertFalse(self.comp.isJudge(profile=None))
        self.assertCountEqual(self.comp.getJudges(), [])
        self.assertEqual(self.comp.totalJudges(), 0)
        self.assertEqual(self.comp.getJudgementLink(), '')
        self.assertFalse(self.comp.isParticipant(profile=None))
        self.assertEqual(self.comp.getMaxScore(), 0)
        self.assertCountEqual(self.comp.getSubmissions(), [])
        self.assertEqual(self.comp.totalSubmissions(), 0)
        self.assertCountEqual(self.comp.getValidSubmissions(), [])
        self.assertTrue(self.comp.submissionPointsLink().endswith(
            url.compete.submitPoints(compID=self.comp.getID())))
        self.assertFalse(self.comp.allSubmissionsMarkedByJudge(judge=None))
        self.assertFalse(self.comp.allSubmissionsMarked())
        self.assertEqual(self.comp.countJudgesWhoMarkedSubmissions(), 0)
        self.assertTrue(self.comp.declareResultsLink().endswith(
            url.compete.declareResults(compID=self.comp.getID())))
        self.assertFalse(self.comp.declareResults())
        self.assertCountEqual(self.comp.getParticipants(),[])
        self.assertEqual(self.comp.totalParticipants(),0)
        self.assertCountEqual(self.comp.getAllParticipants(),[])
        self.assertEqual(self.comp.totalAllParticipants(),0)


    @tag("mod")
    def test_modified_comp_methods(self):
        self.comp.endAt = timezone.now()
        self.comp.perks = TEST_COMP_PERKS
        self.judges = None
        self.comp.save()
        self.assertEqual(self.comp.secondsLeft(), 0)
        self.assertCountEqual(self.comp.getPerks(), TEST_COMP_PERKS.split(';'))
        users = User.objects.bulk_create(getTestUsersInst(3))
        Profile.objects.create(user=users[0],is_moderator=True)
        requestModerationForObject(self.comp,APPNAME)
        self.assertTrue(self.comp.isModerator(self.comp.getModerator()))
        Moderation.objects.filter(type=APPNAME, competition=self.comp).update(resolved=True)
        self.assertTrue(self.comp.moderated())
        judge = Profile.objects.create(user=users[1])
        self.assertFalse(self.comp.isJudge(profile=judge))
        self.comp.judges.add(judge)
        self.assertTrue(self.comp.isJudge(profile=judge))
        subm = Submission.objects.create(competition=self.comp)
        participant = Profile.objects.create(user=users[2])
        subm.members.add(participant)
        self.assertTrue(self.comp.isParticipant(profile=participant))
        topic = Topic.objects.bulk_create(getTestTopicsInst())[0]
        self.comp.topics.add(topic)
        SubmissionTopicPoint.objects.create(submission=subm,judge=judge,topic=topic)
        self.assertTrue(self.comp.allSubmissionsMarkedByJudge(judge=judge))
        self.assertEqual(self.comp.countJudgesWhoMarkedSubmissions(), 1)    

@tag(Code.Test.MODEL, APPNAME)
class CompetitionJudgeAttributeTest(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.comp = Competition.objects.create(
            title=TEST_COMP_TITLE, endAt=timezone.now()+timedelta(days=3))
        users = User.objects.bulk_create(getTestUsersInst())
        judge = Profile.objects.create(user=users[0])
        cls.comp.judges.add(judge)
        cls.compjudge = CompetitionJudge.objects.get(
            competition=cls.comp, judge=judge)

    def test_comp_judge_methods(self):
        self.assertEqual(self.compjudge.__str__(), self.comp.title)


@tag(Code.Test.MODEL, APPNAME)
class CompetitionTopicAttributeTest(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.comp = Competition.objects.create(
            title=TEST_COMP_TITLE, endAt=timezone.now()+timedelta(days=3))
        topic = Topic.objects.bulk_create(getTestTopicsInst())[0]
        cls.comp.topics.add(topic)
        cls.comptopic = CompetitionTopic.objects.get(
            competition=cls.comp, topic=topic)

    def test_comp_topic_methods(self):
        self.assertEqual(self.comptopic.__str__(), self.comp.title)


@tag(Code.Test.MODEL, APPNAME)
class SubmissionTest(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.comp = Competition.objects.create(title=TEST_COMP_TITLE)
        cls.topics = Topic.objects.bulk_create(getTestTopicsInst(4))
        users = User.objects.bulk_create(getTestUsersInst(54))
        profiles = []
        for user in users:
            profiles.append(Profile(
                user=user
            ))
        Profile.objects.bulk_create(profiles)
        cls.judges = Profile.objects.filter(user__in=users)[0:3]
        for judge in cls.judges:
            cls.comp.judges.add(judge)
        cls.users = Profile.objects.filter(user__in=users)[3:54]

    def test_submission_creation(self):
        submissions = []
        i = 0
        for repo in getSubmissionRepos(len(self.users)):
            submissions.append(Submission(
                competition=self.comp,
                repo=repo
            ))
            i += 1
        subs = Submission.objects.bulk_create(submissions)
        s = 0
        for sub in Submission.objects.filter(competition=self.comp):
            sub.members.add(self.users[s])
            s += 1

        self.assertEqual(len(subs), len(self.users))
        count = SubmissionParticipant.objects.filter(
            submission__competition=self.comp, profile__in=self.judges).count()
        self.assertEqual(count, 0)
        count = Submission.objects.filter(
            competition=self.comp, submitted=False, valid=False).count()
        self.assertEqual(count, 0)
        count = Submission.objects.filter(
            competition=self.comp, submitted=True).count()
        self.assertEqual(count, 0)
        count = Submission.objects.filter(
            competition=self.comp, late=True).count()
        self.assertEqual(count, 0)
        count = Submission.objects.filter(
            competition=self.comp, submitted=False, late=True).count()
        self.assertEqual(count, 0)

    def test_submission_invalidation(self):
        submissions = []
        i = 0
        for repo in getSubmissionRepos(len(self.users)):
            submissions.append(Submission(
                competition=self.comp,
                repo=repo,
            ))
            i += 1
        subs = Submission.objects.bulk_create(submissions)
        s = 0
        for sub in Submission.objects.filter(competition=self.comp):
            sub.members.add(self.users[s])
            s += 1
        Submission.objects.filter(
            competition=self.comp, repo__endswith='0').update(valid=False)
        comp = Competition.objects.get(id=self.comp.getID())
        self.assertNotEquals(comp.totalValidSubmissions(
        ), Submission.objects.filter(competition=self.comp).count())


@tag(Code.Test.MODEL, APPNAME)
class SubmissionM2MTest(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.comp = Competition.objects.create(title=TEST_COMP_TITLE)
        cls.topics = Topic.objects.bulk_create(getTestTopicsInst(4))
        for topic in cls.topics:
            cls.comp.topics.add(topic)
        users = User.objects.bulk_create(getTestUsersInst(54))
        profiles = []
        for user in users:
            profiles.append(Profile(
                user=user
            ))
        Profile.objects.bulk_create(profiles)
        cls.judges = Profile.objects.filter(user__in=users)[0:3]
        for judge in cls.judges:
            cls.comp.judges.add(judge)
        cls.users = Profile.objects.filter(user__in=users)[3:54]
        submissions = []
        i = 0
        for repo in getSubmissionRepos(len(cls.users)):
            submissions.append(Submission(
                competition=cls.comp,
                repo=repo
            ))
            i += 1
        cls.subs = Submission.objects.bulk_create(submissions)
        s = 0
        for sub in Submission.objects.filter(competition=cls.comp):
            sub.members.add(cls.users[s])
            s += 1

    def test_submission_members(self):
        s = 0
        for sub in self.subs:
            sub.members.remove(self.users[s+3])
            self.assertEqual(SubmissionParticipant.objects.filter(
                submission=sub, profile=self.users[s+3]).count(), 0)


@tag(Code.Test.MODEL, APPNAME)
class SubmissionAttributeTest(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.comp = Competition.objects.create(title=TEST_COMP_TITLE)
        cls.topics = Topic.objects.bulk_create(getTestTopicsInst(4))
        users = User.objects.bulk_create(getTestUsersInst(2))
        cls.subm = Submission.objects.create(competition=cls.comp)
        cls.firstmem = Profile.objects.create(user=users[0])
        cls.subm.members.add(cls.firstmem)
        SubmissionParticipant.objects.filter(
            submission=cls.subm, profile=cls.firstmem).update(confirmed=True)
        cls.invitee = Profile.objects.create(user=users[1])

    def test_new_subm_methods(self):
        self.assertEqual(self.subm.__str__(),
                         f"{self.comp.title} - {self.subm.getID()}")
        self.assertEqual(self.subm.getID(), self.subm.id.hex)
        self.assertEqual(self.subm.getCompID(), self.subm.competition.getID())
        self.assertTrue(self.subm.saveLink().endswith(url.compete.save(
            compID=self.subm.getCompID(), subID=self.subm.getID())))
        self.assertEqual(self.subm.totalMembers(), 1)
        self.assertTrue(self.subm.isMember(profile=self.firstmem))
        self.assertCountEqual(self.subm.getMembers(), self.subm.members.all())
        self.assertCountEqual(self.subm.getMembersEmail(), [
                              self.firstmem.getEmail()])
        self.assertEqual(self.subm.totalActiveMembers(), 1)
        self.assertEqual(self.subm.memberOrMembers(), 'member')
        self.assertFalse(self.subm.isInvitee(self.firstmem))
        self.assertCountEqual(self.subm.getInvitees(), [])
        self.assertTrue(self.subm.canInvite())
        self.assertEqual(self.subm.getRepo(), '')
        self.assertFalse(self.subm.submittingLate())
        self.assertEqual(self.subm.pointedTopicsByJudge(judge=None), 0)

    def test_modified_subm_methods(self):
        self.subm.members.add(self.invitee)
        self.assertFalse(self.subm.isMember(profile=self.invitee))
        self.assertTrue(self.subm.isInvitee(profile=self.invitee))
        self.assertCountEqual(self.subm.getInvitees(),[self.invitee])
        


@tag(Code.Test.MODEL, APPNAME)
class SubmissionTopicPointTest(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.comp = Competition.objects.create(title=TEST_COMP_TITLE)
        cls.topics = Topic.objects.bulk_create(getTestTopicsInst(4))
        for topic in cls.topics:
            cls.comp.topics.add(topic)

        users = User.objects.bulk_create(getTestUsersInst(54))
        profiles = []
        for user in users:
            profiles.append(Profile(
                user=user
            ))
        Profile.objects.bulk_create(profiles)
        cls.judges = Profile.objects.filter(user__in=users)[0:3]
        for judge in cls.judges:
            cls.comp.judges.add(judge)
        cls.users = Profile.objects.filter(user__in=users)[3:54]
        submissions = []
        i = 0
        for repo in getSubmissionRepos(len(cls.users)):
            submissions.append(Submission(
                competition=cls.comp,
                repo=repo
            ))
            i += 1
        cls.subs = Submission.objects.bulk_create(submissions)

    def test_assign_topic_point(self):
        topicpoints = []
        for judge in self.judges:
            for topic in self.topics:
                for sub in self.subs:
                    topicpoints.append(SubmissionTopicPoint(
                        submission=sub,
                        judge=judge,
                        topic=topic,
                        points=randint(0, self.comp.eachTopicMaxPoint)
                    ))

        subpoints = SubmissionTopicPoint.objects.bulk_create(topicpoints)
        self.assertEqual(len(subpoints), self.comp.totalValidSubmissions(
        )*self.comp.totalTopics()*self.comp.totalJudges())
        self.assertTrue(self.comp.allSubmissionsMarked())


@tag(Code.Test.MODEL, APPNAME)
class SubmissionTopicPointAttributeTest(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.comp = Competition.objects.create(title=TEST_COMP_TITLE)
        cls.topic = Topic.objects.bulk_create(getTestTopicsInst())[0]
        cls.comp.topics.add(cls.topic)

        users = User.objects.bulk_create(getTestUsersInst(2))
        profiles = []
        for user in users:
            profiles.append(Profile(
                user=user
            ))
        Profile.objects.bulk_create(profiles)
        cls.judge = Profile.objects.filter(user__in=users)[0:1][0]
        cls.comp.judges.add(cls.judge)
        cls.user = Profile.objects.filter(user__in=users)[1:2][0]
        cls.subm = Submission.objects.create(competition=cls.comp, repo=getSubmissionRepos()[
                                             0], submitted=True, submitOn=timezone.now())
        cls.submTopicPoint = SubmissionTopicPoint.objects.create(
            submission=cls.subm, judge=cls.judge, topic=cls.topic, points=randint(0, cls.comp.eachTopicMaxPoint))

    def test_default_submtoppoint_method(self):
        self.assertEqual(self.submTopicPoint.__str__(), self.subm.getID())


@tag(Code.Test.MODEL, APPNAME)
class ResultTest(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.comp = Competition.objects.create(title=TEST_COMP_TITLE)
        cls.topics = Topic.objects.bulk_create(getTestTopicsInst(4))
        for topic in cls.topics:
            cls.comp.topics.add(topic)

        users = User.objects.bulk_create(getTestUsersInst(54))
        profiles = []
        for user in users:
            profiles.append(Profile(
                user=user
            ))
        Profile.objects.bulk_create(profiles)
        cls.judges = Profile.objects.filter(user__in=users)[0:3]
        for judge in cls.judges:
            cls.comp.judges.add(judge)
        cls.users = Profile.objects.filter(user__in=users)[3:54]

        for repo in getSubmissionRepos(len(cls.users)):
            Submission.objects.create(competition=cls.comp,
                                      repo=repo,
                                      submitted=True,
                                      submitOn=timezone.now())

        cls.subs = Submission.objects.filter(competition=cls.comp)
        s = 0
        for sub in Submission.objects.filter(competition=cls.comp):
            sub.members.add(cls.users[s])
            s += 1
        topicpoints = []
        for judge in cls.judges:
            for topic in cls.topics:
                for sub in cls.subs:
                    topicpoints.append(SubmissionTopicPoint(
                        submission=sub,
                        topic=topic,
                        judge=judge,
                        points=randint(0, 10)
                    ))
        SubmissionTopicPoint.objects.bulk_create(topicpoints)

    def test_comp_results(self):
        done = self.comp.declareResults()
        self.assertIsNotNone(done)
        self.assertIsInstance(done, Competition)
        self.assertTrue(self.comp.resultDeclared)
        results = Result.objects.filter(competition=self.comp).order_by('rank')
        self.assertEqual(results.count(), len(self.subs))
        self.assertEqual(results.first().rank, 1)
        prevrank = 0
        prevpoint = 0
        for res in results:
            self.assertEqual(res.rank, prevrank+1)
            self.assertTrue(res.points <= (
                prevpoint if prevpoint != 0 else res.points))
            prevrank += 1
            prevpoint = res.points


@tag(Code.Test.MODEL, APPNAME)
class ResultAttributeTest(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.comp = Competition.objects.create(title=TEST_COMP_TITLE)
        cls.topic = Topic.objects.bulk_create(getTestTopicsInst())[0]
        cls.comp.topics.add(cls.topic)
        users = User.objects.bulk_create(getTestUsersInst(2))
        profiles = []
        for user in users:
            profiles.append(Profile(
                user=user
            ))
        Profile.objects.bulk_create(profiles)
        cls.judge = Profile.objects.filter(user__in=users)[0:1][0]
        cls.comp.judges.add(cls.judge)
        cls.user = Profile.objects.filter(user__in=users)[1:2][0]
        now = timezone.now()
        cls.subm = Submission.objects.create(
            competition=cls.comp, repo=getSubmissionRepos()[0], submitted=True, submitOn=now)
        cls.submTopicPoint = SubmissionTopicPoint.objects.create(
            submission=cls.subm, judge=cls.judge, topic=cls.topic, points=randint(0, cls.comp.eachTopicMaxPoint))
        cls.comp.declareResults()
        cls.result = Result.objects.get(
            competition=cls.comp, submission=cls.subm)

    def test_result_methods(self):
        self.assertEqual(self.result.__str__(
        ), f"{self.comp} - {self.result.rank}{self.result.rankSuptext()}")
        self.assertEqual(self.result.submitOn(), self.result.submission.submitOn)
        self.assertEqual(self.result.rankSuptext(),self.result.rankSuptext(rnk=1))
        self.assertEqual(self.result.rankSuptext(rnk=2),self.result.rankSuptext(rnk=22))
        self.assertEqual(self.result.rankSuptext(rnk=1),self.result.rankSuptext(rnk=21))
        self.assertEqual(self.result.rankSuptext(rnk=3),self.result.rankSuptext(rnk=23))
        self.assertEqual(self.result.rankSuptext(rnk=4),self.result.rankSuptext(rnk=24))
        self.assertEqual(self.result.rankSuptext(rnk=5),self.result.rankSuptext(rnk=20))
