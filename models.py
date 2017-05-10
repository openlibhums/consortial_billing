from django.db import models
from django.utils import timezone


class Banding(models.Model):
    name = models.CharField(max_length=255, blank=False, unique=True)
    default_price = models.IntegerField(blank=True, null=True, default=0)


class BillingAgent(models.Model):
    name = models.CharField(max_length=255, blank=False)
    users = models.ManyToManyField('core.Account', blank=True, null=True)


class Institution(models.Model):
    name = models.CharField(max_length=255, blank=False, unique=True)
    country = models.CharField(max_length=255, blank=False)
    active = models.BooleanField(default=True)
    consortial_billing = models.BooleanField(default=False)
    display = models.BooleanField(default=True)
    consortium = models.ForeignKey('self', blank=True, null=True)
    banding = models.ForeignKey(Banding, blank=True, null=True)
    billing_agent = models.ForeignKey(BillingAgent, blank=True, null=True)


class Renewal(models.Model):
    date = models.DateField(default=timezone.now)
    amount = models.DecimalField(decimal_places=2, max_digits=20, blank=False)
    currency = models.CharField(max_length=255, blank=False)
    institution = models.ForeignKey(Institution)


class ExcludedUser(models.Model):
    user = models.ForeignKey('core.Account')
