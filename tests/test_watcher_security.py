# SPDX-FileCopyrightText: 2025 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

"""Unit tests for the watcher security helpers."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

from ocrmypdf._watcher_security import (
    WatcherConfigError,
    assert_data_dirs_isolated,
    assert_no_watch_loop,
    assert_plugins_safe,
    assert_settings_file_safe,
    is_safe_regular_file,
    is_safe_write_target,
    resolve_critical_paths,
)

pytestmark = pytest.mark.skipif(
    os.name == 'nt', reason="POSIX permission and symlink semantics assumed"
)


def test_resolve_critical_paths_includes_expected():
    critical = resolve_critical_paths()
    assert critical
    # The interpreter prefix and the working directory are always present.
    prefix = Path(os.path.normcase(os.path.realpath(sys.prefix)))
    cwd = Path(os.path.normcase(os.path.realpath(Path.cwd())))
    assert prefix in critical
    assert cwd in critical


def test_resolve_critical_paths_excludes_empty(monkeypatch):
    monkeypatch.setenv('PATH', ':/usr/bin:')  # leading/trailing empty segments
    critical = resolve_critical_paths()
    # Empty PATH segments must not smuggle in a bare/empty path.
    assert Path() not in critical
    assert all(str(p) for p in critical)


def test_resolve_critical_paths_survives_getsitepackages_failure(monkeypatch):
    import site

    monkeypatch.setattr(
        site, 'getsitepackages', lambda: (_ for _ in ()).throw(RuntimeError)
    )
    # Should not raise despite getsitepackages blowing up.
    assert resolve_critical_paths()


@pytest.mark.parametrize('relation', ['data_in_critical', 'critical_in_data', 'equal'])
def test_assert_data_dirs_isolated_rejects_overlap(tmp_path, relation):
    critical_dir = tmp_path / 'code'
    critical_dir.mkdir()
    if relation == 'data_in_critical':
        data = critical_dir / 'input'
        data.mkdir()
    elif relation == 'critical_in_data':
        data = tmp_path / 'data'
        data.mkdir()
        critical_dir = data / 'code'  # critical path now lives inside the data dir
        critical_dir.mkdir()
    else:  # equal
        data = critical_dir

    with pytest.raises(WatcherConfigError):
        assert_data_dirs_isolated({'input': data}, [critical_dir])


def test_assert_data_dirs_isolated_allows_disjoint(tmp_path):
    critical_dir = tmp_path / 'code'
    critical_dir.mkdir()
    data = tmp_path / 'input'
    data.mkdir()
    assert_data_dirs_isolated({'input': data}, [critical_dir])  # no raise


def test_assert_data_dirs_isolated_follows_symlinked_data_dir(tmp_path):
    critical_dir = tmp_path / 'code'
    critical_dir.mkdir()
    # A symlink that points into the critical zone must be resolved and rejected.
    data = tmp_path / 'input'
    data.symlink_to(critical_dir, target_is_directory=True)
    with pytest.raises(WatcherConfigError):
        assert_data_dirs_isolated({'input': data}, [critical_dir])


@pytest.mark.parametrize('which', ['output', 'archive'])
@pytest.mark.parametrize('nesting', ['direct_child', 'deep', 'equal'])
def test_assert_no_watch_loop_rejects_dir_under_input(tmp_path, which, nesting):
    input_dir = tmp_path / 'input'
    input_dir.mkdir()
    outside = tmp_path / 'outside'
    outside.mkdir()

    if nesting == 'direct_child':
        looped = input_dir / which
    elif nesting == 'deep':
        looped = input_dir / 'a' / 'b' / which
    else:  # equal
        looped = input_dir

    output_dir = looped if which == 'output' else outside
    archive_dir = looped if which == 'archive' else outside
    with pytest.raises(WatcherConfigError):
        assert_no_watch_loop(input_dir, output_dir, archive_dir)


def test_assert_no_watch_loop_allows_disjoint(tmp_path):
    input_dir = tmp_path / 'input'
    input_dir.mkdir()
    assert_no_watch_loop(
        input_dir, tmp_path / 'output', tmp_path / 'archive'
    )  # no raise


def test_assert_no_watch_loop_allows_input_under_output(tmp_path):
    # input nested under output is fine: output writes are not seen by the watch.
    output_dir = tmp_path / 'output'
    output_dir.mkdir()
    input_dir = output_dir / 'input'
    input_dir.mkdir()
    assert_no_watch_loop(input_dir, output_dir, tmp_path / 'archive')  # no raise


def test_assert_no_watch_loop_follows_symlinked_output(tmp_path):
    # An output dir that is a symlink pointing back inside input must be caught.
    input_dir = tmp_path / 'input'
    input_dir.mkdir()
    real_target = input_dir / 'results'
    real_target.mkdir()
    output_dir = tmp_path / 'output'
    output_dir.symlink_to(real_target, target_is_directory=True)
    with pytest.raises(WatcherConfigError):
        assert_no_watch_loop(input_dir, output_dir, tmp_path / 'archive')


def test_is_safe_regular_file_accepts_regular(tmp_path):
    f = tmp_path / 'a.pdf'
    f.write_bytes(b'%PDF')
    assert is_safe_regular_file(f, tmp_path)


def test_is_safe_regular_file_rejects_symlink(tmp_path):
    target = tmp_path / 'real.pdf'
    target.write_bytes(b'%PDF')
    link = tmp_path / 'link.pdf'
    link.symlink_to(target)
    assert not is_safe_regular_file(link, tmp_path)


def test_is_safe_regular_file_rejects_fifo(tmp_path):
    fifo = tmp_path / 'pipe.pdf'
    os.mkfifo(fifo)
    assert not is_safe_regular_file(fifo, tmp_path)


def test_is_safe_regular_file_rejects_directory(tmp_path):
    d = tmp_path / 'sub'
    d.mkdir()
    assert not is_safe_regular_file(d, tmp_path)


def test_is_safe_regular_file_rejects_symlinked_ancestor(tmp_path):
    # A regular file reached through a symlinked parent directory escapes the
    # watched tree and must be rejected.
    outside = tmp_path / 'outside'
    outside.mkdir()
    real = outside / 'a.pdf'
    real.write_bytes(b'%PDF')

    watched = tmp_path / 'watched'
    watched.mkdir()
    (watched / 'link').symlink_to(outside, target_is_directory=True)
    assert not is_safe_regular_file(watched / 'link' / 'a.pdf', watched)


def test_is_safe_write_target_fresh_path(tmp_path):
    assert is_safe_write_target(tmp_path / 'out.pdf', tmp_path)


def test_is_safe_write_target_rejects_existing_fifo(tmp_path):
    fifo = tmp_path / 'out.pdf'
    os.mkfifo(fifo)
    assert not is_safe_write_target(fifo, tmp_path)


def test_is_safe_write_target_rejects_symlinked_parent(tmp_path):
    outside = tmp_path / 'outside'
    outside.mkdir()
    output = tmp_path / 'output'
    output.mkdir()
    (output / 'redir').symlink_to(outside, target_is_directory=True)
    assert not is_safe_write_target(output / 'redir' / 'out.pdf', output)


def test_assert_settings_file_safe_rejects_inside_data_dir(tmp_path):
    data = tmp_path / 'input'
    data.mkdir()
    settings = data / 'settings.json'
    settings.write_text('{}')
    settings.chmod(0o600)
    with pytest.raises(WatcherConfigError):
        assert_settings_file_safe(settings, [data])


def test_assert_settings_file_safe_rejects_group_world_writable(tmp_path):
    data = tmp_path / 'input'
    data.mkdir()
    settings = tmp_path / 'settings.json'
    settings.write_text('{}')
    settings.chmod(0o666)
    with pytest.raises(WatcherConfigError):
        assert_settings_file_safe(settings, [data])


def test_assert_settings_file_safe_accepts_owner_only(tmp_path):
    data = tmp_path / 'input'
    data.mkdir()
    settings = tmp_path / 'settings.json'
    settings.write_text('{}')
    settings.chmod(0o600)
    assert_settings_file_safe(settings, [data])  # no raise


def test_assert_plugins_safe_allows_module_name(tmp_path):
    data = tmp_path / 'input'
    data.mkdir()
    assert_plugins_safe(['ocrmypdf.builtin_plugins.tesseract_ocr'], [data])


def test_assert_plugins_safe_rejects_absolute_py_in_data_dir(tmp_path):
    data = tmp_path / 'input'
    data.mkdir()
    with pytest.raises(WatcherConfigError):
        assert_plugins_safe([str(data / 'evil.py')], [data])


def test_assert_plugins_safe_rejects_relative_py_resolving_into_data_dir(
    tmp_path, monkeypatch
):
    data = tmp_path / 'input'
    data.mkdir()
    monkeypatch.chdir(data)
    with pytest.raises(WatcherConfigError):
        assert_plugins_safe(['evil.py'], [data])


def test_assert_plugins_safe_allows_py_outside_data_dir(tmp_path):
    data = tmp_path / 'input'
    data.mkdir()
    plugin = tmp_path / 'plugin.py'
    plugin.write_text('# plugin')
    assert_plugins_safe([str(plugin)], [data])  # no raise


def test_assert_plugins_safe_non_py_path_is_treated_as_module(tmp_path):
    # A path-like name without .py is loaded via import_module (which rejects
    # separators), so it cannot execute a data-dir file; containment passes.
    data = tmp_path / 'input'
    data.mkdir()
    assert_plugins_safe([str(data / 'evil')], [data])  # no raise


def test_watcher_config_error_exit_code():
    assert int(WatcherConfigError().exit_code) == 9
