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


def options():
    return [{'name': 'preface_text', 'object': setting_handler.get_plugin_setting(get_self(), 'preface_text', None,
                                                                                  create=True, pretty='Preface Text'),
             'types': 'rich-text'},
            {'name': 'complete_text', 'object': setting_handler.get_plugin_setting(get_self(), 'complete_text', None,
                                                                                   create=True, pretty='Complete Text'),
             'types': 'rich-text'}
            ]


def display_options():
    return [{'name': 'organisation_short_name', 'object': setting_handler.get_plugin_setting(get_self(), 'organisation_short_name', None,
                                                                                             create=True,
                                                                                             pretty='Organisation Short Name'),
             'types': 'rich-text'},
            {'name': 'pre_text', 'object': setting_handler.get_plugin_setting(get_self(), 'pre_text', None,
                                                                              create=True,
                                                                              pretty='Text Before List of Institutions'),
             'types': 'rich-text'},
            {'name': 'post_text', 'object': setting_handler.get_plugin_setting(get_self(), 'post_text', None,
                                                                               create=True,
                                                                               pretty='Text After List of Institutions'),
             'types': 'rich-text'},
            {'name': 'email_text', 'object': setting_handler.get_plugin_setting(get_self(), 'email_text', None,
                                                                              create=True,
                                                                              pretty='Text sent to institutions polling'),
             'types': 'rich-text'},
            {'name': 'display_nav', 'object': setting_handler.get_plugin_setting(get_self(), 'display_nav', None,
                                                                                create=True,
                                                                                pretty='Display nav item',
                                                                                 types='boolean'),
             'types': 'boolean'},
            ]


def currency_options():
    return [
        {'name': 'base_currency', 'object': setting_handler.get_plugin_setting(get_self(),
                                                                               'base_currency',
                                                                               None,
                                                                               create=True,
                                                                               pretty='Press Base Currency'),
         'types': 'char'}
    ]


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
