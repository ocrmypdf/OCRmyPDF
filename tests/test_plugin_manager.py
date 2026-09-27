# SPDX-FileCopyrightText: 2026 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

"""Tests for builtin plugin registration and PyInstaller support."""

from __future__ import annotations

import pkgutil
from pathlib import Path

import pytest

import ocrmypdf.builtin_plugins
from ocrmypdf import _plugin_manager
from ocrmypdf._plugin_manager import get_plugin_manager


def test_builtin_plugin_list_matches_package():
    present = sorted(
        m.name for m in pkgutil.iter_modules(ocrmypdf.builtin_plugins.__path__)
    )
    assert list(_plugin_manager.BUILTIN_PLUGINS) == present
    modules = _plugin_manager._builtin_plugin_modules()
    assert [m.__name__ for m in modules] == [
        f'ocrmypdf.builtin_plugins.{name}' for name in _plugin_manager.BUILTIN_PLUGINS
    ]


def test_builtins_registered_without_package_discovery(monkeypatch):
    # A frozen application (e.g. PyInstaller) cannot enumerate the
    # builtin_plugins package directory, so registration must not depend on it.
    monkeypatch.setattr(ocrmypdf.builtin_plugins, '__path__', [])
    pm = get_plugin_manager([])
    registered = {getattr(p, '__name__', None) for p in pm.pluggy_manager.get_plugins()}
    for name in _plugin_manager.BUILTIN_PLUGINS:
        assert f'ocrmypdf.builtin_plugins.{name}' in registered
    assert pm.get_ocr_engine(options=None) is not None


def test_builtin_registration_order():
    # pluggy lists hook implementations in registration order; later
    # registrations take precedence, so the order is part of the contract.
    pm = get_plugin_manager([])
    impls = pm.pluggy_manager.hook.check_options.get_hookimpls()
    prefix = 'ocrmypdf.builtin_plugins.'
    plugin_names = [getattr(i.plugin, '__name__', '') for i in impls]
    names = [n.removeprefix(prefix) for n in plugin_names if n.startswith(prefix)]
    assert len(names) > 1
    assert names == [n for n in _plugin_manager.BUILTIN_PLUGINS if n in names]


def test_pyinstaller_hook_dir():
    from ocrmypdf._pyinstaller import get_hook_dirs

    (hook_dir,) = get_hook_dirs()
    assert (Path(hook_dir) / 'hook-ocrmypdf.py').is_file()


def test_pyinstaller_entry_point_declared():
    import tomllib

    pyproject = Path(__file__).parents[1] / 'pyproject.toml'
    if not pyproject.exists():
        pytest.skip('pyproject.toml not available')
    data = tomllib.loads(pyproject.read_text())
    entry_points = data['project']['entry-points']['pyinstaller40']
    assert entry_points['hook-dirs'] == 'ocrmypdf._pyinstaller:get_hook_dirs'
