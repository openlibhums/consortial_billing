import uuid
import os

from django.db import models
from django.utils import timezone
from django.conf import settings
from django.core.files.storage import FileSystemStorage

from plugins.consortial_billing import plugin_settings


fs = FileSystemStorage(location=settings.MEDIA_ROOT)


def file_upload_path(instance, filename):
    try:
        filename = str(uuid.uuid4()) + '.' + str(filename.split('.')[1])
    except IndexError:
        filename = str(uuid.uuid4())

    path = "plugins/{0}/".format(plugin_settings.SHORT_NAME)
    return os.path.join(path, filename)


class Banding(models.Model):
    name = models.CharField(max_length=200, blank=False, unique=True)
    currency = models.CharField(max_length=255, blank=True, null=True)
    default_price = models.IntegerField(blank=True, null=True, default=0)
    billing_agent = models.ForeignKey('BillingAgent', null=True, blank=True)
    display = models.BooleanField(default=True)
    redirect_url = models.URLField(blank=True, null=True)

    def __str__(self):
        return '{0}: {1} {2}'.format(self.name, self.default_price, self.currency if self.currency else '')


class BillingAgent(models.Model):
    name = models.CharField(max_length=255, blank=False)
    users = models.ManyToManyField('core.Account', blank=True, null=True)

    def __str__(self):
        return self.name


def supporter_level():
    return (
        ('top', 'Top-Tier Supporters'),
        ('regular', 'Regular Supporters'),
    )


class SupportLevel(models.Model):
    name = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=99)

    class Meta:
        ordering = ('order', 'name')

    def __str__(self):
        return self.name


class Institution(models.Model):
    name = models.CharField(max_length=200, blank=False, unique=True, verbose_name="Institution Name")
    country = models.CharField(max_length=255, blank=False)
    sort_country = models.CharField(max_length=255, blank=True, default='')
    active = models.BooleanField(default=True)
    consortial_billing = models.BooleanField(default=False)
    display = models.BooleanField(default=True)
    consortium = models.ForeignKey('self', blank=True, null=True, on_delete=models.SET_NULL)
    banding = models.ForeignKey(Banding, blank=True, null=True, on_delete=models.SET_NULL)
    billing_agent = models.ForeignKey(BillingAgent, blank=True, null=True, on_delete=models.SET_NULL)

    # Personal signup details
    first_name = models.CharField(max_length=255, null=True, blank=True)
    last_name = models.CharField(max_length=255, null=True, blank=True)
    email_address = models.EmailField(max_length=255, null=True)

    # Address
    address = models.TextField(max_length=255, null=True, blank=True, verbose_name="Billing Address")
    postal_code = models.CharField(max_length=255, null=True, blank=True, verbose_name="Post/Zip Code")

    multiplier = models.DecimalField(decimal_places=2, max_digits=3, default=1.0)

    supporter_level = models.ForeignKey(SupportLevel, blank=True, null=True)

    referral_code = models.UUIDField(default=uuid.uuid4)

    class Meta:
        ordering = ('sort_country', 'name')

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.sort_country = self.country.replace('The ', '')
        super(Institution, self).save(*args, **kwargs)

    @property
    def next_renewal(self):
        renewals = self.renewal_set.order_by('-date')

        if len(renewals) > 0:
            return renewals[0]
        else:
            return None


class Renewal(models.Model):
    date = models.DateField(default=timezone.now)
    amount = models.DecimalField(decimal_places=2, max_digits=20, blank=False)
    currency = models.CharField(max_length=255, blank=False)
    institution = models.ForeignKey(Institution)
    billing_complete = models.BooleanField(default=False)
    date_renewed = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return "Renewal for {0} due {1} for {2} {3}".format(self.institution.name, self.date, self.amount, self.currency)


class ExcludedUser(models.Model):
    user = models.ForeignKey('core.Account')


class Signup(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email_address = models.CharField(max_length=500)
    institution = models.CharField(max_length=500)
    address = models.TextField(max_length=500)

    public = models.BooleanField()
    billing_agent_member = models.BooleanField()

    fte = models.TextField(max_length=500)
    other_amount = models.IntegerField(default=0, null=True)
    years = models.IntegerField(default=1)
    amount = models.IntegerField()


class Poll(models.Model):
    staffer = models.ForeignKey('core.Account')
    name = models.CharField(max_length=255)
    text = models.TextField(null=True)
    file = models.FileField(upload_to=file_upload_path, null=True, blank=True, storage=fs)

    date_started = models.DateTimeField(default=timezone.now)
    date_open = models.DateTimeField()
    date_close = models.DateTimeField()
    processed = models.BooleanField(default=False)

    options = models.ManyToManyField('Option')

    @property
    def open(self):
        if self.date_open < timezone.now() and self.date_close > timezone.now():
            return True
        return False


class Option(models.Model):
    text = models.CharField(max_length=300)
    all = models.BooleanField(default=False)

    def increase(self, institution):
        try:
            increase = IncreaseOptionBand.objects.get(banding=institution.banding, option=self)
            return "{0} {1}".format(increase.price_increase, institution.banding.currency)
        except IncreaseOptionBand.DoesNotExist:
            return "No result found."


class IncreaseOptionBand(models.Model):
    banding = models.ForeignKey(Banding)
    option = models.ForeignKey(Option)
    price_increase = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)


class Vote(models.Model):
    institution = models.ForeignKey(Institution)
    poll = models.ForeignKey(Poll)
    aye = models.ManyToManyField(Option, related_name="vote_aye")
    no = models.ManyToManyField(Option, related_name="vote_no")


class Referral(models.Model):
    referring_institution = models.ForeignKey(Institution, related_name='referring_institution')
    new_institution = models.ForeignKey(Institution, related_name='new_institution')
    referring_discount = models.DecimalField(decimal_places=2, max_digits=10, blank=True, null=True)
    referent_discount = models.DecimalField(decimal_places=2, max_digits=10, blank=True, null=True)
    datetime = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ('datetime',)

    def reverse(self):
        referring_renewal = Renewal.objects.get(pk=self.referring_institution.next_renewal.pk)
        referent_renewal = Renewal.objects.get(pk=self.new_institution.next_renewal.pk)

        referring_renewal.amount = referring_renewal.amount + self.referring_discount
        referent_renewal.amount = referent_renewal.amount + self.referent_discount

        referring_renewal.save()
        referent_renewal.save()

        self.delete()
