__copyright__ = "Copyright 2023 Birkbeck, University of London"
__author__ = "Open Library of Humanities"
__license__ = "AGPL v3"
__maintainer__ = "Open Library of Humanities"

import os
import requests
import json

from django.core.files.base import ContentFile
from django.core.exceptions import ImproperlyConfigured
from django.utils import timezone

from utils import setting_handler
from plugins.consortial_billing import models, plugin_settings
from cms import models as cms_models
from core import models as core_models

from utils.logger import get_logger

logger = get_logger(__name__)


def setting(name, journal=None):
    group = 'plugin:consortial_billing'
    return setting_handler.get_setting(group, name, journal).processed_value


def get_display_bands():
    """
    Compiles bands into display bands for use in
    an HTML table
    """

    def build_display_band(level, size, currency, kwargs):
        bands = models.Band.objects.filter(**kwargs)

        display_band = []

        display_band.append(level)

        display_band.append(size)

        countries = sorted(
            set(band.country.name for band in bands)
        )
        display_band.append(', '.join(countries))

        min_fee = bands.order_by('fee').first().fee
        max_fee = bands.order_by('fee').last().fee
        if min_fee == max_fee:
            display_band.append(f'{min_fee} {currency}')
        else:
            display_band.append(f'{min_fee}&ndash;{max_fee} {currency}')
        return display_band

    def build_segments(level, size, currency, kwargs):
        display_bands = []
        bands = models.Band.objects.filter(**kwargs)
        fees = [band.fee for band in bands]
        span = max(fees) - min(fees)
        if span == 0:
            segments = [
                (0, 1)
            ]
        else:
            segments = [
                (.75, 1),
                (.5, .74999),
                (.25, .49999),
                (0, .24999),
            ]
        for segment in segments:
            lower_end = min(fees) + (span * segment[0])
            higher_end = min(fees) + (span * segment[1])
            kwargs['fee__gte'] = lower_end
            kwargs['fee__lte'] = higher_end
            bands = models.Band.objects.filter(**kwargs)
            if not bands:
                continue
            display_band = build_display_band(level, size, currency, kwargs)
            display_bands.append(display_band)
        return display_bands

    display_band_table = []
    for level in models.SupportLevel.objects.all():
        for size in models.SupporterSize.objects.all():
            for currency in models.Currency.objects.all():
                kwargs = {
                    'supporter__active': True,
                    'fee__isnull': False,
                    'level': level,
                    'size': size,
                    'currency': currency,
                }
                bands = models.Band.objects.filter(**kwargs)
                if not bands:
                    continue
                display_bands = build_segments(level, size, currency, kwargs)
                display_band_table.extend(display_bands)

    return display_band_table


def save_media_file(filename, content):
    """
    Saves a media file outside of a request cycle
    :filename: filename
    :content: bytes
    :return: saved MediaFile
    """
    file, created = cms_models.MediaFile.objects.get_or_create(label=filename)
    if not created:
        file.unlink()
    content_file = ContentFile(content)
    file.uploaded = timezone.now()
    file.file.save(filename, content_file, save=True)
    return file


def last_five_years():
    return [timezone.now().year - num for num in [5, 4, 3, 2, 1]]


def fetch_world_bank_data(indicator, year):
    """
    Gets API data and calls save_media_file if status is 200
    :indicator: A world bank indicator string such as PA.NUS.FCRF
    :return: status code
    """
    base = 'https://api.worldbank.org/v2/country/all/indicator/'
    params = f'?date={year}&format=json&per_page=500'
    url = base + indicator + params
    response = requests.get(url)
    if response.status_code == 200:
        filename = os.path.join(
            plugin_settings.SHORT_NAME,
            f'{indicator}_{year}.json',
        )
        save_media_file(filename, response.content)
    return response.status_code


