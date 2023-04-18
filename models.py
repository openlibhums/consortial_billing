import uuid
import os
import re

from django.db import models
from django.utils import timezone
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.core.exceptions import ValidationError, ImproperlyConfigured
from django.shortcuts import reverse

from django_countries.fields import CountryField

from plugins.consortial_billing import utils, logic, plugin_settings

from utils.logger import get_logger
logger = get_logger(__name__)

fs = FileSystemStorage(location=settings.MEDIA_ROOT)


CURRENCY_REGION_CHOICES = [
    ('EMU', 'Euro area'),
    ('GBR', 'United Kingdom'),
    ('USA', 'United States'),
]


class BillingAgent(models.Model):
    name = models.CharField(
        max_length=255,
    )
    users = models.ManyToManyField(
        'core.Account',
        blank=True,
        null=True,
    )
    country = CountryField(
        blank=True,
        null=True,
        help_text='If selected, will route all signups in this '
                  'country to this agent.',
    )
    default = models.BooleanField(
        default=False,
        help_text='Designates this as the default billing agent. ',
    )
    redirect_url = models.URLField(
        blank=True,
        null=True,
        help_text='If populated, the user will be redirected here '
                  'to complete the sign-up process',
    )

    def save(self, *args, **kwargs):
        # Keep self.default unique
        if self.default:
            self.country = None
            try:
                other = BillingAgent.objects.get(default=True)
                if self != other:
                    other.default = False
                    other.save()
            except BillingAgent.DoesNotExist:
                pass
        super().save(*args, **kwargs)

    @property
    def email(self):
        return self.users.first().email if self.users else None

    @property
    def first_name(self):
        return self.users.first().first_name if self.users else None

    @property
    def last_name(self):
        return self.users.first().last_name if self.users else None

    def __str__(self):
        return self.name


class SupporterSize(models.Model):
    name = models.CharField(
        max_length=50,
        help_text="The name of the size band, e.g. Large Institution",
    )
    description = models.CharField(
        max_length=200,
        blank=True,
        help_text='How size is determined, e.g. 0-4999 FTE staff '
                  'for an institution, or 10-19 members for a consortium '
    )
    multiplier = models.FloatField(
        default=1,
        help_text="The base rate is multiplied by this "
                  "as part of the support fee calculation",
    )
    internal_notes = models.CharField(
        max_length=255,
        blank=True,
        help_text="Internal notes on how this was configured, "
                  "for when it needs updating next",
    )
    is_consortium = models.BooleanField(
        default=False,
        help_text="Whether this is a consortium",
    )

    def __str__(self):
        if self.description:
            return f'{self.name} ({self.description})'
        else:
            return self.name

    class Meta:
        ordering = ('is_consortium', '-multiplier', 'name')


class SupportLevel(models.Model):
    name = models.CharField(
        max_length=30,
        blank=True,
        null=True,
        help_text="The level of support, e.g. Standard or Higher"
    )
    description = models.CharField(
        max_length=255,
        blank=True,
    )
    multiplier = models.FloatField(
        default=1,
        help_text="The base rate is multiplied by this "
                  "as part of the support fee calculation",
    )
    internal_notes = models.CharField(
        max_length=255,
        blank=True,
        help_text="Internal notes on how this was configured, "
                  "for when it needs updating next",
    )

    class Meta:
        ordering = ('-multiplier', 'name')

    def __str__(self):
        return f'{self.name} support'


class Currency(models.Model):

    code = models.CharField(
        max_length=3,
        help_text="Three-letter currency code, e.g. EUR",
    )
    region = models.CharField(
        max_length=3,
        choices=CURRENCY_REGION_CHOICES,
        help_text="The region or country associated with this currency "
                  "in World Bank data",
    )
    internal_notes = models.CharField(
        max_length=255,
        blank=True,
        help_text="Internal notes on how this was configured, "
                  "for when it needs updating next",
    )

    @property
    def exchange_rate(self):
        """
        Gets most up-to-date multiplier for exchange rate
        based on latest GNI per capita figure
        :return: tuple with the rate as int plus a string warning if
                 matching country data could not be found
        """
        base_band = logic.get_base_band()
        if base_band:
            base_key = base_band.country.alpha3
        else:
            # This is needed during initial configuration
            base_key = '---'

        warning = f"""
                   <p>We don't have currency data for the region {self.region},
                   so we could not factor that in to the fee calculation</p>
                   """
        return logic.latest_multiplier_for_indicator(
            plugin_settings.RATE_INDICATOR,
            self.region,
            base_key,
            warning,
        )

    def __str__(self):
        return self.code

    class Meta:
        ordering = ('code',)
        verbose_name_plural = 'Currencies'


