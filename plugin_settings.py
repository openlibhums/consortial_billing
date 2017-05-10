PLUGIN_NAME = 'Consortial Billing'
DESCRIPTION = 'This is a plugin to handle consortial billing.'
AUTHOR = 'Martin Paul Eve'


def install():
    # Install stub, when the revists install_plugins management command is run,
    # this command is run for all plugins that do not have a record in the
    # plugins table.
    pass


def hook_registry():
    # On site load, the load function is run for each installed plugin to generate
    # a list of hooks.
    return {'name_of_the_template_hook': 'plugins.generic_plugin.hooks.another_hook_function'}
