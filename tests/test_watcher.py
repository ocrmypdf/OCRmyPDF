from __future__ import annotations

import datetime as dt
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import time
from collections.abc import Callable
from pathlib import Path

import pikepdf
import pytest

watchfiles = pytest.importorskip('watchfiles')

WATCHER = Path(__file__).parent.parent / 'misc' / 'watcher.py'

# Printed by the watcher immediately before it enters the watch loop.
WATCHING_MESSAGE = 'for new PDFs'

# Basename stem of the throwaway entries used to prove the watch is live.
PROBE_NAME = 'watchprobe'

# Generous, so a loaded CI runner cannot flake. Nothing pays for it in the
# common case because every wait below is event-driven.
TIMEOUT = 60.0


def _spawn_watcher(input_dir, output_dir, processed_dir, cwd, log_path, env_extra=None):
    """Launch watcher.py as a subprocess, cwd disjoint from the data dirs.

    The startup check treats the working directory as part of the code zone, so
    the subprocess must run from a directory that is neither an ancestor nor a
    descendant of the watched data directories.

    Both output streams are merged into ``log_path``. A file rather than a pipe,
    so the child can never block on a full pipe buffer, and ``PYTHONUNBUFFERED``
    keeps its stdout from sitting in a block buffer until exit; the tests read
    the log to learn what the watcher has done so far.
    """
    with log_path.open('wb') as log_file:
        return subprocess.Popen(
            [
                sys.executable,
                str(WATCHER),
                str(input_dir),
                str(output_dir),
                str(processed_dir),
            ],
            cwd=str(cwd),
            env=os.environ.copy() | {'PYTHONUNBUFFERED': '1'} | (env_extra or {}),
            stdout=log_file,
            stderr=subprocess.STDOUT,
        )


def _read_log(log_path: Path) -> str:
    try:
        return log_path.read_text(encoding='utf-8', errors='replace')
    except FileNotFoundError:
        return ''


def _wait_for(
    predicate: Callable[[], bool],
    what: str,
    log_path: Path | None = None,
    timeout: float = TIMEOUT,
    interval: float = 0.05,
) -> None:
    """Poll ``predicate`` until true, else fail with the watcher's log attached."""
    deadline = time.monotonic() + timeout
    while not predicate():
        if time.monotonic() > deadline:
            log = f"\nWatcher log:\n{_read_log(log_path)}" if log_path else ''
            raise AssertionError(f"Timed out after {timeout}s waiting for {what}.{log}")
        time.sleep(interval)


def _wait_for_log(log_path: Path, needle: str, what: str) -> None:
    _wait_for(lambda: needle in _read_log(log_path), what, log_path)


def _wait_for_watch_live(input_dir: Path, log_path: Path) -> None:
    """Wait until the watcher is really watching, not merely started.

    The readiness banner is printed just before the watch loop is entered, so an
    entry created the instant it appears can land before the filesystem watch
    exists and be missed entirely. Keep creating a throwaway probe until one of
    them shows up in the log; from then on no event is lost.

    The probe is a *directory* with a PDF name: it matches the watched pattern,
    yet the watcher rejects it at once as a non-regular file, so it costs no OCR
    run, leaves nothing in the output directory, and needs no POSIX-only trick.
    """
    _wait_for_log(log_path, WATCHING_MESSAGE, "the watcher to start up")

    attempt = 0

    def probe_seen() -> bool:
        nonlocal attempt
        if PROBE_NAME in _read_log(log_path):
            return True
        (input_dir / f'{PROBE_NAME}{attempt}.pdf').mkdir()
        attempt += 1
        return False

    _wait_for(
        probe_seen,
        "the watcher's filesystem watch to go live",
        log_path,
        interval=0.2,
    )


def _wait_for_file(path: Path, log_path: Path) -> None:
    _wait_for(path.exists, f"{path} to be created", log_path)


