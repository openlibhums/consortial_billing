__copyright__ = "Copyright 2023 Birkbeck, University of London"
__author__ = "Open Library of Humanities"
__license__ = "AGPL v3"
__maintainer__ = "Open Library of Humanities"

import os
import requests
import json
import decimal
from typing import List
from tqdm import tqdm
from urllib.parse import urlencode

from django.utils import timezone
from django.core.files.base import ContentFile
from django.conf import settings
from django.contrib import admin

from cms import models as cms_models
from utils import setting_handler
from plugins.consortial_billing import plugin_settings, models
from utils.logger import get_logger

logger = get_logger(__name__)


DEMO_COUNTRIES = [
    # 2-letter country code
    # 3-letter currency code
    # 3-letter region code in Word Bank data, e.g. EMU for Euro
    ('IN', 'USD', 'USA'),
    ('ZA', 'USD', 'USA'),
    ('BR', 'USD', 'USA'),
    ('CZ', 'EUR', 'EMU'),
    ('IT', 'EUR', 'EMU'),
    ('JP', 'USD', 'USA'),
    ('FR', 'EUR', 'EMU'),
    ('GB', 'GBP', 'GBR'),
    ('DE', 'EUR', 'EMU'),
    # ('DK', 'EUR', 'EMU'),
    ('US', 'USD', 'USA'),
    # ('NO', 'EUR', 'EMU'),
]
DEMO_DATA_FILENAME = 'band_demo_data.json'


def setting(name, journal=None):
    group = 'plugin:consortial_billing'
    return setting_handler.get_setting(group, name, journal).processed_value


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


def form_world_bank_url(indicator, year):
    base = 'https://api.worldbank.org/v2/country/all/indicator/'
    params = f'?date={year}&format=json&per_page=500'
    return base + indicator + params


def save_file_for_indicator_and_year(indicator, year, content):
    filename = os.path.join(
        plugin_settings.SHORT_NAME,
        f'{indicator}_{year}.json',
    )
    save_media_file(filename, content)


def fetch_world_bank_data(indicator, year):
    """
    Gets API data and calls save_media_file if status is 200
    :indicator: A world bank indicator string such as PA.NUS.FCRF
    :year: YYYY as int
    :return: status code
    """
    url = form_world_bank_url(indicator, year)
    response = requests.get(url)
    if response.status_code == 200:
        save_file_for_indicator_and_year(indicator, year, response.content)
    return response.status_code


def load_json_with_decimals(file_ref):
    """
    Loads a JSON media file with decimals for all numbers.
    :file_ref: An open file reference
    :returns: Python-loaded JSON with decimal.Decimal for numbers
    """
    return json.loads(
        file_ref.read(),
        parse_float=decimal.Decimal,
        parse_int=decimal.Decimal,
    )


def open_json_media_file(filename):
    """
    Opens a JSON file saved as a Janeway media file.
    Logs an error if the file is not found.
    """
    try:
        file = cms_models.MediaFile.objects.get(label=filename)
        with file.file.open('r') as file_ref:
            return load_json_with_decimals(file_ref)
    except cms_models.MediaFile.DoesNotExist as e:
        logger.error(e)
        logger.error(f'...while trying to load {filename}')
        return []


def open_saved_world_bank_data(indicator: str, year: int) -> List:
    """
    Opens saved API data for indicator
    :indicator: A world bank indicator string such as PA.NUS.FCRF
    :return: a Pythonic JSON object with decimal.Decimal for all numbers
    """

    filename = os.path.join(
        plugin_settings.SHORT_NAME,
        f'{indicator}_{year}.json',
    )
    return open_json_media_file(filename)


def get_abstract_band(size, level, country, currency):
    from plugins.consortial_billing import forms
    band_form = forms.BandForm({
        'size': size,
        'level': level,
        'country': country,
        'currency': currency,
        'category': 'calculated',
    })
    if not band_form.is_valid():
        logger.error(band_form.errors)
    return band_form.save(commit=False)


def short_country_name(country, max_length=10):
    special_abbreviations = {
        'GB': 'UK',
        'CH': 'Switz.',
    }
    if len(country.name) > max_length:
        if country.code in special_abbreviations:
            return special_abbreviations[country.code]
        else:
            return country.code
    else:
        return country.name


