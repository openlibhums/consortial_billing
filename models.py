from django.db import models
from django.utils import timezone


class Banding(models.Model):
    name = models.CharField(500, blank=False, unique=True)
    default_price = models.IntegerField(blank=True)


class Renewal(models.Model):
    date = models.DateField(default=timezone.now())
    amount = models.IntegerField(blank=False)
    currency = models.CharField(blank=False)
    institution = models.ForeignKey(Institution)


class BillingAgent(models.Model):
    name = models.CharField(500, blank=False)
    users = models.ManyToManyField('core.Account')


class Institution(models.Model):
    name = models.CharField(500, blank=False)
    country = models.CharField(500, blank=False)
    active = models.BooleanField(default=True)
    consortial_billing = models.BooleanField(default=False)
    banding = models.ForeignKey(Banding)