@pytest.fixture
def data_dirs(tmp_path):
    input_dir = tmp_path / 'input'
    input_dir.mkdir()
    output_dir = tmp_path / 'output'
    output_dir.mkdir()
    processed_dir = tmp_path / 'processed'
    processed_dir.mkdir()
    work_dir = tmp_path / 'work'  # cwd, disjoint from the data dirs
    work_dir.mkdir()
    return input_dir, output_dir, processed_dir, work_dir


@pytest.fixture
def watcher_log(tmp_path):
    # Outside the watched data dirs, so it is never mistaken for input.
    return tmp_path / 'watcher.log'


@pytest.fixture(scope='module')
def watcher_module():
    """Import misc/watcher.py directly, to unit test its pure helpers.

    The file is a script rather than part of the installed package, so it has to
    be loaded by path.
    """
    spec = importlib.util.spec_from_file_location('watcher_under_test', WATCHER)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize(
    'name, expected',
    [
        ('trivial.pdf', 'trivial.pdf'),
        ('a:b?.pdf', 'a_b_.pdf'),
        ('<>:"/\\|?*', '_________'),
        ('bell\x07.pdf', 'bell_.pdf'),
        ('trailing...', 'trailing'),
        ('trailing   ', 'trailing'),
        ('', '_'),
        ('...', '_'),
        ('   ', '_'),
        ('con.pdf', '_con.pdf'),
        ('CON', '_CON'),
        ('NuL.tiff', '_NuL.tiff'),
        ('com1.pdf', '_com1.pdf'),
        ('LPT9', '_LPT9'),
        ('contact.pdf', 'contact.pdf'),  # only exact device names are reserved
        ('com10.pdf', 'com10.pdf'),
    ],
)
def test_sanitize_filename_component(watcher_module, name, expected):
    assert watcher_module.sanitize_filename_component(name) == expected


def test_get_output_path_flat(watcher_module, tmp_path):
    structure = watcher_module.OutputStructure
    root = tmp_path / 'output'
    input_dir = tmp_path / 'input'
    assert watcher_module.get_output_path(
        root, input_dir, input_dir / 'a' / 'b' / 'trivial.PDF', structure.FLAT
    ) == (root / 'trivial.pdf')


def test_get_output_path_year_month(watcher_module, tmp_path):
    structure = watcher_module.OutputStructure
    root = tmp_path / 'output'
    input_dir = tmp_path / 'input'
    today = dt.date.today()
    assert watcher_module.get_output_path(
        root, input_dir, input_dir / 'trivial.pdf', structure.YEAR_MONTH
    ) == (root / f'{today.year}' / f'{today.month:02d}' / 'trivial.pdf')


def test_get_output_path_hierarchy(watcher_module, tmp_path):
    structure = watcher_module.OutputStructure
    root = tmp_path / 'output'
    input_dir = tmp_path / 'input'
    assert watcher_module.get_output_path(
        root, input_dir, input_dir / 'a' / 'b' / 'trivial.pdf', structure.HIERARCHY
    ) == (root / 'a' / 'b' / 'trivial.pdf')
    # A file in the root of the input directory has no subtree to mirror.
    assert watcher_module.get_output_path(
        root, input_dir, input_dir / 'trivial.pdf', structure.HIERARCHY
    ) == (root / 'trivial.pdf')


@pytest.mark.skipif(os.name == 'nt', reason="illegal characters on Windows")
def test_get_output_path_sanitizes_every_component(watcher_module, tmp_path):
    structure = watcher_module.OutputStructure
    root = tmp_path / 'output'
    input_dir = tmp_path / 'input'
    assert watcher_module.get_output_path(
        root, input_dir, input_dir / 'a:b' / 'c?d.pdf', structure.HIERARCHY
    ) == (root / 'a_b' / 'c_d.pdf')


