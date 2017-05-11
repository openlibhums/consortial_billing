from django.contrib.humanize.templatetags.humanize import intcomma
from django import template

from plugins.consortial_billing import plugin_settings
from utils import setting_handler

register = template.Library()


@register.simple_tag()
def convert(value, currency, action="display"):
    if currency == plugin_settings.BASE_CURRENCY:
        if action == "display":
            return intcomma(value)
        else:
            return value

    plugin = plugin_settings.get_self()
    ex_rate = setting_handler.get_plugin_setting(plugin, 'ex_rate_{0}'.format(currency), None, create=False)

    if ex_rate:
        ex_rate = ex_rate.value
        if action == "display":
            return "{0} (ex rate {1})".format(intcomma(round((float(value) / float(ex_rate)), 2)), ex_rate)
        else:
            return round((float(value) / float(ex_rate)), 2)