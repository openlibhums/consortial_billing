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
        if self.default:
            self.country = None
        logic.keep_default_unique(self)
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
        if self.default:
            return f'{self.name} (default)'
        elif self.country:
            return f'{self.name} ({self.country})'


class SupporterSize(models.Model):
    name = models.CharField(
        max_length=50,
        help_text="The name of the size band, e.g. Large Institution",
    )
    description = models.CharField(
        max_length=200,
        blank=True,
        help_text='How size is determined, e.g. 0-4999 FTE staff '
                  'for an institution'
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

    def __str__(self):
        if self.description:
            return f'{self.name} ({self.description})'
        else:
            return self.name

    class Meta:
        ordering = ('-multiplier',)


class SupportLevel(models.Model):
    name = models.CharField(
        max_length=30,
        blank=True,
        null=True,
        help_text="The level of support, e.g. Standard or Gold"
    )
    description = models.CharField(
        max_length=255,
        blank=True,
    )
    order = models.IntegerField(
        blank=True,
        null=True,
        help_text="The order in which to display the levels "
                  "from highest to lowest.",
    )
    default = models.BooleanField(
        default=False,
        help_text="Designates this level as the standard level, set "
                  "apart from higher levels. "
                  "If checked, institution size will be factored "
                  "in to fees on this level. If unchecked, institution "
                  "size will not matter.",
    )
    internal_notes = models.CharField(
        max_length=255,
        blank=True,
        help_text="Internal notes on how this was configured, "
                  "for when it needs updating next",
    )

    class Meta:
        ordering = ('order', 'name')

    def __str__(self):
        if self.description:
            return f'{self.name} ({self.description})'
        else:
            return f'{self.name}'

    def save(self, *args, **kwargs):
        logic.keep_default_unique(self)
        super().save(*args, **kwargs)


class Currency(models.Model):

    code = models.CharField(
        max_length=3,
        help_text="Three-letter currency code, e.g. EUR",
    )
    symbol = models.CharField(
        blank=True,
        max_length=2,
        help_text="Currency symbol, e.g. €",
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

    def exchange_rate(self, base_band=None):
        """
        Gets most up-to-date multiplier for exchange rate
        based on latest World Bank data,
        which is oriented around USD
        :return: tuple with the rate as int plus a string warning if
                 matching country data could not be found
        """
        if not base_band:
            base_band = logic.get_base_band()

        if base_band:
            base_key = base_band.country.alpha3
        else:
            # This is needed during initial configuration
            base_key = '---'

        warning = utils.setting('missing_data_exchange_rate')

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
        verbose_name="Institution size",
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
        verbose_name='Annual fee',
    )
    fixed_fee = models.BooleanField(
        default=False,
        help_text='Select if you want to manually set the fee '
                  'for this band. The fee calculator for this '
                  'band (i.e., this combination of size, level, '
                  'country, and currency) will then return '
                  'whatever fee you type in the fee field. '
                  'Note: thie field has no effect on base bands, '
                  'which do take a manually input fee.',
    )
    warnings = models.CharField(
        max_length=255,
        blank=True,
        help_text='Warning messages from the fee calculator',
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
                  'the base fee, country, and currency for a '
                  'given support level.',
    )

    @property
    def economic_disparity(self):
        """
        Gets most up-to-date multiplier for economic disparity
        based on latest GNI per capita figure
        :return: tuple of the indicator as int plus a string warning if
                 matching country data could not be found
        """
        base_band = logic.get_base_band(self.level)
        base_key = base_band.country.alpha3
        warning = utils.setting('missing_data_economic_disparity')

        return logic.latest_multiplier_for_indicator(
            plugin_settings.DISPARITY_INDICATOR,
            self.country.alpha3,
            base_key,
            warning,
        )

    @property
    def size_difference(self):
        """
        Returns multiplier representing the
        difference between the institution size
        and the base band institution size
        :return: integer
        """
        base_band = logic.get_base_band(self.level)
        return self.size.multiplier / base_band.size.multiplier

    @property
    def exchange_rate(self):
        """
        Returns exchange rate between this
        band's currency and the base band currency
        :return: integer
        """
        base_band = logic.get_base_band(self.level)
        return self.currency.exchange_rate(base_band)

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

        if self.fixed_fee:
            return self.fee, warnings

        fee = logic.get_base_band(self.level).fee
        if fee is None:
            raise ImproperlyConfigured(
                'No fee has been set on base band'
            )

        # Account for size of institution
        # but only for standard support levels,
        # not higher supporters
        if self.level.default:
            fee *= self.size_difference

        # Account for country
        disparity, warning = self.economic_disparity
        fee *= disparity
        warnings += warning

        # Convert into preferred currency
        rate, warning = self.exchange_rate
        fee *= rate
        warnings += warning

        # Round to the nearest ten
        fee = int(round(fee, -1))

        # Check against minimum fee (e.g. 100)
        fee = max(fee, utils.setting('minimum_fee'))

        return fee, warnings

    def determine_billing_agent(self):
        return logic.determine_billing_agent(self.country)

    def save(self, *args, **kwargs):
        # Don't display base bands
        if self.base:
            self.display = False

        # Calculate fee if empty
        if not self.fee and not self.base:
            self.fee, self.warnings = self.calculate_fee()

        # Update datetime on save for fixed fee bands only
        # (others should retain original timestamp because
        # they are designed to be superseded by new bands annually)
        if self.fixed_fee:
            self.datetime = timezone.now()

        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.fee} {self.currency} ({self.datetime}): ' \
               f'{self.size}, {self.level}, {self.country.name}'

    class Meta:
        get_latest_by = 'datetime'


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
        verbose_name="Institution name",
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
