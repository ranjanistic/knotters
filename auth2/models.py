from datetime import datetime
from uuid import UUID, uuid4

from django.conf import settings
from django.core.cache import cache
from django.db import models
from django.utils import timezone
from main.strings import PEOPLE


class Country(models.Model):
    """The model a country record"""
    id: UUID = models.UUIDField(
        primary_key=True, default=uuid4, editable=False)
    name: str = models.CharField(max_length=200)
    """name (str): The name of the country."""
    code: str = models.CharField(max_length=20)
    """code (str): The code of the country. (dialing code)"""
    iso3: str = models.CharField(max_length=5)
    """iso3 (str): The ISO 3166-1 alpha-3 code of the country."""
    iso2: str = models.CharField(max_length=3)
    """iso2 (str): The ISO 3166-1 alpha-2 code of the country."""

    def __str__(self):
        return f"{self.name} ({self.code})"

    def getStates(self):
        cacheKey = f'auth_country_data_states_{self.id}'
        states = cache.get(cacheKey, None)
        if not states:
            states = State.objects.filter(country=self)
            cache.set(cacheKey, states, settings.CACHE_ETERNAL)
        return states

    def getStatesCount(self):
        cacheKey = f'auth_country_data_states_count_{self.id}'
        states_count = cache.get(cacheKey, None)
        if not states_count:
            states_count = State.objects.filter(country=self).count()
            cache.set(cacheKey, states_count, settings.CACHE_ETERNAL)
        return states_count


class State(models.Model):
    """The model for state information of a country."""
    id: UUID = models.UUIDField(
        primary_key=True, default=uuid4, editable=False)
    country: Country = models.ForeignKey(
        Country, on_delete=models.CASCADE, related_name='state_country')
    """country (ForeignKey<Country>): The country that this state belongs to."""
    name: str = models.CharField(max_length=200)
    """name (CharField): The name of the state."""
    # created_at = models.DateTimeField(auto_now=False,default=timezone.now)

    def __str__(self):
        return self.name


class PhoneNumber(models.Model):
    """The model for phone numbers of users"""
    id: UUID = models.UUIDField(
        primary_key=True, default=uuid4, editable=False)
    user = models.ForeignKey(
        f"{PEOPLE}.User", on_delete=models.CASCADE, related_name='phone_user')
    """user (OneToOneField<User>): The user who owns this phone number."""
    number: str = models.CharField(max_length=100)
    """number (CharField): The phone number."""
    country: Country = models.ForeignKey(
        Country, on_delete=models.CASCADE, related_name='phone_country')
    """country (ForeignKey<Country>): The country of this phone number."""
    verified: bool = models.BooleanField(default=False)
    """verified (BooleanField): Whether this phone number is verified."""
    primary: bool = models.BooleanField(default=False)
    """primary (BooleanField): Whether this phone number is the primary one."""
    created_at: datetime = models.DateTimeField(
        auto_now=False, default=timezone.now)
    """created_at (DateTimeField): The date and time this phone number was created."""

    def __str__(self):
        return self.user.get_name


class Address(models.Model):
    """The model for addresses of users"""
    id: UUID = models.UUIDField(
        primary_key=True, default=uuid4, editable=False)
    user = models.OneToOneField(
        f"{PEOPLE}.User", on_delete=models.CASCADE, related_name='address_user')
    """user (OneToOneField<User>): The user who owns this address."""
    locality: str = models.CharField(max_length=200, null=True, blank=True)
    """locality (str): The locality of the address."""
    line_1: str = models.CharField(max_length=200, null=True, blank=True)
    """line_1 (str): The first line of the address."""
    line_2: str = models.CharField(max_length=200, null=True, blank=True)
    """line_2 (str): The second line of the address."""
    city: str = models.CharField(max_length=200, null=True, blank=True)
    """city (str): The city of the address."""
    state: State = models.ForeignKey(
        State, on_delete=models.CASCADE, related_name='phone_country')
    """state (ForeignKey<State>): The state of the address."""
    country: Country = models.ForeignKey(
        Country, on_delete=models.CASCADE, related_name='address_country')
    """country (ForeignKey<Country>): The country of the address."""
    zip_code: str = models.CharField(max_length=100, null=True, blank=True)
    """zip_code (str): The zip code of the address."""
    phone_number: PhoneNumber = models.ForeignKey(
        PhoneNumber, on_delete=models.SET_NULL, related_name='address_phone', null=True, blank=True)
    """phone_number (ForeignKey<PhoneNumber>): The phone number of the address."""
    created_at: datetime = models.DateTimeField(
        auto_now=False, default=timezone.now)
    """created_at (DateTimeField): The date and time the address was created."""

    def __str__(self):
        return self.user.get_name


