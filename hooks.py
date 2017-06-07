from django.core.urlresolvers import reverse
from utils import setting_handler
from consortial_billing import plugin_settings


def nav_hook(context):
    supporters_url = reverse('consortial_supporters')
    signup_url = reverse('consortial_signup')

    plugin = plugin_settings.get_self()
    short_org_name = setting_handler.get_plugin_setting(plugin, 'organisation_short_name', None, create=True,
                                                        pretty='Organisation Short Name')
    display_nav = setting_handler.get_plugin_setting(plugin, 'display_nav', None, create=True,
                                                        pretty='Display nav item', types='boolean').processed_value

    if display_nav:
        return '<li><a href="{0}">Support {1}</a>' \
               '<ul class="dropdown menu" data-dropdown-menu>' \
               '<li><a href="{0}">Library Sign Up</a></li>' \
               '<li><a href="{2}">Supporting Institutions</a></li>' \
               '</ul></li>'.format(signup_url, short_org_name.value, supporters_url)
    return ''
