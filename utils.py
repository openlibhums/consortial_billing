__copyright__ = "Copyright 2023 Birkbeck, University of London"
__author__ = "Open Library of Humanities"
__license__ = "AGPL v3"
__maintainer__ = "Open Library of Humanities"

import os
import requests
import json
from datetime import datetime

from django.core.files.base import ContentFile
from django.utils import timezone

from utils import setting_handler
from plugins.consortial_billing import models, plugin_settings
from cms import models as cms_models

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
                    'institution__active': True,
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
    """
    indicator = 'PA.NUS.FCRF'
    base = models.Band.objects.filter(base=True).latest('datetime')
    for year in reversed(last_five_years()):
        rates = get_indicator_by_country(indicator, year)
        if currency.region in rates and rates[currency.region]:
            return rates[currency.region] / rates[base.currency.region]

    logger.warning(f'No {indicator} data for {currency.region}')
    return 1


def get_economic_disparity(country):
    """
    Gets most up-to-date multiplier for economic disparity
    based on latest GNI per capita figure
    """
    indicator = 'NY.GNP.PCAP.CD'
    base = models.Band.objects.filter(base=True).latest('datetime')
    for year in reversed(last_five_years()):
        gnis = get_indicator_by_country(indicator, year)
        if country.alpha3 in gnis and gnis[country.alpha3]:
            return gnis[country.alpha3] / gnis[base.country.alpha3]

    logger.warning(f'No {indicator} data for {country.name}')
    return 1
