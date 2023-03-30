from decimal import Decimal

from django.contrib.humanize.templatetags.humanize import intcomma
from django import template

from plugins.consortial_billing import plugin_settings
from utils import setting_handler

register = template.Library()


@register.simple_tag()
def convert(value, currency, action="display"):

    base_currency = setting_handler.get_setting(
        'plugin:consortial_billing',
        'base_currency',
        None,
    ).value
    if currency == base_currency:
        if action == "display":
            return intcomma(value)
        else:
            return value

    ex_rate = setting_handler.get_setting(
        'plugin:consortial_billing',
        'ex_rate_{0}'.format(currency.upper()),
        None,
    )

    if ex_rate:
        ex_rate = ex_rate.value
        if action == "display":
            return "{0} (ex rate {1})".format(intcomma(round((float(value) / float(ex_rate)), 2)), ex_rate)
        else:
            return round((float(value) / float(ex_rate)), 2)


@register.simple_tag()
def convert_all(dict):
    base_currency = setting_handler.get_setting(
        'plugin:consortial_billing',
        'base_currency',
        None,
    ).value
    total_in_local_currency = Decimal()

    for item in dict:
        currency = item.get('currency')
        price = item.get('price')

        if currency == base_currency:
            total_in_local_currency = total_in_local_currency + price

        else:

            ex_rate = setting_handler.get_setting(
                'plugin:consortial_billing',
                'ex_rate_{0}'.format(currency.upper()),
                None,
            )

            if ex_rate:
                ex_rate = Decimal(ex_rate.value)

                total_in_local_currency = total_in_local_currency + (price / ex_rate)

    return intcomma(round(total_in_local_currency, 2))


@register.simple_tag()
def convert_multiplier(value, currency, multiplier):
    conversion = convert(value, currency, 'multiplication')

    return float(conversion) * float(multiplier)


@register.simple_tag()
def multiply(value, multiplier):
    return float(value) * float(multiplier)


@register.simple_tag()
def discount(value, discount):
    return intcomma(round(value - (float(value) * float(discount) / 100)), 2)


@register.simple_tag()
def reverse_discount(value, discount):
    return intcomma(round(value + (float(value) * float(discount) / 100)), 2)


@register.simple_tag()
def default_currency():
    return setting_handler.get_setting(
        'plugin:consortial_billing',
        'base_currency',
        None,
    ).value


@register.simple_tag()
def convert_to(value, currency_to):
    currency_from = default_currency()

    if currency_to == currency_from:
        return value

    ex_rate = setting_handler.get_setting(
        'plugin:consortial_billing',
        'ex_rate_{0}'.format(currency_to.upper()),
        None,
    ).value

    return round(float(ex_rate) * float(value))