def test_get_output_path_does_not_create_directories(watcher_module, tmp_path):
    structure = watcher_module.OutputStructure
    root = tmp_path / 'output'
    root.mkdir()
    input_dir = tmp_path / 'input'
    path = watcher_module.get_output_path(
        root, input_dir, input_dir / 'a' / 'b' / 'trivial.pdf', structure.HIERARCHY
    )
    assert not path.parent.exists()
    assert list(root.iterdir()) == []


def test_get_output_path_archive_keeps_suffix(watcher_module, tmp_path):
    structure = watcher_module.OutputStructure
    root = tmp_path / 'processed'
    input_dir = tmp_path / 'input'
    assert watcher_module.get_output_path(
        root,
        input_dir,
        input_dir / 'scan.PDF',
        structure.FLAT,
        force_pdf=False,
    ) == (root / 'scan.PDF')


def test_apply_conflict_policy_no_conflict(watcher_module, tmp_path):
    policy = watcher_module.ConflictPolicy
    path = tmp_path / 'trivial.pdf'
    for p in (policy.SKIP, policy.OVERWRITE, policy.SUFFIX):
        assert watcher_module.apply_conflict_policy(path, p) == path


def test_apply_conflict_policy_skip(watcher_module, tmp_path):
    path = tmp_path / 'trivial.pdf'
    path.write_bytes(b'sentinel')
    assert (
        watcher_module.apply_conflict_policy(path, watcher_module.ConflictPolicy.SKIP)
        is None
    )


def test_apply_conflict_policy_overwrite(watcher_module, tmp_path):
    path = tmp_path / 'trivial.pdf'
    path.write_bytes(b'sentinel')
    assert (
        watcher_module.apply_conflict_policy(
            path, watcher_module.ConflictPolicy.OVERWRITE
        )
        == path
    )


def test_apply_conflict_policy_suffix(watcher_module, tmp_path):
    suffix = watcher_module.ConflictPolicy.SUFFIX
    path = tmp_path / 'trivial.pdf'
    path.write_bytes(b'sentinel')
    assert watcher_module.apply_conflict_policy(path, suffix) == (
        tmp_path / 'trivial (1).pdf'
    )
    (tmp_path / 'trivial (1).pdf').write_bytes(b'sentinel')
    assert watcher_module.apply_conflict_policy(path, suffix) == (
        tmp_path / 'trivial (2).pdf'
    )


@pytest.mark.parametrize(
    'json_settings, deskew, expected',
    [
        ({'deskew': True}, None, True),  # OCR_DESKEW unset: JSON wins
        ({'deskew': False}, None, False),
        ({}, None, None),  # neither: OCRmyPDF's default
        ({'deskew': True}, False, False),  # OCR_DESKEW set: it wins
        ({'deskew': False}, True, True),
        ({}, True, True),
    ],
)
def test_ocrmypdf_kwargs_deskew(watcher_module, json_settings, deskew, expected):
    kwargs = watcher_module.ocrmypdf_kwargs(
        json_settings | {'language': ['eng']}, deskew
    )
    assert kwargs.get('deskew') == expected
    assert kwargs['language'] == ['eng']


@pytest.mark.parametrize('env, expected', [({}, None), ({'OCR_DESKEW': '1'}, True)])
def test_deskew_unset_by_default(watcher_module, monkeypatch, env, expected):
    monkeypatch.delenv('OCR_DESKEW', raising=False)
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    _command, bound, _ = watcher_module.app.parse_args(['in', 'out', 'processed'])
    bound.apply_defaults()
    assert bound.arguments['deskew'] is expected


