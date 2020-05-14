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

import importlib
import importlib.util
import sys
from pathlib import Path
from typing import List

import pluggy

from ocrmypdf import pluginspec


def get_plugin_manager(plugins: List[str], builtins=True):
    pm = pluggy.PluginManager('ocrmypdf')
    pm.add_hookspecs(pluginspec)
    if builtins:
        plugins.insert(0, 'ocrmypdf.builtin_plugins')
    for name in plugins:
        if name.endswith('.py'):
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
    return pm
