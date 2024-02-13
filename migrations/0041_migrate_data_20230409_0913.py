# Generated by Django 3.2.18 on 2023-04-09 08:13

from django.db import migrations
from django.utils import timezone

NOW = timezone.now()


def migrate_data(apps, schema_editor):

    Institution = apps.get_model('consortial_billing', 'Institution')
    SupportLevel = apps.get_model('consortial_billing', 'SupportLevel')
    SupporterSize = apps.get_model('consortial_billing', 'SupporterSize')
    Currency = apps.get_model('consortial_billing', 'Currency')
    Banding = apps.get_model('consortial_billing', 'Banding')
    Account = apps.get_model('core', 'Account')

    def record_old_band(supporter):
        if not supporter.banding:
            return

        supporter.internal_notes = \
            f'Pre-2024 banding:\n'\
            f'{supporter.banding.name}\n'\
            f'Fee: {supporter.banding.default_price} {supporter.banding.currency}\n'\
            f'Agent: {supporter.banding.billing_agent.name if supporter.banding.billing_agent else ""}\n'\
            f'Display: {"Yes" if supporter.banding.display else "No"}\n'\
            f'Redirect URL: {supporter.banding.redirect_url if supporter.banding.redirect_url else ""}\n'\
            f'Size: {supporter.banding.size}'\

    # Institution.supporter_level -> Institution.band_temp.level
    def determine_level(supporter):
        # Regarding levels, it is not worth trying to parse Gold, Silver, etc.,
        # because those bandings are not actually used in the old data.
        if supporter.supporter_level and 'higher' in supporter.supporter_level.name.lower():
            return supporter.supporter_level
        else:
            level, created = SupportLevel.objects.get_or_create(name='Standard')
            return level

    # Institution.banding.name -> Institution.band_temp.size_temp
    # Institution.banding.size -> Institution.band_temp.size_temp
    def determine_size(supporter):

        size_descriptor = supporter.banding.size.capitalize()
        name = f'{size_descriptor}'

        if '0-5' in supporter.banding.name:
            description = '0-4,999 students'
        elif '000-9' in supporter.banding.name:
            description = '5,000-9,999 students'
        elif '10' in supporter.banding.name:
            description = '10,000+ students'
        else:
            description = ''

        size_temp, created = SupporterSize.objects.get_or_create(
            name=name,
        )
        if description and not size_temp.description:
            size_temp.description = description
            size_temp.save()
        return size_temp

    # Country setup
    COUNTRIES_NORMALIZED = {
        'Australia': 'AU',
        'Austria': 'AT',
        'Belgium': 'BE',
        'Canada': 'CA',
        'Denmark': 'DK',
        'ESPAÑA': 'ES',
        'Finland': 'FI',
        'France': 'FR',
        'Germany': 'DE',
        'Greece': 'GR',
        'Hong Kong': 'HK',
        'Hungary': 'HU',
        'Ireland': 'IE',
        'Israel': 'IL',
        'New Zealand': 'NZ',
        'Norway': 'NO',
        'Portugal': 'PT',
        'Schweiz': 'CH',
        'Singapore': 'SG',
        'Spain': 'ES',
        'Sweden': 'SE',
        'Switzerland': 'CH',
        'The Netherlands': 'NL',
        'The United Kingdom': 'GB',
        'United States': 'US',
        'The United States of America': 'US',
        'United States of America': 'US',
        'USA': 'US',
    }

    # Institution.country -> Institution.band_temp.country
    def determine_country(supporter):
        country = COUNTRIES_NORMALIZED[supporter.country]
        return country

    # Currency setup
    # Move all currencies to GBP, USD, and EUR
    OLD_NEW_CURRENCIES = {
        'AUD': 'USD',
        'CAD': 'USD',
        'CZK': 'EUR',
        'EUR': 'EUR',
        'GBP': 'GBP',
        'HKD': 'USD',
        'ILS': 'USD',
        'NOK': 'EUR',
        'NZD': 'USD',
        'SGD': 'USD',
        'USD': 'USD',
    }

    # Need to match each new currency to a region code
    # for auto exchange rates to work
    CURRENCIES_REGIONS = {
        'EUR': 'EMU',
        'GBP': 'GBR',
        'USD': 'USA',
    }

    # Institution.banding.currency -> Institution.band_temp.currency_temp
    def determine_currency(supporter):

        code = OLD_NEW_CURRENCIES[supporter.banding.currency]
        region = CURRENCIES_REGIONS[code]
        currency_temp, created = Currency.objects.get_or_create(
            code=code,
            region=region,
        )
        return currency_temp

    # Fee setup
    # Exchange rates are World Bank averages from 2021
    USD_EX = {
        'AUD': 1.33122425957081,
        'CAD': 1.2538769021268,
        'CZK': 21.6781666666667,
        'EUR': 0.84549413889045,
        'GBP': 0.727064944688322,
        'HKD': 7.77325,
        'ILS': 3.23019832251082,
        'NOK': 8.59,
        'NZD': 1.4138,
        'SGD': 1.34348333333333,
        'USD': 1,
    }

    # Institution.banding.fee -> Institution.band_temp.fee
    def determine_fee(supporter):
        old_currency = supporter.banding.currency
        new_currency = determine_currency(supporter).code
        exchange_rate = USD_EX[new_currency] / USD_EX[old_currency]
        fee = supporter.banding.default_price * exchange_rate
        return fee

    # Institution.banding -> Institution.band_temp
    def determine_band(supporter):

        if not supporter.banding:
            return Banding.objects.filter(base=True).order_by('-datetime').first()

        band_temp = supporter.banding
        band_temp.level = determine_level(supporter)
        band_temp.size_temp = determine_size(supporter)
        band_temp.country = determine_country(supporter)
        band_temp.currency_temp = determine_currency(supporter)
        band_temp.fee = determine_fee(supporter)
        band_temp.datetime = NOW
        band_temp.billing_agent = supporter.billing_agent
        band_temp.save()
        return band_temp

    # Institution.email_address -> Institution.contacts.email
    # Institution.first_name -> Institution.contacts.first_name
    # Institution.last_name -> Institution.contacts.last_name
    def determine_contact(supporter):
        if not supporter.email_address:
            return
        email = supporter.email_address.lower()

        try:
            account = Account.objects.get(email=email)
        except Account.DoesNotExist:
            account = Account.objects.create(
                email=email,
                username=email,
                first_name=supporter.first_name,
                last_name=supporter.last_name,
            )
        return account

    for supporter in Institution.objects.all():
        record_old_band(supporter)
        band_temp = determine_band(supporter)
        if band_temp:
            supporter.band_temp = band_temp
            supporter.country_temp = band_temp.country
        contact = determine_contact(supporter)
        if contact:
            supporter.contacts.add(contact)
        supporter.save()


class Migration(migrations.Migration):

    dependencies = [
        ('consortial_billing', '0040_revise_data_model_20230407_1640'),
    ]

    operations = [

        # MIGRATE DATA
        migrations.RunPython(
            migrate_data,
            reverse_code=migrations.RunPython.noop
        ),

    ]