@pytest.mark.parametrize('year_month', [True, False])
def test_watcher(data_dirs, watcher_log, resources, year_month):
    input_dir, output_dir, processed_dir, work_dir = data_dirs

    env_extra = {'OCR_OUTPUT_DIRECTORY_YEAR_MONTH': '1'} if year_month else {}
    proc = _spawn_watcher(
        input_dir,
        output_dir,
        processed_dir,
        work_dir,
        watcher_log,
        env_extra=env_extra,
    )
    _wait_for_watch_live(input_dir, watcher_log)

    shutil.copy(resources / 'trivial.pdf', input_dir / 'trivial.pdf')

    if year_month:
        expected = (
            output_dir
            / f'{dt.date.today().year}'
            / f'{dt.date.today().month:02d}'
            / 'trivial.pdf'
        )
    else:
        expected = output_dir / 'trivial.pdf'
    _wait_for_file(expected, watcher_log)

    deprecation = 'OCR_OUTPUT_DIRECTORY_YEAR_MONTH is deprecated'
    if year_month:
        _wait_for_log(watcher_log, deprecation, "the deprecation notice")
    else:
        assert deprecation not in _read_log(watcher_log)

    proc.terminate()
    proc.wait()


def test_watcher_output_structure_hierarchy(data_dirs, watcher_log, resources):
    input_dir, output_dir, processed_dir, work_dir = data_dirs

    # Create the subtree before the watch goes live: the watch is recursive, but
    # a directory created and filled in the same instant can race the watch.
    nested = input_dir / 'a' / 'b'
    nested.mkdir(parents=True)

    proc = _spawn_watcher(
        input_dir,
        output_dir,
        processed_dir,
        work_dir,
        watcher_log,
        env_extra={'OCR_OUTPUT_STRUCTURE': 'HIERARCHY'},
    )
    _wait_for_watch_live(input_dir, watcher_log)

    shutil.copy(resources / 'trivial.pdf', nested / 'trivial.pdf')
    _wait_for_file(output_dir / 'a' / 'b' / 'trivial.pdf', watcher_log)

    proc.terminate()
    proc.wait()


def test_watcher_conflict_suffix_is_default(data_dirs, watcher_log, resources):
    input_dir, output_dir, processed_dir, work_dir = data_dirs

    sentinel = output_dir / 'trivial.pdf'
    sentinel.write_bytes(b'sentinel')

    proc = _spawn_watcher(input_dir, output_dir, processed_dir, work_dir, watcher_log)
    _wait_for_watch_live(input_dir, watcher_log)

    shutil.copy(resources / 'trivial.pdf', input_dir / 'trivial.pdf')
    _wait_for_file(output_dir / 'trivial (1).pdf', watcher_log)

    assert sentinel.read_bytes() == b'sentinel'
    proc.terminate()
    proc.wait()


def test_watcher_conflict_skip(data_dirs, watcher_log, resources):
    input_dir, output_dir, processed_dir, work_dir = data_dirs

    sentinel = output_dir / 'trivial.pdf'
    sentinel.write_bytes(b'sentinel')

    proc = _spawn_watcher(
        input_dir,
        output_dir,
        processed_dir,
        work_dir,
        watcher_log,
        env_extra={'OCR_ON_CONFLICT': 'SKIP'},
    )
    _wait_for_watch_live(input_dir, watcher_log)

    shutil.copy(resources / 'trivial.pdf', input_dir / 'trivial.pdf')
    _wait_for_log(
        watcher_log, 'already exists', "the watcher to skip the existing output"
    )

    assert 'Skipping' in _read_log(watcher_log)
    assert not (output_dir / 'trivial (1).pdf').exists()
    assert sentinel.read_bytes() == b'sentinel'
    assert proc.poll() is None  # still running

    proc.terminate()
    proc.wait()


@pytest.mark.skipif(os.name == 'nt', reason="illegal characters on Windows")
def test_watcher_sanitizes_output_filename(data_dirs, watcher_log, resources):
    input_dir, output_dir, processed_dir, work_dir = data_dirs

    proc = _spawn_watcher(input_dir, output_dir, processed_dir, work_dir, watcher_log)
    _wait_for_watch_live(input_dir, watcher_log)

    # Legal on POSIX, illegal on Windows/SMB: the output name must be repaired.
    shutil.copy(resources / 'trivial.pdf', input_dir / 'a:b?.pdf')
    _wait_for_file(output_dir / 'a_b_.pdf', watcher_log)

    proc.terminate()
    proc.wait()


