import importlib

import pluggy

from ocrmypdf import pluginspec


def get_plugin_manager(options):
    pm = pluggy.PluginManager('ocrmypdf')
    pm.add_hookspecs(pluginspec)

    for name in options.plugins:
        module = importlib.import_module(name)
        pm.register(module)
    return pm
