from django.test import TestCase, tag
from compete.models import *


@tag('model')
class CompetitionTest(TestCase):
    def test_invalid_comp(self):
        comp = Competition.objects.create(title=None)
        self.assertIsNone(comp.title)

    def test_valid_comp(self):
        comp = Competition.objects.create(title="Test competition")
        self.assertIsNotNone(comp.title)
