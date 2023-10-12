__copyright__ = "Copyright 2023 Birkbeck, University of London"
__author__ = "Open Library of Humanities"
__license__ = "AGPL v3"
__maintainer__ = "Open Library of Humanities"

import os
import requests
import json
from tqdm import tqdm

from django.utils import timezone
from django.core.files.base import ContentFile

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


def generate_new_demo_data():
    from plugins.consortial_billing import forms
    data = {}

    levels = models.SupportLevel.objects.all().order_by('-order')

    data['thead'] = []
    for level in levels:
        data['thead'].append(level.name)

    data['tbody'] = {}
    for size in models.SupporterSize.objects.all().order_by('multiplier'):
        data['tbody'][size.name] = {}
        for country, curr_code, region in tqdm(DEMO_COUNTRIES):
            for level in levels:
                currency, _ = models.Currency.objects.get_or_create(
                    code=curr_code,
                    region=region,
                )
                band_form = forms.BandForm({
                    'size': size,
                    'level': level,
                    'country': country,
                    'currency': currency,
                })
                if not band_form.is_valid():
                    logger.error(band_form.errors)
                band = band_form.save(commit=False)
                country_name = band.country.name
                if country_name == 'United States of America':
                    country_name = 'USA'
                elif country_name == 'United Kingdom':
                    country_name = 'UK'
                if country_name not in data['tbody'][size.name]:
                    data['tbody'][size.name][country_name] = {}
                cell = {
                    'fee': band.fee,
                    'currency': band.currency.symbol
                }
                data['tbody'][size.name][country_name][level.name] = cell

    return data


def update_demo_band_data():
    data = generate_new_demo_data()
    data_json = json.dumps(data, separators=(',', ':'))
    filename = os.path.join(plugin_settings.SHORT_NAME, DEMO_DATA_FILENAME)
    return save_media_file(filename, data_json)


def get_saved_demo_band_data():
    filename = os.path.join(plugin_settings.SHORT_NAME, DEMO_DATA_FILENAME)
    file = cms_models.MediaFile.objects.get(label=filename)
    with file.file.open('r') as file_ref:
        return json.loads(file_ref.read())
