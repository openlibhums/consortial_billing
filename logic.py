__copyright__ = "Copyright 2023 Birkbeck, University of London"
__author__ = "Open Library of Humanities"
__license__ = "AGPL v3"
__maintainer__ = "Open Library of Humanities"

import os
import decimal
from typing import Tuple

from django.utils import timezone
from django.conf import settings
from django.db.models import Sum, Q

from core import models as core_models
from cms import models as cms_models
from plugins.consortial_billing import utils, models as supporter_models, plugin_settings
from utils.logger import get_logger

logger = get_logger(__name__)


def get_display_bands():
    """
    Compiles bands into display bands for use in
    an HTML table
    """

    def build_display_band(level, size, currency, kwargs):
        bands = supporter_models.Band.objects.filter(**kwargs)

        display_band = {}

        display_band['level'] = level

        display_band['size'] = size.name

        countries = sorted(
            set(band.country.name for band in bands)
        )
        display_band['countries'] = ', '.join(countries)

        min_fee = bands.order_by('fee').first().fee
        max_fee = bands.order_by('fee').last().fee
        if min_fee == max_fee:
            display_band[currency.code] = min_fee
        else:
            display_band[currency.code] = f'{min_fee}&ndash;{max_fee}'
        return display_band

    def build_segments(level, size, currency, kwargs):
        display_bands = []
        bands = supporter_models.Band.objects.filter(**kwargs)
        fees = [band.fee for band in bands]
        span = max(fees) - min(fees)
        if span == 0:
            segments = [
                (0, 1)
            ]
        else:
            segments = [
                (.666667, 1),
                (.333334, .666666),
                (0, .333333),
            ]
            # segments = [
            #     (.75, 1),
            #     (.5, .74999),
            #     (.25, .49999),
            #     (0, .24999),
            # ]
        for start, end in segments:
            lower_end = min(fees) + (span * start)
            higher_end = min(fees) + (span * end)
            kwargs['fee__gte'] = lower_end
            kwargs['fee__lte'] = higher_end
            bands = supporter_models.Band.objects.filter(**kwargs)
            if not bands:
                continue
            display_band = build_display_band(level, size, currency, kwargs)
            display_bands.append(display_band)
        return display_bands

    display_band_table = []
    for level in supporter_models.SupportLevel.objects.all():
        for size in supporter_models.SupporterSize.objects.all():
            for currency in supporter_models.Currency.objects.all():
                kwargs = {
                    'current_supporter__active': True,
                    'fee__isnull': False,
                    'level': level,
                    'size': size,
                    'currency': currency,
                }
                bands = supporter_models.Band.objects.filter(**kwargs)
                if not bands:
                    continue
                display_bands = build_segments(level, size, currency, kwargs)
                display_band_table.extend(display_bands)

    return display_band_table


def last_five_years():
    return [timezone.now().year - num for num in [5, 4, 3, 2, 1]]


def get_indicator_by_country(
        indicator: str,
        year: int
    ) -> dict[str, decimal.Decimal]:
    data = utils.open_saved_world_bank_data(indicator, year)
    # The next few lines are written defensively because of the variation
    # in the JSON received from the World Bank API.
    if not data:
        return {}
    _metadata, country_records = data
    if not country_records:
        return {}
    return {each['countryiso3code']: each['value'] for each in country_records}


def countries_with_billing_agents():
    return {
        a.country for a in supporter_models.BillingAgent.objects.filter(
            country__isnull=False
        )
    }


def get_base_band(level=None, country=None):
    bases = supporter_models.Band.objects.filter(category='base')
    query = Q()

    # Check if there is a base for this country on each level.
    # If so, filter by the country. If not, exclude bands
    # that fall under a country-specific billing agent.
    bases_for_country = bases.all().filter(country=country).count()
    num_levels = supporter_models.SupportLevel.objects.count()
    agent_countries = countries_with_billing_agents()
    if country in agent_countries and bases_for_country == num_levels:
        query &= Q(country=country)
    else:
        query &= ~Q(country__in=agent_countries)

    # Check if there is a base on this level for each country
    # (plus one for the default: no country).
    # If so, filter by the level.
    level = level or utils.get_standard_support_level()
    bases_on_level = bases.all().filter(level=level).count()
    if level and bases_on_level == len(agent_countries) + 1:
        query &= Q(level=level)

    try:
        return bases.filter(query).latest()
    except supporter_models.Band.DoesNotExist:
        logger.warning('No base band found for parameters ' + str(query))
        try:
            return bases.latest()
        except supporter_models.Band.DoesNotExist:
            logger.warning('No base bands found.')