def test_watcher_archive_matches_output_behavior(data_dirs, watcher_log, resources):
    input_dir, output_dir, processed_dir, work_dir = data_dirs

    nested = input_dir / 'a' / 'b'
    nested.mkdir(parents=True)
    occupied = processed_dir / 'a' / 'b' / 'trivial.pdf'
    occupied.parent.mkdir(parents=True)
    occupied.write_bytes(b'sentinel')

    proc = _spawn_watcher(
        input_dir,
        output_dir,
        processed_dir,
        work_dir,
        watcher_log,
        env_extra={
            'OCR_ON_SUCCESS_ARCHIVE': '1',
            'OCR_OUTPUT_STRUCTURE': 'HIERARCHY',
        },
    )
    _wait_for_watch_live(input_dir, watcher_log)

    shutil.copy(resources / 'trivial.pdf', nested / 'trivial.pdf')
    _wait_for_file(output_dir / 'a' / 'b' / 'trivial.pdf', watcher_log)
    # The archive mirrors the input subtree and refuses to overwrite, exactly
    # like the output directory.
    _wait_for_file(processed_dir / 'a' / 'b' / 'trivial (1).pdf', watcher_log)

    assert occupied.read_bytes() == b'sentinel'
    assert not (nested / 'trivial.pdf').exists()

    proc.terminate()
    proc.wait()


def test_watcher_aborts_when_input_dir_in_code_zone(tmp_path, watcher_log):
    # Point the input directory at the interpreter prefix (a code zone). The
    # watcher must refuse to run and never enter the watch loop.
    input_dir = Path(sys.prefix)
    output_dir = tmp_path / 'output'
    output_dir.mkdir()
    processed_dir = tmp_path / 'processed'
    processed_dir.mkdir()
    work_dir = tmp_path / 'work'
    work_dir.mkdir()

    proc = _spawn_watcher(input_dir, output_dir, processed_dir, work_dir, watcher_log)
    assert proc.wait(timeout=30) == 9  # ExitCode.invalid_config


def test_watcher_aborts_when_output_under_input(tmp_path, watcher_log):
    # Output nested inside the watched input directory would loop forever.
    input_dir = tmp_path / 'input'
    input_dir.mkdir()
    output_dir = input_dir / 'output'
    output_dir.mkdir()
    processed_dir = tmp_path / 'processed'
    processed_dir.mkdir()
    work_dir = tmp_path / 'work'
    work_dir.mkdir()

    proc = _spawn_watcher(input_dir, output_dir, processed_dir, work_dir, watcher_log)
    assert proc.wait(timeout=30) == 9


def test_watcher_rejects_world_writable_settings_file(data_dirs, watcher_log, tmp_path):
    input_dir, output_dir, processed_dir, work_dir = data_dirs
    settings = tmp_path / 'settings.json'
    settings.write_text('{}')
    settings.chmod(0o666)

    proc = _spawn_watcher(
        input_dir,
        output_dir,
        processed_dir,
        work_dir,
        watcher_log,
        env_extra={'OCR_JSON_SETTINGS': str(settings)},
    )
    assert proc.wait(timeout=30) == 9


def test_watcher_rejects_plugin_in_data_dir(data_dirs, watcher_log):
    input_dir, output_dir, processed_dir, work_dir = data_dirs
    settings = json.dumps({'plugins': [str(input_dir / 'evil.py')]})

    proc = _spawn_watcher(
        input_dir,
        output_dir,
        processed_dir,
        work_dir,
        watcher_log,
        env_extra={'OCR_JSON_SETTINGS': settings},
    )
    assert proc.wait(timeout=30) == 9