def open_saved_world_bank_data(indicator, year):
    """
    Opens saved API data for indicator
    :indicator: A world bank indicator string such as PA.NUS.FCRF
    :return: a Pythonic JSON object
    """

    filename = os.path.join(
        plugin_settings.SHORT_NAME,
        f'{indicator}_{year}.json',
    )
    file = cms_models.MediaFile.objects.get(label=filename)
    with file.file.open('r') as file_ref:
        return json.loads(file_ref.read())


def get_indicator_by_country(indicator, year):
    data = open_saved_world_bank_data(indicator, year)
    if not data[1]:
        return {}
    return {each['countryiso3code']: each['value'] for each in data[1]}


def get_exchange_rate(currency):
    """
    Gets most up-to-date multiplier for exchange rate
    based on latest GNI per capita figure
    :return: tuple of the indicator as int plus a string warning if
             matching country data could not be found
    """
    indicator = 'PA.NUS.FCRF'
    base = models.Band.objects.filter(base=True).latest('datetime')
    base_improperly_configured = 0
    for year in reversed(last_five_years()):
        rates = get_indicator_by_country(indicator, year)
        if (
            base.currency.region not in rates
            or not rates[base.currency.region]
        ):
            base_improperly_configured += 1
        elif currency.region in rates and rates[currency.region]:
            rate = rates[currency.region] / rates[base.currency.region]
            warning = ''
            return rate, warning

    if base_improperly_configured == 5:
        raise ImproperlyConfigured(
            f'{base.currency.region} not found in {indicator} data'
        )

    rate = 1
    warning = f"""
               <p>We don't have currency data for the region {currency.region},
               so we could not factor that in to the fee calculation</p>
               """
    return rate, warning


def get_economic_disparity(country):
    """
    Gets most up-to-date multiplier for economic disparity
    based on latest GNI per capita figure
    :return: tuple of the indicator as int plus a string warning if
             matching country data could not be found
    """
    indicator = 'NY.GNP.PCAP.CD'
    base = models.Band.objects.filter(base=True).latest('datetime')
    base_improperly_configured = 0
    for year in reversed(last_five_years()):
        gnis = get_indicator_by_country(indicator, year)
        if base.country.alpha3 not in gnis or not gnis[base.country.alpha3]:
            base_improperly_configured += 1
        elif country.alpha3 in gnis and gnis[country.alpha3]:
            disparity = gnis[country.alpha3] / gnis[base.country.alpha3]
            warning = ''
            return disparity, warning

    if base_improperly_configured == 5:
        raise ImproperlyConfigured(
            f'{base.country.alpha3} not found in {indicator} data'
        )

    disparity = 1
    warning = f"""
               <p>We don't have data for {country.name},
               so we could not factor that in to the fee calculation</p>
               """
    return disparity, warning


def get_base_band():
    try:
        return models.Band.objects.filter(
            base=True
        ).latest('datetime')
    except models.Band.DoesNotExist:
        return None


def get_latest_gni_data():
    try:
        return cms_models.MediaFile.objects.filter(
            label__contains='NY.GNP.PCAP.CD',
        ).latest('uploaded')
    except cms_models.MediaFile.DoesNotExist:
        return None


def get_latest_exchange_rate_data():
    try:
        return cms_models.MediaFile.objects.filter(
            label__contains='PA.NUS.FCRF',
        ).latest('uploaded')
    except cms_models.MediaFile.DoesNotExist:
        return None


def get_exchange_rates_for_display():
    """
    Get exchange rates from base rate in tuples
    """
    exchange_rates = []
    base_band = get_base_band()
    if base_band:
        for currency in models.Currency.objects.all():
            rate_usd, _warnings = currency.exchange_rate
            base_usd, _warnings = base_band.currency.exchange_rate
            rate = rate_usd / base_usd
            exchange_rates.append((rate, currency.code))
    return exchange_rates


def get_settings_for_display():
    """
    Get settings for display in manager
    """
    settings = []
    with open('install/settings.json', 'r') as file_ref:
        for default_setting in json.loads(file_ref.read()):
            setting = core_models.Setting.objects.get(
                group__name=default_setting['group']['name'],
                name=default_setting['setting']['name'],
            )
            settings.append(setting)
    return settings