def iter_demo_countries():
    if not settings.IN_TEST_RUNNER:
        return tqdm(DEMO_COUNTRIES)
    else:
        return DEMO_COUNTRIES


def get_standard_support_level():
    """
    :return: SupportLevel object or None
    """
    try:
        return models.SupportLevel.objects.get(default=True)
    except models.SupportLevel.DoesNotExist:
        logger.error(
            'No default support level found. '
            'Using the support level ordered last, '
            'but that may produce unintended results. '
            'For best results, set a level as the default.'
        )
        return models.SupportLevel.objects.all().last()


def make_table_of_higher_supporters_by_country_and_level():
    standard_level = get_standard_support_level()
    levels = models.SupportLevel.objects.exclude(
        pk=standard_level.pk
    ).order_by('-order')
    size = models.SupporterSize.objects.all().first()

    data = {}
    data['thead'] = []
    for level in levels:
        data['thead'].append(str(level))

    data['tbody'] = {}
    for country, curr_code, region in iter_demo_countries():
        currency, _ = models.Currency.objects.get_or_create(
            code=curr_code,
            region=region,
        )
        for level in levels:
            band = get_abstract_band(size, level, country, currency)
            country_name = short_country_name(band.country)
            if country_name not in data['tbody']:
                data['tbody'][country_name] = {}
            cell = {
                'fee': band.fee,
                'currency': band.currency.symbol
            }
            data['tbody'][country_name][str(level)] = cell

    return data


def make_table_of_standard_supporters_by_country_and_size():
    sizes = models.SupporterSize.objects.all().order_by('multiplier')
    standard_level = get_standard_support_level()

    data = {}
    data['thead'] = []
    for size in sizes:
        data['thead'].append(str(size))

    data['tbody'] = {}
    for country, curr_code, region in iter_demo_countries():
        currency, _ = models.Currency.objects.get_or_create(
            code=curr_code,
            region=region,
        )
        for size in sizes:
            band = get_abstract_band(size, standard_level, country, currency)
            country_name = short_country_name(band.country)
            if country_name not in data['tbody']:
                data['tbody'][country_name] = {}
            cell = {
                'fee': band.fee,
                'currency': band.currency.symbol
            }
            data['tbody'][country_name][str(size)] = cell

    return data


def make_table_showing_all_levels_by_country_and_size():
    levels = models.SupportLevel.objects.all().order_by('-order')

    data = {}
    data['thead'] = []
    for level in levels:
        data['thead'].append(level.name)

    data['tbody'] = {}
    for size in models.SupporterSize.objects.all().order_by('multiplier'):
        size_display = str(size)
        data['tbody'][size_display] = {}
        for country, curr_code, region in iter_demo_countries():
            for level in levels:
                currency, _ = models.Currency.objects.get_or_create(
                    code=curr_code,
                    region=region,
                )
                band = get_abstract_band(size, level, country, currency)
                country_name = short_country_name(band.country)
                if country_name not in data['tbody'][size_display]:
                    data['tbody'][size_display][country_name] = {}
                cell = {
                    'fee': band.fee,
                    'currency': band.currency.symbol
                }
                data['tbody'][size_display][country_name][level.name] = cell

    return data


def generate_new_demo_data():
    return [
        make_table_of_higher_supporters_by_country_and_level(),
        make_table_of_standard_supporters_by_country_and_size()
    ]


def update_demo_band_data():
    data_json = json.dumps(generate_new_demo_data(), separators=(',', ':'))
    filename = os.path.join(plugin_settings.SHORT_NAME, DEMO_DATA_FILENAME)
    return save_media_file(filename, data_json)


def get_saved_demo_band_data() -> List:
    filename = os.path.join(plugin_settings.SHORT_NAME, DEMO_DATA_FILENAME)
    return open_json_media_file(filename)


def get_ror(name):
    """ Gets a ROR that exactly matches an organization name
    """
    base = 'https://api.ror.org/organizations'
    params = { 'affiliation': name }
    response = requests.get(f'{ base }?{ urlencode(params) }')
    try:
        response.raise_for_status()
        content = json.loads(response.content)
        record = content['items'].pop() if content['items'] else None
        if record and record['chosen'] and record['matching_type'] == 'EXACT':
            return record['organization']['id']
    except requests.HTTPError as error:
        logger.error('Unexpected ROR API response:')
        logger.error(error)
