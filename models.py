import uuid
import os
import re
import decimal
from typing import Tuple

from django.db import models
from django.utils import timezone
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.core.exceptions import ValidationError
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


BAND_CATEGORY_CHOICES = [
    ('calculated', 'Calculated'),
    ('special', 'Special'),
    ('base', 'Base'),
]


class BillingAgent(models.Model):
    name = models.CharField(
        max_length=255,
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
        help_text='If populated, the user will be redirected here '
                  'to complete the sign-up process',
    )

    def save(self, *args, **kwargs):
        if self.default:
            self.country = None
        logic.keep_default_unique(self)
        super().save(*args, **kwargs)

    def __str__(self):
        if self.default:
            return f'{self.name} (default)'
        elif self.country:
            return f'{self.name} ({self.country})'
        else:
            return self.name


class AgentContact(models.Model):
    agent = models.ForeignKey(
        'consortial_billing.BillingAgent',
        on_delete=models.CASCADE
    )
    account = models.ForeignKey(
        'core.Account',
        on_delete=models.CASCADE
    )

    @property
    def email(self):
        return self.account.email

    def __str__(self):
        return f'{self.account} <{self.email}>'


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
    multiplier = models.DecimalField(
        default=1,
        decimal_places=2,
        max_digits=3,
        help_text="Usually a decimal number between 0.00 and 5.00. "
                  "The base rate is multiplied by this number "
                  "as part of the support fee calculation.",
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

    def exchange_rate(self, base_band=None) -> Tuple[decimal.Decimal, str]:
        """
        Gets most up-to-date multiplier for exchange rate
        based on latest World Bank data,
        which is oriented around USD
        :return: tuple with the rate as decimal.Decimal plus a string warning if
                 matching country data could not be found
        """
        if not base_band:
            base_band = logic.get_base_band()

        if base_band:
            base_key = base_band.currency.region
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

    def convert_from(self, value, origin_currency):
        if not isinstance(origin_currency, Currency):
            try:
                currency = Currency.objects.get(code=origin_currency)
            except Currency.DoesNotExist:
                logger.error(f'{origin_currency} is not a recognized currency code.')
        target_exchange_rate, _warnings = self.exchange_rate()
        origin_exchange_rate, _warnings = origin_currency.exchange_rate()
        return value * (target_exchange_rate / origin_exchange_rate)

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
    category = models.CharField(
        max_length=10,
        default='calculated',
        choices=BAND_CATEGORY_CHOICES,
        help_text='Controls how the band functions, either as the basis '
                  'or result of fee calculation, or as a special band '
                  'for one supporter with a manually set fee.',
    )

    @property
    def economic_disparity(self) -> Tuple[decimal.Decimal, str]:
        """
        Gets most up-to-date multiplier for economic disparity
        based on latest GNI per capita figure
        :return: tuple of the indicator as decimal.Decimal plus a string warning if
                 matching country data could not be found
        """
        base_band = logic.get_base_band(level=self.level, country=self.country)
        base_key = base_band.country.alpha3
        warning = utils.setting('missing_data_economic_disparity')

        return logic.latest_multiplier_for_indicator(
            plugin_settings.DISPARITY_INDICATOR,
            self.country.alpha3,
            base_key,
            warning,
        )

    @property
    def size_difference(self) -> decimal.Decimal:
        """
        Returns multiplier representing the
        difference between the institution size
        and the base band institution size
        :return: decimal.Decimal
        """
        base_band = logic.get_base_band(self.level)
        base_band = logic.get_base_band(level=self.level, country=self.country)
        return self.size.multiplier / base_band.size.multiplier

    @property
    def exchange_rate(self) -> Tuple[decimal.Decimal, str]:
        """
        Returns exchange rate between this
        band's currency and the base band currency
        :return: a tuple with the rate as decimal.Decimal
        and a string warning if no data
        """
        base_band = logic.get_base_band(level=self.level, country=self.country)
        return self.currency.exchange_rate(base_band=base_band)

    def fee_in_currency(self, currency):
        if not isinstance(currency, Currency):
            try:
                currency = Currency.objects.get(code=currency)
            except Currency.DoesNotExist:
                logger.error(f'{currency} is not a recognized currency code.')

        target_exchange_rate, _warnings = currency.exchange_rate()
        origin_exchange_rate, _warnings = self.exchange_rate
        return self.fee * (target_exchange_rate / origin_exchange_rate)

    def calculate_fee(self) -> Tuple[int, str]:
        """
        Given institution size, supporter level, country,
        and exchange rate, calculates supporter fee
        :returns: The fee, as an int rounded to the nearest ten, and
        a string containing warnings for the end user
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

        if self.country in logic.countries_with_billing_agents():
            fee = logic.get_base_band(level=self.level, country=self.country).fee
        else:
            fee = logic.get_base_band(level=self.level).fee
        if fee is None:
            logger.error(
                'No fee has been set on base band'
            )

        # Account for size of institution
        # but only for standard (default) support levels,
        # not for higher supporters
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
        fee = max(fee, int(utils.setting('minimum_fee')))

        return fee, warnings

    def determine_billing_agent(self):
        return logic.determine_billing_agent(self.country)

    def save(self, *args, **kwargs):
        # Calculate fee if appropriate
        if not self.fee and self.category == 'calculated':
            self.fee, self.warnings = self.calculate_fee()

        # The user has changed an existing band from calculated to special.
        # In this case we want to create a new band object so we do not throw
        # off other supporter fees that may be dependant on the existing band.
        if self.pk and self.category == 'special':
            previous_category = Band.objects.get(pk=self.pk)
            if previous_category == 'calculated':
                self.warnings = ''
                self.pk = None

        # to do: change the type if the fee entered is
        # different than the calculated one

        super().save(*args, **kwargs)

    def __str__(self):
        yyyy_mm_dd = self.datetime.strftime("%Y-%m-%d")
        return f'{self.currency.symbol if self.currency else ""}' \
               f'{self.fee if self.fee else "?"}, ' \
               f'{self.level.name if self.level else ""}, ' \
               f'{self.size.name if self.size else ""}, ' \
               f'{self.country.name if self.country else ""}, ' \
               f'{ self.get_category_display() }, created {yyyy_mm_dd}'

    class Meta:
        get_latest_by = 'datetime'


class OldBand(models.Model):
    supporter = models.ForeignKey(
        'consortial_billing.Supporter',
        on_delete=models.CASCADE
    )
    band = models.ForeignKey(
        Band,
        on_delete=models.CASCADE
    )
    def __str__(self):
        return f'{self.supporter}, {self.band}'


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
        verbose_name="Institution name",
    )
    ror = models.URLField(
        blank=True,
        validators=[validate_ror],
        verbose_name='ROR',
        help_text='Research Organization Registry identifier (URL)',
    )
    address = models.TextField(
        max_length=255,
        blank=True,
        verbose_name="Billing address",
    )
    postal_code = models.CharField(
        max_length=255,
        blank=True,
    )
    display = models.BooleanField(
        default=True,
        help_text="May we include your institution name "
                  "in our public list of supporters?",
    )

    # Attached to supporter at signup or
    # recalculation with new data
    band = models.ForeignKey(
        Band,
        related_name='current_supporter',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        help_text='Current band',
    )

    prospective_band = models.ForeignKey(
        Band,
        related_name='prospective_supporter',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        help_text='Prospective band',
    )

    # Determined for the user or entered in admin
    active = models.BooleanField(
        default=False,
        help_text="Whether the supporter is active",
    )

    internal_notes = models.TextField(
        max_length=500,
        blank=True,
        help_text="Internal notes on this supporter",
    )

    @property
    def size(self):
        return self.band.size if self.band else None

    @property
    def country(self):
        return self.band.country if self.band else None

    @property
    def country_name(self):
        return self.band.country.name if self.band and self.band.country else ''

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
    def url(self):
        return reverse(
            'edit_supporter_band',
            args=(self.pk, ),
        )

    def get_ror(self, save=False, overwrite=False):
        ror = utils.get_ror(self.name)
        if ror and save and (not self.ror or overwrite):
            self.ror = ror
            self.save()
        return ror

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):

        # If the band has been changed, create an old band record.
        if self.band and self.pk:
            old_band = Supporter.objects.get(pk=self.pk).band
            if old_band and old_band != self.band:
                OldBand.objects.get_or_create(
                    supporter=self,
                    band=old_band,
                )

        super().save(*args, **kwargs)

    class Meta:
        ordering = ('name',)


class SupporterContact(models.Model):
    supporter = models.ForeignKey(
        Supporter,
        on_delete=models.CASCADE
    )
    account = models.ForeignKey(
        'core.Account',
        on_delete=models.CASCADE
    )

    @property
    def email(self):
        return self.account.email

    def __str__(self):
        return f'{self.account} <{self.email}>'


# Keep this for old migrations
def file_upload_path(instance, filename):
    try:
        filename = str(uuid.uuid4()) + '.' + str(filename.split('.')[1])
    except IndexError:
        filename = str(uuid.uuid4())

    path = "plugins/{0}/".format(plugin_settings.SHORT_NAME)
    return os.path.join(path, filename)