class Band(models.Model):

    size = models.ForeignKey(
        SupporterSize,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        verbose_name="Institution/consortium size",
    )
    country = CountryField(
        blank=True,
        null=True,
    )
    currency = models.ForeignKey(
        Currency,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        verbose_name="Preferred currency",
    )
    level = models.ForeignKey(
        SupportLevel,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        verbose_name="Support level",
    )
    datetime = models.DateTimeField(
        default=timezone.now,
    )
    fee = models.IntegerField(
        blank=True,
        null=True,
    )
    billing_agent = models.ForeignKey(
        BillingAgent,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        help_text="Who is responsible for billing this supporter",
    )
    display = models.BooleanField(
        default=True,
    )
    base = models.BooleanField(
        default=False,
        help_text='Select if this is the base band to represent '
                  'the base fee, country, currency, size, and support level.',
    )
    warnings = models.CharField(
        max_length=255,
        blank=True,
        help_text='Warning messages from the fee calculator',
    )

    @property
    def economic_disparity(self):
        """
        Gets most up-to-date multiplier for economic disparity
        based on latest GNI per capita figure
        :return: tuple of the indicator as int plus a string warning if
                 matching country data could not be found
        """
        base_key = logic.get_base_band().country.alpha3
        warning = f"""
                   <p>We don't have data for {self.country.name},
                   so we could not factor that in to the fee calculation</p>
                   """

        return logic.latest_multiplier_for_indicator(
            plugin_settings.DISPARITY_INDICATOR,
            self.country.alpha3,
            base_key,
            warning,
        )

    def calculate_fee(self):
        """
        Given institution size, supporter level, country,
        and exchange rate, calculates supporter fee
        """
        for field in [
            self.size,
            self.level,
            self.country,
            self.currency
        ]:
            if not field:
                raise ValidationError(
                    'Band does not have data needed for fee calculation'
                )

        warnings = ''
        fee = logic.get_base_band().fee

        # Account for size of institution
        fee *= self.size.multiplier

        # Account for support level chosen
        fee *= self.level.multiplier

        # Account for country
        disparity, warning = self.economic_disparity
        fee *= disparity
        warnings += warning

        # Convert into preferred currency
        rate, warning = self.currency.exchange_rate
        fee *= rate
        warnings += warning

        # Round to the nearest ten
        fee = int(round(fee, -1))

        # Check against minimum fee (e.g. 100)
        fee = max(fee, utils.setting('minimum_fee'))

        return fee, warnings

    def determine_billing_agent(self):
        try:
            agent = BillingAgent.objects.get(country=self.country)
            return agent
        except BillingAgent.DoesNotExist:
            try:
                agent = BillingAgent.objects.get(default=True)
                return agent
            except BillingAgent.DoesNotExist:
                raise ImproperlyConfigured(
                    'No billing agent has been set as default'
                )

    def save(self, *args, **kwargs):
        # Don't display base bands
        if self.base:
            self.display = False

        # Calculate fee if empty
        if not self.fee and not self.base:
            self.fee, self.warnings = self.calculate_fee()

        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.fee} {self.currency} ({self.datetime}): ' \
               f'{self.size}, {self.level}, {self.country.name}'


def validate_ror(url):
    ror = os.path.split(url)[-1]
    ror_regex = '^0[a-hj-km-np-tv-z|0-9]{6}[0-9]{2}$'
    if not re.match(ror_regex, ror):
        raise ValidationError(f'{ror} is not a valid ROR identifier')


class Supporter(models.Model):

    # Entered by user on signup
    name = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name="Institution/consortium name",
    )
    ror = models.URLField(
        blank=True,
        null=True,
        validators=[validate_ror],
        verbose_name='ROR',
        help_text='Research Organization Registry identifier (URL)',
    )
    address = models.TextField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Billing address",
    )
    postal_code = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )
    country = CountryField(
        blank=True,
        null=True,
    )
    display = models.BooleanField(
        default=True,
        help_text="May we include your institution name "
                  "in our public list of supporters?",
    )
    contacts = models.ManyToManyField(
        'core.Account',
        related_name="contact_for_supporter",
        blank=True,
        null=True,
        help_text="Who can be contacted at this supporter",
    )

    # Attached to supporter at signup or
    # recalculation with new data
    band = models.ForeignKey(
        Band,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        help_text='Current band',
    )
    old_bands = models.ManyToManyField(
        Band,
        blank=True,
        null=True,
        help_text='Old bands for this supporter',
        related_name='supporter_history',
    )

    # Determined for the user or entered in admin
    active = models.BooleanField(
        default=False,
        help_text="Whether the supporter is active",
    )

    @property
    def size(self):
        return self.band.size if self.band else None

    @property
    def level(self):
        return self.band.level if self.band else None

    @property
    def currency(self):
        return self.band.currency if self.band else None

    @property
    def fee(self):
        return self.band.fee if self.band else None

    @property
    def warnings(self):
        return self.band.warnings if self.band else None

    @property
    def datetime(self):
        return self.band.datetime if self.band else None

    @property
    def billing_agent(self):
        return self.band.billing_agent if self.band else None

    @property
    def email(self):
        return self.contacts.first().email if self.contacts else None

    @property
    def first_name(self):
        return self.contacts.first().first_name if self.contacts else None

    @property
    def last_name(self):
        return self.contacts.first().last_name if self.contacts else None

    @property
    def url(self):
        return reverse(
            'admin:consortial_billing_supporter_change',
            args=(self.pk, ),
        )

    def __str__(self):
        return self.name

    class Meta:
        ordering = ('name',)


# Keep this for old migrations
def file_upload_path(instance, filename):
    try:
        filename = str(uuid.uuid4()) + '.' + str(filename.split('.')[1])
    except IndexError:
        filename = str(uuid.uuid4())

    path = "plugins/{0}/".format(plugin_settings.SHORT_NAME)
    return os.path.join(path, filename)
