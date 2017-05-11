import requests

from django.core.management.base import BaseCommand

from plugins.consortial_billing import models, plugin_settings
from utils import setting_handler


class Command(BaseCommand):
    """
    Fetches exchange rates
    """

    help = "Deletes duplicate settings."

    def handle(self, *args, **options):
        """Fetches exchange rates for GBP

        :param args: None
        :param options: None
        :return: None
        """
        plugin = plugin_settings.get_self()
        base_currency = setting_handler.get_plugin_setting(plugin, 'base_currency', None, create=False).value
        currencies = models.Renewal.objects.all().values('currency').distinct()
        api_call = requests.get('http://api.fixer.io/latest?base={0}'.format(base_currency)).json()

        for currency in currencies:
            currency_code = currency.get('currency')
            if currency_code != base_currency:
                rate = api_call['rates'].get(currency_code)
                value = setting_handler.get_plugin_setting(plugin, 'ex_rate_{0}'.format(currency_code),
                                                            None,
                                                            create=True,
                                                            pretty='Ex Rate GBP',
                                                            fallback='')
                setting_handler.save_plugin_setting(plugin, value.setting.name, rate, None)
