from utils import plugins
from utils.install import update_settings
from django.core.management import call_command

PLUGIN_NAME = 'Consortial Billing'
DISPLAY_NAME = 'Supporters'
SHORT_NAME = 'consortial_billing'
MANAGER_URL = 'supporters_manager'
DESCRIPTION = 'This plugin helps presses manage consortial support'
AUTHOR = 'Martin Paul Eve & Joseph Muller'
VERSION = '2.0'
JANEWAY_VERSION = "1.5.0"
IS_WORKFLOW_PLUGIN = False


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


def install():
    ConsortialBillingPlugin.install()
    update_settings(
        file_path=f'plugins/{SHORT_NAME}/install/settings.json'
    )
    call_command('fetch_world_bank_data', 'PA.NUS.FCRF')
    call_command('fetch_world_bank_data', 'NY.GNP.PCAP.CD')


def hook_registry():
    return {
        'press_admin_nav_block': {
            'module': 'plugins.consortial_billing.hooks',
            'function': 'admin_hook'
        },
    }
