# © 2019 James R. Barlow: github.com/jbarlow83
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

import logging
import importlib
import os
import sys


log = logging.getLogger(__name__)


def _load_function_from_module(location):
    """Load a function given a module location

    For location=a.b.c, will effectively run "from a.b import c"

    Example:
        _load_function_from_module("a.b.c")

    """
    module_parts = location.split('.')
    module_name = '.'.join(module_parts[:-1])
    object_name = module_parts[-1]
    module = importlib.import_module(module_name)
    fn = getattr(module, object_name)
    log.debug(f"Loaded function: from {module_name} import {object_name}")
    return fn


def _load_function_from_pyfile(location):
    """Load a function from a file

    Example:
        _load_function_from_pyfile("test.py::blur_filter")
    """
    filename, object_name = location.split('::', maxsplit=1)
    log.debug(f"Loading function {object_name} from {filename}")

    module_name = os.path.basename(filename)
    if module_name.endswith('.py'):
        module_name = module_name[:-3]

    spec = importlib.util.spec_from_file_location(module_name, filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    fn = getattr(module, object_name)
    return fn


def load_plugin(plugin):
    if callable(plugin):
        return plugin

    if not isinstance(plugin, str):
        raise TypeError()

    if '::' not in plugin:
        plugin = _load_function_from_module(plugin)
    else:
        plugin = _load_function_from_pyfile(plugin)

    return plugin


def check_plugin_loadable(plugin):
    load_plugin(plugin)
    return plugin
