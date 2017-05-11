from utils import models, setting_handler


PLUGIN_NAME = 'Consortial Billing'
DESCRIPTION = 'This is a plugin to handle consortial billing.'
AUTHOR = 'Martin Paul Eve'
VERSION = '1.0'
SHORT_NAME = 'consortial_billing'
DISPLAY_NAME = 'supporters'
MANAGER_URL = 'consortial_index'


def get_self():
    new_plugin, created = models.Plugin.objects.get_or_create(name=SHORT_NAME,
                                                              display_name=DISPLAY_NAME,
                                                              version=VERSION,
                                                              enabled=True)
    return new_plugin

options = [{'name': 'preface_text', 'object': setting_handler.get_plugin_setting(get_self(), 'preface_text', None,
                                                                                 create=True)},]


def install():
    new_plugin, created = models.Plugin.objects.get_or_create(name=SHORT_NAME,
                                                              display_name=DISPLAY_NAME,
                                                              version=VERSION,
                                                              enabled=True)

    if created:
        print('Plugin {0} installed.'.format(PLUGIN_NAME))
    else:
        print('Plugin {0} is already installed.'.format(PLUGIN_NAME))


def hook_registry():
    # On site load, the load function is run for each installed plugin to generate
    # a list of hooks.
    return {'nav_block': {'module': 'plugins.consortial_billing.hooks', 'function': 'nav_hook'}}
