from django.core.urlresolvers import reverse
from django.shortcuts import render
from django.template.loader import render_to_string

from utils import setting_handler
from plugins.consortial_billing import plugin_settings


def nav_hook(context):
    supporters_url = reverse('consortial_supporters')
    signup_url = reverse('consortial_signup')

    plugin = plugin_settings.get_self()
    short_org_name = setting_handler.get_plugin_setting(plugin, 'organisation_short_name', None, create=True,
                                                        pretty='Organisation Short Name')
    display_nav = setting_handler.get_plugin_setting(plugin, 'display_nav', None, create=True,
                                                        pretty='Display nav item', types='boolean').processed_value

    if display_nav:
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