class Notification(models.Model):
    """The model for notification channels"""
    id: UUID = models.UUIDField(
        primary_key=True, default=uuid4, editable=False)
    name: str = models.CharField(max_length=80)
    """name (str): The name of the notification channel"""
    code: int = models.IntegerField(default=0)
    """code (int) : Code for notification type"""
    description: str = models.CharField(max_length=200, null=True, blank=True)
    """description (str): The description of the notification channel"""
    disabled: bool = models.BooleanField(default=False)
    """disabled (bool): Whether the notification channel is disabled"""
    created_at: datetime = models.DateTimeField(
        auto_now=False, default=timezone.now)
    """created_at (datetime): The date and time the notification channel was created"""

    def __str__(self) -> str:
        return self.name


class EmailNotification(models.Model):
    """The model for email notification subscribers of a notification channel"""
    id: UUID = models.UUIDField(
        primary_key=True, default=uuid4, editable=False)
    notification: Notification = models.OneToOneField(
        Notification, on_delete=models.CASCADE, related_name='email_notification_notif', default=None)
    """notifcation (OneToOneField<Notification>): The notification channel"""
    subscribers = models.ManyToManyField(f"{PEOPLE}.User", through="EmailNotificationSubscriber", default=[
    ], related_name='email_notification_subscribers')
    """subscribers (ManyToManyField<User>): The subscribers of the notification channel"""

    def __str__(self) -> str:
        return self.notification.name


class DeviceNotification(models.Model):
    """The model for device push notification subscribers of a notification channel"""
    id: UUID = models.UUIDField(
        primary_key=True, default=uuid4, editable=False)
    notification: Notification = models.OneToOneField(
        Notification, on_delete=models.CASCADE, related_name='device_notification_notif', default=None)
    """notifcation (OneToOneField<Notification>): The notification channel"""
    subscribers = models.ManyToManyField(f"{PEOPLE}.User", through="DeviceNotificationSubscriber", default=[
    ], related_name='device_notification_subscribers')
    """subscribers (ManyToManyField<User>): The subscribers of the notification channel"""

    def __str__(self) -> str:
        return self.notification.name


class EmailNotificationSubscriber(models.Model):
    """The model for relation between a user and an email notification subscription"""
    id: UUID = models.UUIDField(
        primary_key=True, default=uuid4, editable=False)
    user = models.ForeignKey(
        f"{PEOPLE}.User", on_delete=models.CASCADE, related_name='enotification_sub_user')
    """user (ForeignKey<User>): The user who is subscribed to the notification."""
    email_notification: EmailNotification = models.ForeignKey(
        EmailNotification, on_delete=models.CASCADE, related_name='enotification_sub_notification')
    """email_notification (ForeignKey<EmailNotification>): The notification to which the user is subscribed."""
    created_at: datetime = models.DateTimeField(
        auto_now=False, default=timezone.now)
    """created_at (DateTimeField): The date and time when the subscription relation was created"""


class DeviceNotificationSubscriber(models.Model):
    """The model for relation between a user and a device notification subscription"""
    id: UUID = models.UUIDField(
        primary_key=True, default=uuid4, editable=False)
    user = models.ForeignKey(
        f"{PEOPLE}.User", on_delete=models.CASCADE, related_name='dnotification_sub_user')
    """user (ForeignKey<User>): The user who is subscribed to the notification."""
    device_notification: DeviceNotification = models.ForeignKey(
        DeviceNotification, on_delete=models.CASCADE, related_name='dnotification_sub_notification')
    """device_notification (ForeignKey<DeviceNotification>): The device notification subscription"""
    created_at: datetime = models.DateTimeField(
        auto_now=False, default=timezone.now)
    """created_at (DateTimeField): The date and time when the subscription relation was created"""
