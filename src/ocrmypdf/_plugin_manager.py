# © 2020 James R. Barlow: github.com/jbarlow83
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


import argparse
import importlib
import importlib.util
import pkgutil
import sys
from pathlib import Path
from typing import List, Tuple, Union

import pluggy

import ocrmypdf.builtin_plugins
from ocrmypdf import pluginspec
from ocrmypdf.cli import get_parser, plugins_only_parser


class OcrmypdfPluginManager(pluggy.PluginManager):
    """pluggy.PluginManager that can fork.

    Capable of reconstructing itself in child workers.

    Arguments:
        setup_func: callback that initializes the plugin manager with all
            standard plugins
    """

    def __init__(
        self,
        *args,
        plugins: List[Union[str, Path]],
        builtins: bool = True,
        **kwargs,
    ):
        self.__init_args = args
        self.__init_kwargs = kwargs
        self.__plugins = plugins
        self.__builtins = builtins
        super().__init__(*args, **kwargs)
        self.setup_plugins()

    def __getstate__(self):
        state = dict(
            init_args=self.__init_args,
            plugins=self.__plugins,
            builtins=self.__builtins,
            init_kwargs=self.__init_kwargs,
        )
        return state

    def __setstate__(self, state):
        self.__init__(
            *state['init_args'],
            plugins=state['plugins'],
            builtins=state['builtins'],
            **state['init_kwargs'],
        )

    def setup_plugins(self):
        self.add_hookspecs(pluginspec)

        # 1. Register builtins
        if self.__builtins:
            for module in sorted(
                pkgutil.iter_modules(ocrmypdf.builtin_plugins.__path__)
            ):
                name = f'ocrmypdf.builtin_plugins.{module.name}'
                module = importlib.import_module(name)
                self.register(module)

        # 2. Install semfree if needed
        try:
            # pylint: disable=import-outside-toplevel
            from multiprocessing.synchronize import SemLock

            del SemLock
        except ImportError:
            self.register(importlib.import_module('ocrmypdf.extra_plugins.semfree'))

        # 3. Register setuptools plugins
        self.load_setuptools_entrypoints('ocrmypdf')

        # 4. Register plugins specified on command line
        for name in self.__plugins:
            if isinstance(name, Path) or name.endswith('.py'):
                # Import by filename
                module_name = Path(name).stem
                spec = importlib.util.spec_from_file_location(module_name, name)
                module = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = module
                spec.loader.exec_module(module)
            else:
                # Import by dotted module name
                module = importlib.import_module(name)
            self.register(module)


def get_plugin_manager(plugins: List[Union[str, Path]], builtins=True):
    pm = OcrmypdfPluginManager(
        project_name='ocrmypdf',
        plugins=plugins,
        builtins=builtins,
    )
    return pm


def get_parser_options_plugins(
    args,
) -> Tuple[argparse.ArgumentParser, argparse.Namespace, pluggy.PluginManager]:
    pre_options, _unused = plugins_only_parser.parse_known_args(args=args)
    plugin_manager = get_plugin_manager(pre_options.plugins)

    parser = get_parser()
    plugin_manager.hook.add_options(parser=parser)  # pylint: disable=no-member

    options = parser.parse_args(args=args)
    return parser, options, plugin_manager
