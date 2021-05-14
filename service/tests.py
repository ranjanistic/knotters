from django.test import TestCase

from .models import *

# class ServiceTestCase(TestCase):
#     def setUp(self):
#         Service.objects.create(name="TestService", url="testurl.myapp.xyz", description="Nothing new")

#     def test_service(self):
#         testservice = Service.objects.get(name="TestService")
#         self.assertEqual(testservice.url, "testurl.myapp.xyz")
