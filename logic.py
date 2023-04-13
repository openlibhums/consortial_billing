__copyright__ = "Copyright 2023 Birkbeck, University of London"
__author__ = "Open Library of Humanities"
__license__ = "AGPL v3"
__maintainer__ = "Open Library of Humanities"

import json

from django.core.exceptions import ImproperlyConfigured
from django.utils import timezone

from core import models as core_models
from cms import models as cms_models
from plugins.consortial_billing import utils, models


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


def last_five_years():
    return [timezone.now().year - num for num in [5, 4, 3, 2, 1]]


def get_indicator_by_country(indicator, year):
    data = utils.open_saved_world_bank_data(indicator, year)
    if not data[1]:
        return {}
    return {each['countryiso3code']: each['value'] for each in data[1]}


def get_base_band():
    try:
        return models.Band.objects.filter(
            base=True
        ).latest('datetime')
    except models.Band.DoesNotExist:
        raise ImproperlyConfigured('No base band found')


def latest_multiplier_for_indicator(indicator, measure_key, base_key, warning):
    """
    Checks last five years for specified indicator
    :indicator: Word Bank indicator code such as PA.NUS.FCRF or NY.GNP.PCAP.CD
    :measure_key: the key to use for the record being calculated, e.g. USA
    :base_key: the key to use from the base band, e.g. GBR
    :warning: the string to display to the end user explaining the lack of data
    :return: tuple with the measure as int plus a string warning if
             matching data could not be found
    """
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
        raise ImproperlyConfigured(f'{base_key} not found in {indicator} data')

    multiplier = 1
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
    settings = []
    with open('install/settings.json', 'r') as file_ref:
        for default_setting in json.loads(file_ref.read()):
            setting = core_models.Setting.objects.get(
                group__name=default_setting['group']['name'],
                name=default_setting['setting']['name'],
            )
            settings.append(setting)
    return settings