def get_base_bands():
    # We create the result set this crude way to avoid being
    # reliant on postgreSQL for order_by + distinct.
    # base_bands will only ever be a handful of items.
    base_bands = set()
    # Get any country-specific base bands (by billing agent)
    for country in countries_with_billing_agents():
        for level in supporter_models.SupportLevel.objects.all():
            band = get_base_band(level=level, country=country)
            if band:
                base_bands.add(band)
            else:
                logger.warning(f'Missing base band for level {level} in country {country}')
    # Get non-country-specific base bands
    for level in supporter_models.SupportLevel.objects.all():
        band = get_base_band(level=level, country=None)
        if band:
            base_bands.add(band)
    return base_bands


def latest_multiplier_for_indicator(
        indicator: str,
        measure_key: str,
        base_key: str,
        warning: str,
    ) -> Tuple[decimal.Decimal, str]:
    """
    Checks last five years for specified indicator
    :indicator: Word Bank indicator code such as PA.NUS.FCRF or NY.GNP.PCAP.CD
    :measure_key: the key to use for the record being calculated, e.g. USA
    :base_key: the key to use from the base band, e.g. GBR
    :warning: the string to display to the end user explaining the lack of data
    :return: tuple with the measure as decimal.Decimal plus a string warning if
             matching data could not be found
    """

    multiplier = decimal.Decimal(1)

    if base_key == '---':
        # The plugin is being configured
        # via the admin interface
        warning = ''
        return multiplier, warning

    base_improperly_configured = 0
    for year in reversed(last_five_years()):
        data = get_indicator_by_country(indicator, year)
        if base_key not in data or not data[base_key]:
            base_improperly_configured += 1
        elif measure_key in data and data[measure_key]:
            multiplier = data[measure_key] / data[base_key]
            warning = ''
            return multiplier, warning

    if base_improperly_configured == 5:
        logger.error(
            f'{base_key} not found in the data for indicator {indicator}. '
            f'World Bank data may be missing or the base band '
            f'may not be properly configured.'
        )

    return multiplier, warning


def latest_dataset_for_indicator(indicator):
    try:
        return cms_models.MediaFile.objects.filter(
            label__contains=indicator,
        ).latest('uploaded')
    except cms_models.MediaFile.DoesNotExist:
        return None


def get_settings_for_display():
    """
    Get settings for display in manager
    """
    file_path = os.path.join(
        settings.BASE_DIR,
        'plugins',
        plugin_settings.SHORT_NAME,
        'install',
        'settings.json',
    )
    display_settings = []
    with open(file_path, 'r') as file_ref:
        for default_setting in utils.load_json_with_decimals(file_ref):
            setting = core_models.Setting.objects.get(
                group__name=default_setting['group']['name'],
                name=default_setting['setting']['name'],
            )
            display_settings.append(setting)
    return display_settings


def determine_billing_agent(country):
    """
    :country: a two-letter country code like the ones
              django_countries stores in the database
    :return: BillingAgent
    """
    try:
        agent = supporter_models.BillingAgent.objects.get(country=country)
        return agent
    except supporter_models.BillingAgent.DoesNotExist:
        try:
            agent = supporter_models.BillingAgent.objects.get(default=True)
            return agent
        except supporter_models.BillingAgent.DoesNotExist:
            logger.error(
                'No billing agent has been set as default'
            )


def keep_default_unique(obj):
    """
    Checks other instances to see if there is one with default=True
    and sets it to default=False
    :obj: an unsaved model instance with a property named 'default'
    """
    if obj.default:
        type(obj).objects.filter(default=True).exclude(pk=obj.pk).update(
            default=False,
        )


def get_total_revenue(currency=None):
    if not currency:
        base_band = get_base_band(level=None, country=None)
        if base_band:
            currency = base_band.currency
        else:
            return 0, None
    revenue = 0
    for supporter_currency in supporter_models.Currency.objects.all():
        revenue_in_currency = supporter_models.Supporter.objects.filter(
            active=True,
            band__isnull=False,
            band__currency=supporter_currency
        ).aggregate(
            Sum('band__fee')
        )['band__fee__sum']
        target_exchange_rate, _warnings = currency.exchange_rate()
        origin_exchange_rate, _warnings = supporter_currency.exchange_rate()
        revenue += revenue_in_currency * (target_exchange_rate / origin_exchange_rate)

    return round(revenue), currency
