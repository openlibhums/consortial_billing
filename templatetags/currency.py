from decimal import Decimal

from django.contrib.humanize.templatetags.humanize import intcomma
from django import template

from plugins.consortial_billing import plugin_settings
from utils import setting_handler

register = template.Library()


@register.simple_tag()
def convert(value, currency, action="display"):
    plugin = plugin_settings.get_self()
    base_currency = setting_handler.get_plugin_setting(plugin, 'base_currency', None, create=False).value
    if currency == base_currency:
        if action == "display":
            return intcomma(value)
        else:
            return value

    ex_rate = setting_handler.get_plugin_setting(plugin, 'ex_rate_{0}'.format(currency), None, create=False)

    if ex_rate:
        ex_rate = ex_rate.value
        if action == "display":
            return "{0} (ex rate {1})".format(intcomma(round((float(value) / float(ex_rate)), 2)), ex_rate)
        else:
            return round((float(value) / float(ex_rate)), 2)


@register.simple_tag()
def convert_all(dict):
    plugin = plugin_settings.get_self()
    base_currency = setting_handler.get_plugin_setting(plugin, 'base_currency', None, create=False).value
    total_in_local_currency = Decimal()

    for item in dict:
        currency = item.get('currency')
        price = item.get('price')

        if currency == base_currency:
            total_in_local_currency = total_in_local_currency + price

        else:

            ex_rate = setting_handler.get_plugin_setting(plugin, 'ex_rate_{0}'.format(currency), None, create=False)

            if ex_rate:
                ex_rate = Decimal(ex_rate.value)

                total_in_local_currency = total_in_local_currency + (price / ex_rate)

    return intcomma(round(total_in_local_currency, 2))


@register.simple_tag()
def convert_multiplier(value, currency, multiplier):
    conversion = convert(value, currency, 'multiplication')

    return (conversion * float(multiplier) + conversion)


@register.simple_tag()
def multiply(value, multiplier):
    return (value * float(multiplier)) + value
