from django.core.urlresolvers import reverse
from django.template.loader import render_to_string

from utils import setting_handler
from plugins.consortial_billing import plugin_settings
from journal import models as journal_models


def nav_hook(context):
    supporters_url = reverse('consortial_supporters')
    signup_url = reverse('consortial_signup')
    request = context['request']

    plugin = plugin_settings.get_self()
    short_org_name = setting_handler.get_plugin_setting(plugin, 'organisation_short_name', None, create=True,
                                                        pretty='Organisation Short Name')
    display_nav = setting_handler.get_plugin_setting(plugin, 'display_nav', None, create=True,
                                                        pretty='Display nav item', types='boolean').processed_value

    journals_setting = setting_handler.get_plugin_setting(plugin_settings.get_self(),
                                                          'journal_display',
                                                          None,
                                                          create=True,
                                                          pretty='Journal Display',
                                                          ).value
    journal_pks = []
    if journals_setting:
        journal_pks = [int(pk) for pk in journals_setting.split(',')]
    if (request.journal and request.journal.id in journal_pks) or (not request.journal and request.press):
        item = {
            'link_name': 'Support {0}'.format(short_org_name.value),
            'link': '',
            'has_sub_nav': True,
            'sub_nav_items': [
                {'link_name': 'Library Sign Up',
                 'link': signup_url},
                {'link_name': 'Supporting Institutions',
                 'link': supporters_url}
            ]
        }
        nav = render_to_string('elements/nav_element.html', {'item': item})

        return nav
    return ''
