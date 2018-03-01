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
                                                              enabled=True,
                                                              press_wide=True)
    return new_plugin


def options():
    return [{'name': 'preface_text', 'object': setting_handler.get_plugin_setting(get_self(), 'preface_text', None,
                                                                                  create=True, pretty='Preface Text'),
             'types': 'rich-text'},
            {'name': 'complete_text', 'object': setting_handler.get_plugin_setting(get_self(), 'complete_text', None,
                                                                                   create=True, pretty='Complete Text'),
             'types': 'rich-text'},
            {'name': 'new_signup_email', 'object': setting_handler.get_plugin_setting(get_self(), 'new_signup_email',
                                                                                      None,
                                                                                      create=True,
                                                                                      pretty='Email sent on signup'),
             'types': 'rich-text'},
            {'name': 'display_referral',
             'object': setting_handler.get_plugin_setting(get_self(), 'display_referral', None,
                                                          create=True, pretty='Referral Display',
                                                          types='boolean'),
             'types': 'boolean'},
            {'name': 'referral_text', 'object': setting_handler.get_plugin_setting(get_self(), 'referral_text', None,
                                                                                   create=True, pretty='Referral Text'),
             'types': 'rich-text'},
            {'name': 'referrer_discount',
             'object': setting_handler.get_plugin_setting(get_self(), 'referrer_discount', None,
                                                          create=True,
                                                          pretty='Referrer Discount %',
                                                          types='number'),
             'types': 'number'},
            {'name': 'referent_discount',
             'object': setting_handler.get_plugin_setting(get_self(), 'referent_discount', None,
                                                          create=True,
                                                          pretty='Referent Discount %',
                                                          types='number'),
             'types': 'number'},
            {'name': 'leader_board', 'object': setting_handler.get_plugin_setting(get_self(), 'leader_board', None,
                                                                                 create=True,
                                                                                 pretty='Display leader board',
                                                                                 types='boolean'),
             'types': 'boolean'},
            ]


def display_options():
    return [{'name': 'organisation_short_name',
             'object': setting_handler.get_plugin_setting(get_self(), 'organisation_short_name', None,
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
            {'name': 'banding_pre_text',
             'object': setting_handler.get_plugin_setting(get_self(), 'banding_pre_text', None,
                                                          create=True,
                                                          pretty='Text Before List of Institutions'),
             'types': 'rich-text'},
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
                                                              enabled=True,
                                                              press_wide=True)

    if created:
        print('Plugin {0} installed.'.format(PLUGIN_NAME))
    else:
        print('Plugin {0} is already installed.'.format(PLUGIN_NAME))


def hook_registry():
    # On site load, the load function is run for each installed plugin to generate
    # a list of hooks.
    return {
        'nav_block': {'module': 'plugins.consortial_billing.hooks', 'function': 'nav_hook'},
        'press_admin_nav_block': {'module': 'plugins.consortial_billing.hooks', 'function': 'admin_hook'},
        'journal_admin_nav_block': {'module': 'plugins.consortial_billing.hooks', 'function': 'admin_hook'}
    }
