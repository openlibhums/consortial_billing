__copyright__ = "Copyright 2023 Birkbeck, University of London"
__author__ = "Open Library of Humanities"
__license__ = "AGPL v3"
__maintainer__ = "Open Library of Humanities"

import os
import requests
import json

from django.utils import timezone
from django.core.files.base import ContentFile

from cms import models as cms_models
from utils import setting_handler
from plugins.consortial_billing import plugin_settings

from utils.logger import get_logger

logger = get_logger(__name__)


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
