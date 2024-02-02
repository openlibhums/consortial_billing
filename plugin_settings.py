from utils import plugins
from utils.install import update_settings
from events import logic as events_logic
from django.core.management import call_command
from django.conf import settings

PLUGIN_NAME = 'Consortial Billing'
DISPLAY_NAME = 'Supporters'
SHORT_NAME = 'consortial_billing'
MANAGER_URL = 'supporters_manager'
DESCRIPTION = 'This plugin helps presses manage consortial support'
AUTHOR = 'Open Library of Humanities'
VERSION = '2.0'
JANEWAY_VERSION = "1.5.0"
IS_WORKFLOW_PLUGIN = False

ON_SIGNUP = "on_signup"

RATE_INDICATOR = 'PA.NUS.FCRF'
DISPARITY_INDICATOR = 'NY.GNP.PCAP.CD'


class ConsortialBillingPlugin(plugins.Plugin):
    plugin_name = PLUGIN_NAME
    display_name = DISPLAY_NAME
    description = DESCRIPTION
    author = AUTHOR
    short_name = SHORT_NAME

    manager_url = MANAGER_URL

    version = VERSION
    janeway_version = JANEWAY_VERSION

    is_workflow_plugin = IS_WORKFLOW_PLUGIN
    press_wide = True


def install(fetch_data=False):
    ConsortialBillingPlugin.install()
    update_settings(
        file_path=f'plugins/{SHORT_NAME}/install/settings.json'
    )
    if fetch_data and not settings.IN_TEST_RUNNER:
        call_command('fetch_world_bank_data', RATE_INDICATOR)
        call_command('fetch_world_bank_data', DISPARITY_INDICATOR)


def hook_registry():
    return {
        'press_admin_nav_block': {
            'module': 'plugins.consortial_billing.hooks',
            'function': 'admin_hook'
        },
    }


def register_for_events():
    # Plugin modules can't be imported until plugin is loaded
    from plugins.consortial_billing.notifications import emails

    events_logic.Events.register_for_event(
        ON_SIGNUP,
        emails.email_agent_about_signup,
    )

    events_logic.Events.register_for_event(
        ON_SIGNUP,
        emails.email_supporter_to_confirm,
    )
