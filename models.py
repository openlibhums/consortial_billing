from django.db import models
from django.utils import timezone


class Banding(models.Model):
    name = models.CharField(max_length=255, blank=False, unique=True)
    currency = models.CharField(max_length=255, blank=True, null=True)
    default_price = models.IntegerField(blank=True, null=True, default=0)
    billing_agent = models.ForeignKey('BillingAgent', null=True, blank=True)

    def __str__(self):
        return '{0}: {1} {2}'.format(self.name, self.default_price, self.currency if self.currency else '')


class BillingAgent(models.Model):
    name = models.CharField(max_length=255, blank=False)
    users = models.ManyToManyField('core.Account', blank=True, null=True)

    def __str__(self):
        return self.name


class Institution(models.Model):
    name = models.CharField(max_length=255, blank=False, unique=True, verbose_name="Institution Name")
    country = models.CharField(max_length=255, blank=False)
    active = models.BooleanField(default=True)
    consortial_billing = models.BooleanField(default=False)
    display = models.BooleanField(default=True)
    consortium = models.ForeignKey('self', blank=True, null=True)
    banding = models.ForeignKey(Banding, blank=True, null=True)
    billing_agent = models.ForeignKey(BillingAgent, blank=True, null=True)

    # Personal signup details
    first_name = models.CharField(max_length=255, null=True)
    last_name = models.CharField(max_length=255, null=True)
    email_address = models.EmailField(max_length=255, null=True)

    # Address
    address = models.TextField(max_length=255, null=True, verbose_name="Billing Address")
    postal_code = models.CharField(max_length=255, null=True, verbose_name="Post/Zip Code")

    def __str__(self):
        return self.name

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

    date_started = models.DateTimeField(default=timezone.now)
    date_open = models.DateTimeField()
    date_close = models.DateTimeField()

    options = models.ManyToManyField('Option')


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


