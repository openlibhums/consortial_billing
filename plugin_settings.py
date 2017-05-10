from utils import models

PLUGIN_NAME = 'Consortial Billing'
DESCRIPTION = 'This is a plugin to handle consortial billing.'
AUTHOR = 'Martin Paul Eve'
VERSION = '1.0'
SHORT_NAME = 'consortial'
MANAGER_URL = 'consortial_index'


def install():
    new_plugin, created = models.Plugin.objects.get_or_create(name=SHORT_NAME, version=VERSION, enabled=True)

    if created:
        print('Plugin {0} installed.'.format(PLUGIN_NAME))
    else:
        print('Plugin {0} is already installed.'.format(PLUGIN_NAME))


def hook_registry():
    # On site load, the load function is run for each installed plugin to generate
    # a list of hooks.
    return {'name_of_the_template_hook': 'plugins.generic_plugin.hooks.another_hook_function'}
