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
from typing import List

import pluggy

from ocrmypdf import pluginspec


def get_plugin_manager(plugins: List[str]):
    pm = pluggy.PluginManager('ocrmypdf')
    pm.add_hookspecs(pluginspec)
    for name in plugins:
        module = importlib.import_module(name)
        pm.register(module)
    return pm
