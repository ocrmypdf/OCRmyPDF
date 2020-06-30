# © 2020 James R. Barlow: github.com/jbarlow83
#
# This file is part of OCRmyPDF.
#
# OCRmyPDF is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OCRmyPDF is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with OCRmyPDF.  If not, see <http://www.gnu.org/licenses/>.

import argparse
import importlib
import importlib.util
import sys
from functools import partial
from pathlib import Path
from typing import Callable, List, Tuple, Union

import pluggy

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
        self, *args, setup_func: Callable[[pluggy.PluginManager], None], **kwargs
    ):
        self._init_args = args
        self._setup_func = setup_func
        self._init_kwargs = kwargs
        super().__init__(*args, **kwargs)
        setup_func(self)

    def __getstate__(self):
        state = dict(
            _init_args=self._init_args,
            _setup_func=self._setup_func,
            _init_kwargs=self._init_kwargs,
        )
        return state

    def __setstate__(self, state):
        self.__init__(
            *state['_init_args'],
            setup_func=state['_setup_func'],
            **state['_init_kwargs'],
        )


def _setup_plugins(
    pm: pluggy.PluginManager, plugins: List[Union[str, Path]], builtins: bool = True
):
    pm.add_hookspecs(pluginspec)

    all_plugins: List[Union[str, Path]] = []
    if builtins:
        all_plugins.extend(
            [
                'ocrmypdf.builtin_plugins.ghostscript',
                'ocrmypdf.builtin_plugins.tesseract_ocr',
            ]
        )
    all_plugins.extend(plugins)
    for name in all_plugins:
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
        pm.register(module)


def get_plugin_manager(plugins: List[str], builtins=True):
    pm = OcrmypdfPluginManager(
        project_name='ocrmypdf',
        setup_func=partial(_setup_plugins, plugins=plugins, builtins=builtins),
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