@pytest.mark.skipif(os.name == 'nt', reason="POSIX fifo semantics")
def test_watcher_skips_fifo_input(data_dirs, watcher_log, resources):
    input_dir, output_dir, processed_dir, work_dir = data_dirs

    # Poll, because the native backend is not guaranteed to see a fifo appear:
    # macOS FSEvents reports the creation of a directory or a regular file but
    # not of a fifo, so the event would never arrive and the watcher would never
    # get the chance to reject it. Polling compares directory listings, so it
    # surfaces every new entry whatever its type.
    proc = _spawn_watcher(
        input_dir,
        output_dir,
        processed_dir,
        work_dir,
        watcher_log,
        env_extra={'OCR_USE_POLLING': '1'},
    )
    _wait_for_watch_live(input_dir, watcher_log)

    # A fifo named like a PDF must be ignored, not OCR'd or crash the watcher.
    os.mkfifo(input_dir / 'pipe.pdf')
    _wait_for_log(watcher_log, 'pipe.pdf', "the watcher to notice the fifo")
    # Then a genuine PDF should still be processed. The watcher handles files
    # one at a time, so the fifo is fully dealt with by the time this appears.
    shutil.copy(resources / 'trivial.pdf', input_dir / 'trivial.pdf')
    _wait_for_file(output_dir / 'trivial.pdf', watcher_log)

    assert not (output_dir / 'pipe.pdf').exists()
    assert proc.poll() is None  # still running

    proc.terminate()
    proc.wait()


def test_watcher_survives_encrypted_pdf(data_dirs, watcher_log, resources, tmp_path):
    # pikepdf.PasswordError does not derive from pikepdf.PdfError, so an
    # encrypted PDF used to escape wait_for_file_ready() and tear down the
    # watch loop, leaving later files unprocessed.
    input_dir, output_dir, processed_dir, work_dir = data_dirs

    encrypted = tmp_path / 'encrypted.pdf'
    with pikepdf.open(resources / 'trivial.pdf') as pdf:
        pdf.save(
            encrypted, encryption=pikepdf.Encryption(owner='owner', user='user', R=6)
        )

    proc = _spawn_watcher(input_dir, output_dir, processed_dir, work_dir, watcher_log)
    _wait_for_watch_live(input_dir, watcher_log)

    shutil.copy(encrypted, input_dir / 'encrypted.pdf')
    _wait_for_log(
        watcher_log, 'encrypted.pdf', "the watcher to pick up the encrypted PDF"
    )
    # A PDF arriving after the encrypted one must still be processed. The
    # watcher handles files one at a time, so the encrypted one is fully dealt
    # with by the time this output appears.
    shutil.copy(resources / 'trivial.pdf', input_dir / 'trivial.pdf')
    _wait_for_file(output_dir / 'trivial.pdf', watcher_log)

    assert not (output_dir / 'encrypted.pdf').exists()
    assert proc.poll() is None  # still running

    proc.terminate()
    proc.wait()


def test_watcher_survives_ocr_exception(data_dirs, watcher_log, resources):
    # Any per-file error, not just PasswordError, must be contained: a file
    # that makes ocrmypdf.ocr() raise must not stop the watch loop.
    input_dir, output_dir, processed_dir, work_dir = data_dirs

    # An unreadable-by-ocrmypdf file that still passes wait_for_file_ready() is
    # hard to synthesize, so drive the failure through OCR_JSON_SETTINGS: an
    # unsupported language makes ocrmypdf.ocr() raise MissingDependencyError.
    proc = _spawn_watcher(
        input_dir,
        output_dir,
        processed_dir,
        work_dir,
        watcher_log,
        env_extra={'OCR_JSON_SETTINGS': json.dumps({'language': ['zzz']})},
    )
    _wait_for_watch_live(input_dir, watcher_log)

    shutil.copy(resources / 'trivial.pdf', input_dir / 'bad.pdf')
    _wait_for_log(
        watcher_log,
        'Error while processing',
        "the watcher to log and contain the OCR failure",
    )

    assert not (output_dir / 'bad.pdf').exists()
    assert proc.poll() is None  # error contained, watcher still running

    proc.terminate()
    proc.wait()
