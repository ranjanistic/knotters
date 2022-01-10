import uuid
from django.core.cache import cache
from django.db import models
from main.strings import PEOPLE
from django.conf import settings
from django.utils import timezone

class Country(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20)
    iso3 = models.CharField(max_length=5)
    iso2 = models.CharField(max_length=3)
    # created_at = models.DateTimeField(auto_now=False,default=timezone.now)

    def __str__(self):
        return f"{self.name} ({self.code})"
    
    def getStates(self):
        states = cache.get(f'auth_country_data_states_{self.id}')
        if not states:
            states = State.objects.filter(country=self)
            cache.set(f'auth_country_data_states_{self.id}',states,settings.CACHE_ETERNAL)
        return states

    def getStatesCount(self):
        states_count = cache.get(f'auth_country_data_states_count_{self.id}')
        if not states_count:
            states_count = State.objects.filter(country=self).count()
            cache.set(f'auth_country_data_states_count_{self.id}',states_count,settings.CACHE_ETERNAL)
        return states_count

class State(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name='state_country')
    name = models.CharField(max_length=200)
    # created_at = models.DateTimeField(auto_now=False,default=timezone.now)

    def __str__(self):
        return self.name

class PhoneNumber(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        f"{PEOPLE}.User", on_delete=models.CASCADE, related_name='phone_user')
    number = models.CharField(max_length=100)
    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name='phone_country')
    verified = models.BooleanField(default=False)
    primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now=False,default=timezone.now)

    def __str__(self):
        return self.user.get_name

class Address(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        f"{PEOPLE}.User", on_delete=models.CASCADE, related_name='address_user')
    locality = models.CharField(max_length=200, null=True, blank=True)
    line_1 = models.CharField(max_length=200, null=True, blank=True)
    line_2 = models.CharField(max_length=200, null=True, blank=True)
    city = models.CharField(max_length=200, null=True, blank=True)
    state = models.ForeignKey(State, on_delete=models.CASCADE, related_name='phone_country')
    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name='address_country')
    zip_code = models.CharField(max_length=100, null=True, blank=True)
    phone_number = models.ForeignKey(PhoneNumber,on_delete=models.SET_NULL, related_name='address_phone', null=True,blank=True)
    created_at = models.DateTimeField(auto_now=False,default=timezone.now)

    def __str__(self):
        return self.user.get_name