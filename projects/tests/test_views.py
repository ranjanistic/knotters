from json import loads as json_loads

from allauth.account.models import EmailAddress
from auth2.tests.utils import (getTestEmail, getTestGHID, getTestName,
                               getTestPassword)
from django.db.models import QuerySet
from django.http import HttpResponse, HttpResponseNotAllowed
from django.http.response import HttpResponseNotFound, HttpResponseRedirect
from django.test import Client, TestCase, tag
from main.env import BOTMAIL
from main.strings import Action, Code, Message, template, url
from main.tests.utils import authroot, getRandomStr
from moderation.models import Moderation
from people.models import Profile, Topic, User
from people.tests.utils import getTestTopicsInst
from projects.apps import APPNAME
from projects.models import Category, FreeProject, License, Project, Tag, defaultImagePath
from projects.views import acceptTerms

from .utils import (getLicDesc, getLicName, getProjCategory, getProjDesc,
                    getProjName, getProjRepo, getTestTags, getTestTagsInst,
                    root)


@tag(Code.Test.VIEW, APPNAME)
class TestViews(TestCase):
    @classmethod
    def setUpTestData(self) -> None:
        self.bot, _ = User.objects.get_or_create(email=BOTMAIL, defaults=dict(
            first_name='knottersbot', email=BOTMAIL, password=getTestPassword()))
        Profile.KNOTBOT()
        self.client = Client()
        self.license = License.objects.create(
            name=getLicName(), description=getLicDesc(), creator=self.bot.profile, public=True)
        self.email = getTestEmail()
        self.ghID = getTestGHID()
        self.password = getTestPassword()
        self.user = User.objects.create_user(
            email=self.email, password=self.password, first_name=getTestName())
        self.profile = Profile.objects.get(user=self.user)
        self.moduser:User = User.objects.create_user(
            email=getTestEmail(), password=self.password, first_name=getTestName())
        self.modprofile = Profile.objects.get(user=self.moduser)
        self.modprofile.is_moderator = True
        self.modprofile.save()
        self.category = Category.objects.create(name=getProjCategory())
        self.license = License.objects.create(
            name=getLicName(), description=getLicDesc(), creator=self.bot.profile, public=True)
        EmailAddress.objects.get_or_create(
            user=self.user, email=self.email, verified=True, primary=True)
        return super().setUpTestData()

    def setUp(self) -> None:
        Profile.KNOTBOT()
        self.client = Client()
        return super().setUp()

    def test_index(self):
        resp = self.client.get(follow=True, path=root(''))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.index)
        self.assertTemplateUsed(resp, template.projects.index)

    def test_allLicenses(self):
        resp = self.client.get(
            follow=True, path=root(url.projects.ALLLICENSES))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertIsInstance(resp.context['licenses'], QuerySet)
        self.assertNotIsInstance(resp.context['custom'], QuerySet)
        self.assertTemplateUsed(resp, template.index)
        self.assertTemplateUsed(resp, template.projects.index)
        self.assertTemplateUsed(resp, template.projects.license_index)

    def test_license(self):
        resp = self.client.get(follow=True, path=root(
            url.projects.license(getRandomStr())))
        self.assertEqual(resp.status_code, HttpResponseNotFound.status_code)
        resp = self.client.get(follow=True, path=root(
            url.projects.license(self.license.getID())))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertIsInstance(resp.context['license'], License)
        self.assertTemplateUsed(resp, template.index)
        self.assertTemplateUsed(resp, template.projects.index)
        self.assertTemplateUsed(resp, template.projects.license_index)
        self.assertTemplateUsed(resp, template.projects.license_lic)

    def test_createMod(self):
        resp = self.client.get(path=root(url.projects.CREATE_MOD))
        self.assertEqual(resp.status_code, HttpResponseRedirect.status_code)
        resp = self.client.get(follow=True, path=root(url.projects.CREATE_MOD))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.auth.login)

        self.client.login(email=self.email, password=self.password)
        resp = self.client.get(follow=True, path=root(url.projects.CREATE_MOD))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertIsInstance(resp.context['categories'], QuerySet)
        self.assertIsInstance(resp.context['licenses'], QuerySet)
        self.assertTemplateUsed(resp, template.index)
        self.assertTemplateUsed(resp, template.projects.index)
        self.assertTemplateUsed(resp, template.projects.create)
        self.assertTemplateUsed(resp, template.projects.create_mod)

    def test_createFree(self):
        resp = self.client.get(path=root(url.projects.CREATE_FREE))
        self.assertEqual(resp.status_code, HttpResponseRedirect.status_code)
        resp = self.client.get(
            follow=True, path=root(url.projects.CREATE_FREE))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.auth.login)

        self.client.login(email=self.email, password=self.password)
        resp = self.client.get(
            follow=True, path=root(url.projects.CREATE_FREE))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertIsInstance(resp.context['categories'], QuerySet)
        self.assertIsInstance(resp.context['licenses'], QuerySet)
        self.assertTemplateUsed(resp, template.index)
        self.assertTemplateUsed(resp, template.projects.index)
        self.assertTemplateUsed(resp, template.projects.create)
        self.assertTemplateUsed(resp, template.projects.create_free)

    def test_validateField(self):
        self.client.login(email=self.email, password=self.password)
        resp = self.client.post(follow=True, path=root(
            url.projects.createValidField(getRandomStr())))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertDictEqual(json_loads(resp.content.decode(
            Code.UTF_8)), dict(code=Code.NO, error=Message.ERROR_OCCURRED))
        reponame = getRandomStr()
        resp = self.client.post(follow=True, path=root(url.projects.createValidField('reponame')), data={
            'reponame': reponame
        })
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertDictEqual(json_loads(resp.content.decode(
            Code.UTF_8)), dict(code=Code.NO, error=Message.Custom.already_exists(reponame)))

        resp = self.client.post(follow=True, path=root(url.projects.createValidField('reponame')), data={
            'reponame': getProjRepo()
        })
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertDictEqual(json_loads(
            resp.content.decode(Code.UTF_8)), dict(code=Code.OK))

    def test_licenses(self):
        self.client.login(email=self.email, password=self.password)
        resp = self.client.post(follow=True, path=root(url.projects.LICENSES))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertEqual(json_loads(
            resp.content.decode(Code.UTF_8))['code'], Code.OK)

    @tag('addlic')
    def test_addLicense(self):
        resp = self.client.post(path=root(url.projects.ADDLICENSE))
        self.assertEqual(resp.status_code, HttpResponseRedirect.status_code)

        self.client.login(email=self.email, password=self.password)
        resp = self.client.post(
            follow=True, path=root(url.projects.ADDLICENSE))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertDictEqual(json_loads(resp.content.decode(
            Code.UTF_8)), dict(code=Code.NO, error=Message.INVALID_REQUEST))

        licname = getLicName()
        resp = self.client.post(follow=True, path=root(url.projects.ADDLICENSE), data={
            "name": licname,
            "description": getLicDesc(),
            "content": getRandomStr(),
        })
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        license = License.objects.get(name=licname, creator=self.profile)
        self.assertDictEqual(json_loads(resp.content.decode(Code.UTF_8)), dict(code=Code.OK,
                             license=dict(id=license.getID(), name=license.name, description=license.description)))
    @tag('create')
    def _test_submitProject(self):
        resp = self.client.post(follow=True, path=root(url.projects.SUBMIT))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.auth.login)

        self.client.login(email=self.email, password=self.password)
        resp = self.client.post(follow=True, path=root(url.projects.SUBMIT))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.projects.create_mod)
        reponame = getProjRepo()
        categoryname = getProjCategory()
        data = {
            "projectname": getProjName(),
            "projectabout": getRandomStr(),
            "projectcategory": categoryname,
            "reponame": reponame,
            "description": getProjDesc(),
            "license": self.license.getID(),
        }
        resp = self.client.post(follow=True, path=root(
            url.projects.SUBMIT), data=data)
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.projects.create_mod)

        data["acceptterms"] = True
        resp = self.client.post(follow=True, path=root(
            url.projects.SUBMIT), data=data)
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.index)
        self.assertTemplateUsed(resp, template.moderation.index)
        self.assertTemplateUsed(resp, template.moderation.projects)
        project = Project.objects.get(
            reponame=reponame, status=Code.MODERATION)
        category = Category.objects.get(name=categoryname)
        self.assertTrue(project.acceptedTerms)
        self.assertEqual(project.creator, self.profile)
        self.assertEqual(project.moderator(), self.modprofile)
        self.assertEqual(project.category, category)
        self.assertEqual(str(project.image), defaultImagePath())
        self.assertIsNone(project.approvedOn)

    @tag('afag')
    def test_trashProject(self):
        project = Project.objects.create(name=getProjName(
        ), creator=self.profile, reponame=getProjRepo(), category=self.category, license=self.license)
        resp = self.client.post(follow=True, path=root(
            url.projects.trash(project.getID())))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.auth.login)

        self.client.login(email=self.email, password=self.password)
        resp = self.client.post(follow=True, path=root(
            url.projects.trash(project.getID())))
        # self.assertEqual(resp.status_code, HttpResponseNotFound.status_code)
        self.assertTrue(Project.objects.filter(id=project.id).exists())
        project.status = Code.REJECTED
        project.save()
        resp = self.client.post(follow=True, path=root(
            url.projects.trash(project.getID())))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertIsInstance(Project.objects.get(
            id=project.id, trashed=True), Project)
        self.assertTemplateUsed(resp, template.index)
        self.assertTemplateUsed(resp, template.people.index)
        self.assertTemplateUsed(resp, template.people.profile)

    def _test_profile(self):
        self.client.login(email=self.email, password=self.password)
        reponame = getProjRepo()
        resp = self.client.post(follow=True, path=root(url.projects.SUBMIT), data={
            "projectname": getProjName(),
            "projectabout": getRandomStr(),
            "reponame": reponame,
            "projectcategory": getProjCategory(),
            "description": getProjDesc(),
            "license": self.license.getID(),
            "tags": ",".join(getTestTags()),
            "acceptterms": True
        })
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.moderation.projects)

        resp = self.client.get(follow=True, path=root(
            url.projects.profile(getRandomStr())))
        self.assertEqual(resp.status_code, HttpResponseNotFound.status_code)

        project = Project.objects.get(reponame=reponame)

        self.client.logout()
        resp = self.client.get(follow=True, path=root(
            url.projects.profile(project.reponame)))
        self.assertEqual(resp.status_code, HttpResponseNotFound.status_code)

        self.client.login(email=self.email, password=self.password)
        resp = self.client.get(follow=True, path=root(
            url.projects.profile(project.reponame)))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.index)
        self.assertTemplateUsed(resp, template.moderation.index)
        self.assertTemplateUsed(resp, template.moderation.projects)

        mod = Moderation.objects.get(
            type=APPNAME, project=project, resolved=False)
        self.assertTrue(mod.approve())
        resp = self.client.get(follow=True, path=root(
            url.projects.profile(project.reponame)))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.index)
        self.assertTemplateUsed(resp, template.projects.index)
        self.assertTemplateUsed(resp, template.projects.profile)
        self.assertTrue(resp.context['iscreator'])
        self.assertFalse(resp.context['ismoderator'])
        self.assertEqual(resp.context['project'], project)

    def test_editProfile(self):
        project = Project.objects.create(name=getProjName(
        ), creator=self.profile, status=Code.APPROVED, reponame=getProjRepo(), category=self.category, license=self.license)
        resp = self.client.post(follow=True, path=root(url.projects.profileEdit(
            project.getID(), 'pallete')))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.auth.login)

        self.client.login(email=self.email, password=self.password)
        resp = self.client.post(follow=True, path=root(url.projects.profileEdit(project.getID(), 'pallete')), data={
            'projectname': getProjName(),
            'projectabout': getRandomStr()
        })
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        newproj = Project.objects.get(id=project.id)
        self.assertNotEqual(project.name, newproj.name)
        self.assertTemplateUsed(resp, template.index)
        self.assertTemplateUsed(resp, template.projects.index)
        self.assertTemplateUsed(resp, template.projects.profile)

    def test_topicsSearch(self):
        project = Project.objects.create(name=getProjName(
        ), creator=self.profile, status=Code.APPROVED, reponame=getProjRepo(), category=self.category, license=self.license)

        resp = self.client.post(follow=True, path=root(
            url.projects.topicsSearch(project.getID())))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.auth.login)

        self.client.login(email=self.email, password=self.password)
        resp = self.client.post(follow=True, path=root(
            url.projects.topicsSearch(project.getID())))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertDictEqual(json_loads(
            resp.content.decode(Code.UTF_8)), dict(code=Code.NO, error=Message.INVALID_REQUEST))

        resp = self.client.post(follow=True, path=root(url.projects.topicsSearch(project.getID())), data={
                                'query': getRandomStr()})
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertEqual(json_loads(
            resp.content.decode(Code.UTF_8))['code'], Code.OK)

    def test_topicsUpdate(self):
        project = Project.objects.create(name=getProjName(
        ), creator=self.profile, status=Code.APPROVED, reponame=getProjRepo(), category=self.category, license=self.license)
        resp = self.client.post(follow=True, path=root(url.projects.topicsUpdate(project.getID())), data={
                                'addtopicIDs': str()})
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.auth.login)

        self.client.login(email=self.email, password=self.password)
        topics = Topic.objects.bulk_create(getTestTopicsInst(4))
        addTopicIDs = ''
        for top in topics:
            addTopicIDs = f"{addTopicIDs},{top.getID()}"
        resp = self.client.post(follow=True, path=root(url.projects.topicsUpdate(project.getID())), data={
                                'addtopicIDs': addTopicIDs})
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.projects.profile)
        self.assertEqual(project.totalTopics(), 4)

    def test_tagsSearch(self):
        project = Project.objects.create(name=getProjName(
        ), creator=self.profile, status=Code.APPROVED, reponame=getProjRepo(), category=self.category, license=self.license)

        resp = self.client.post(follow=True, path=root(
            url.projects.tagsSearch(project.getID())))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.auth.login)

        self.client.login(email=self.email, password=self.password)
        resp = self.client.post(follow=True, path=root(
            url.projects.tagsSearch(project.getID())))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertDictEqual(json_loads(
            resp.content.decode(Code.UTF_8)), dict(code=Code.NO, error=Message.INVALID_REQUEST))

        resp = self.client.post(follow=True, path=root(url.projects.tagsSearch(project.getID())), data={
                                'query': getRandomStr()})
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertEqual(json_loads(
            resp.content.decode(Code.UTF_8))['code'], Code.OK)

    @tag('tagsup')
    def test_tagsUpdate(self):
        project = Project.objects.create(name=getProjName(
        ), creator=self.profile, status=Code.APPROVED, reponame=getProjRepo(), category=self.category, license=self.license)
        resp = self.client.post(follow=True, path=root(url.projects.tagsUpdate(project.getID())), data={
                                'addtagIDs': []})
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.auth.login)
        tags = Tag.objects.bulk_create(getTestTagsInst(4))
        addTagIDs = []
        for tag in tags:
            addTagIDs.append(tag.getID())
        self.client.login(email=self.email, password=self.password)
        resp = self.client.post(follow=True, path=root(url.projects.tagsUpdate(project.getID())), data={
                                'addtagIDs': ",".join(addTagIDs)})
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.projects.profile)
        self.assertEqual(project.totalTags(), 4)

    def test_liveData(self):
        project = Project.objects.create(name=getProjName(
        ), creator=self.profile, status=Code.APPROVED, reponame=getProjRepo(), category=self.category, license=self.license)
        resp = self.client.post(follow=True, path=root(
            url.projects.liveData(project.getID())))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        data = json_loads(resp.content.decode(Code.UTF_8))
        self.assertIsInstance(data['languages'], list)
        self.assertIsInstance(data['contributorsHTML'], str)

    @tag('cocreator')
    def test_cocreator(self):
        project:FreeProject = FreeProject.objects.create(name=getProjName(
        ), creator=self.profile, nickname=getProjRepo(), category=self.category, license=self.license, acceptedTerms=True)
        client = Client()
        resp = client.post(authroot(url.auth.LOGIN),dict(login=self.email, password=self.password),follow=True)
        self.assertTrue(resp.context['user'].is_authenticated)
        resp = client.get(root(url.projects.inviteProjectCocreator(project.get_id)))
        self.assertEqual(resp.status_code,HttpResponseNotAllowed.status_code)
        self.assertTrue(project.can_invite_cocreator_profile(self.modprofile))
        resp = client.post(root(url.projects.inviteProjectCocreator(project.get_id)),dict(action=getRandomStr()))
        self.assertEqual(resp.status_code,HttpResponse.status_code)
        self.assertDictEqual(json_loads(resp.content.decode(Code.UTF_8)),dict(code=Code.NO,error=Message.INVALID_REQUEST))
        resp = client.post(root(url.projects.inviteProjectCocreator(project.get_id)),dict(action=Action.CREATE))
        self.assertDictEqual(json_loads(resp.content.decode(Code.UTF_8)),dict(code=Code.NO,error=Message.INVALID_REQUEST))
        resp = client.post(root(url.projects.inviteProjectCocreator(project.get_id)),dict(action=Action.CREATE,email=self.email))
        self.assertDictEqual(json_loads(resp.content.decode(Code.UTF_8)),dict(code=Code.NO,error=Message.INVALID_REQUEST))
        resp = client.post(root(url.projects.inviteProjectCocreator(project.get_id)),dict(action=Action.CREATE,email=self.moduser.email))
        self.assertDictEqual(json_loads(resp.content.decode(Code.UTF_8)),dict(code=Code.OK))
        self.assertTrue(project.under_cocreator_invitation())
        self.assertTrue(project.under_cocreator_invitation_profile(self.modprofile))
        self.assertEqual(project.total_cocreator_invitations(),1)
        self.assertEqual(project.total_cocreators(),0)
        self.assertFalse(project.has_cocreators())
        self.assertFalse(project.can_invite_cocreator_profile(self.modprofile))

        



        


        

    
