from django.test import TestCase, tag
from main.strings import Code
from people.tests.utils import getTestEmail, getTestFName
from .utils import getRandomStr, getTestUrl
from main.mailers import *



@tag(Code.Test.MAIL,Code.Test.REST)
class TestMailers(TestCase):
    def test_getEmailHtmlBody(self):
        html, body = getEmailHtmlBody(getRandomStr(),getRandomStr(),getRandomStr(),getTestFName(),conclusion=getRandomStr())
        self.assertIsNotNone(html)
        self.assertIsNotNone(body)

    def test_sendEmail(self):
        html, body = getEmailHtmlBody(getRandomStr(),getRandomStr(),getRandomStr(),getTestFName(),conclusion=getRandomStr())
        self.assertTrue(sendEmail(getTestEmail(),getRandomStr(),html,body))

    def test_sendCCEmail(self):
        html, body = getEmailHtmlBody(getRandomStr(),getRandomStr(),getRandomStr(),getTestFName(),conclusion=getRandomStr())
        self.assertTrue(sendCCEmail([getTestEmail(),getTestEmail()],getRandomStr(),html,body))

    def test_sendAlertEmail(self):
        self.assertTrue(sendAlertEmail(getTestEmail(),getRandomStr(),getRandomStr(),getRandomStr(),getRandomStr()))

    def test_sendCCAlertEmail(self):
        self.assertTrue(sendCCAlertEmail([getTestEmail(),getTestEmail()],getRandomStr(),getRandomStr(),getRandomStr(),getRandomStr()))

    def test_sendActionEmail(self):
        self.assertTrue(sendActionEmail(getTestEmail(),getRandomStr(),getRandomStr(),getRandomStr(),getRandomStr(), actions=[dict(
            text=getRandomStr(),
            url=getTestUrl(),
        )]))

    def test_sendCCActionEmail(self):
        self.assertTrue(sendCCActionEmail([getTestEmail(),getTestEmail()],getRandomStr(),getRandomStr(),getRandomStr(),getRandomStr(),actions=[dict(
            text=getRandomStr(),
            url=getTestUrl(),
        )]))
