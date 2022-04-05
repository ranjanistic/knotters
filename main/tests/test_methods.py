from auth2.tests.utils import getTestPassword
from django.test import TestCase, tag
from main.env import BOTMAIL
from main.methods import *
from main.strings import Code, Message, classAttrsToDict
from people.models import User

from .utils import B64


@tag(Code.Test.METHOD, Code.Test.REST)
class MainMethodsTest(TestCase):
    @classmethod
    def setUpTestData(self) -> None:
        self.bot, _ = User.objects.get_or_create(email=BOTMAIL, defaults=dict(
            first_name='knottersbot', email=BOTMAIL, password=getTestPassword()))
        return super().setUpTestData()

    def test_respondJSON(self):
        response = respondJson(Code.OK)
        self.assertJSONEqual(
            str(response.content, encoding=response.charset), dict(code=Code.OK))

    def test_getDeepFilePaths(self):
        def appendWhen(path):
            return path.endswith('.html')

        self.assertEqual(len(getDeepFilePaths('template', appendWhen)), 0)
        templates = getDeepFilePaths('templates', appendWhen)
        self.assertIsInstance(templates, list)
        self.assertTrue(len(templates) > 0)

    def test_maxLengthInList(self):
        def appendWhen(path):
            return path.endswith('.html')
        templates = getDeepFilePaths('templates', appendWhen)
        self.assertIsInstance(maxLengthInList(templates), int)
        self.assertTrue(maxLengthInList(templates) > 0)

    def test_minLengthInList(self):
        def appendWhen(path):
            return path.endswith('.html')
        templates = getDeepFilePaths('templates', appendWhen)
        self.assertIsInstance(minLengthInList(templates), int)
        self.assertTrue(maxLengthInList(templates) >=
                        minLengthInList(templates))

    def test_base64ToImageFile(self):
        file = base64ToImageFile(B64)
        self.assertIsInstance(file, ContentFile)

    def test_classAttrsToDict(self):
        def conditn(key, _):
            return str(key).isupper()
        self.assertIsInstance(classAttrsToDict(Message, conditn), dict)
