# SPDX-FileCopyrightText: 2022 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import itertools
import multiprocessing
import os
import platform
import subprocess
import sys
import threading

import pikepdf
import pytest

import ocrmypdf
import ocrmypdf.api
from ocrmypdf import ExitCode
from ocrmypdf._concurrent import SerialExecutor
from ocrmypdf.builtin_plugins.concurrency import get_progressbar_class

from .conftest import TESTS_ROOT, run_ocrmypdf_api

NOOP_PLUGIN = 'tests/plugins/tesseract_noop.py'


@pytest.mark.skipif(os.name == 'nt', reason="Windows doesn't have SIGKILL")
@pytest.mark.skipif(
    platform.python_version_tuple() >= ('3', '12'), reason="can deadlock due to fork"
)
def test_simulate_oom_killer(multipage, no_outpdf):
    exitcode = run_ocrmypdf_api(
        multipage,
        no_outpdf,
        '--force-ocr',
        '--no-use-threads',
        '--plugin',
        'tests/plugins/tesseract_simulate_oom_killer.py',
    )
    assert exitcode == ExitCode.child_process_error


def _run_in_threads(target, count=2):
    """Run ``target`` in ``count`` threads, returning any exceptions raised."""
    errors: list[BaseException] = []

    def wrapper():
        try:
            target()
        except BaseException as e:  # noqa: BLE001 - report, don't swallow
            errors.append(e)

    threads = [threading.Thread(target=wrapper) for _ in range(count)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=180)
    return errors


def test_executors_do_not_serialize_across_instances():
    """Two Executor instances must be able to run tasks at the same time.

    ``Executor`` used to hold a lock shared by every instance and subclass in
    the process, so a second executor could not start until the first finished.
    """
    barrier = threading.Barrier(2, timeout=30)

    def run():
        # A distinct instance per thread - the point is that they must not
        # share a class-level lock.
        SerialExecutor()(
            use_threads=True,
            max_workers=1,
            progress_kwargs=dict(total=1, desc='test', unit='task', disable=True),
            task=lambda _: barrier.wait(),
            task_arguments=[(1,)],
        )

    assert not _run_in_threads(run)


def test_progress_bar_console_ownership():
    """Only one progress bar at a time may render on the shared console."""
    pbar_class = get_progressbar_class()
    kwargs = dict(total=10, unit='page', disable=False)

    with pbar_class(desc='first', **kwargs) as first:
        assert first.progress.disable is False
        with pbar_class(desc='second', **kwargs) as second:
            assert second.progress.disable is True  # lost the console race

    # Console released - a later bar renders again. Each job creates several
    # bars in sequence, so this must work repeatedly.
    with pbar_class(desc='third', **kwargs) as third:
        assert third.progress.disable is False


def test_progress_bar_releases_console_on_exception():
    """A progress bar that raises must not strand ownership of the console."""
    pbar_class = get_progressbar_class()
    kwargs = dict(total=1, unit='page', disable=False)

    with pytest.raises(ZeroDivisionError), pbar_class(desc='doomed', **kwargs):
        raise ZeroDivisionError

    with pbar_class(desc='next', **kwargs) as pbar:
        assert pbar.progress.disable is False


def test_two_api_jobs_overlap_in_pipeline(monkeypatch, resources, tmp_path):
    """Two OCR jobs in one process must be able to be in the pipeline at once.

    The barrier only completes if both jobs reach ``run_pipeline`` together, so
    this asserts the property directly rather than timing anything.
    """
    barrier = threading.Barrier(2, timeout=60)
    real_run_pipeline = ocrmypdf.api.run_pipeline

    def spy_run_pipeline(*args, **kwargs):
        barrier.wait()
        return real_run_pipeline(*args, **kwargs)

    monkeypatch.setattr(ocrmypdf.api, 'run_pipeline', spy_run_pipeline)

    counter = itertools.count()

    def job():
        ocrmypdf.ocr(
            resources / 'trivial.pdf',
            tmp_path / f'out{next(counter)}.pdf',
            jobs=1,
            optimize=0,
            plugins=[NOOP_PLUGIN],
            progress_bar=False,
        )

    assert not _run_in_threads(job)


def test_two_api_jobs_produce_valid_output(resources, tmp_path):
    """Two concurrent jobs must both produce a valid PDF."""
    counter = itertools.count()

    def job():
        n = next(counter)
        ocrmypdf.ocr(
            resources / 'trivial.pdf',
            tmp_path / f'valid{n}.pdf',
            jobs=1,
            optimize=0,
            plugins=[NOOP_PLUGIN],
            progress_bar=False,
        )

    assert not _run_in_threads(job)
    outputs = sorted(tmp_path.glob('valid*.pdf'))
    assert len(outputs) == 2
    for output in outputs:
        with pikepdf.open(output) as pdf:
            assert len(pdf.pages) >= 1


def test_same_plugin_set_is_installed_once_per_interpreter(resources, tmp_path):
    """Repeat jobs must reuse the installed plugin set, not re-execute it."""

    def run(name):
        ocrmypdf.ocr(
            resources / 'trivial.pdf',
            tmp_path / name,
            optimize=0,
            plugins=[NOOP_PLUGIN],
            progress_bar=False,
        )

    run('once.pdf')
    first = sys.modules['tesseract_noop']
    run('twice.pdf')
    assert sys.modules['tesseract_noop'] is first


def test_installing_a_different_plugin_set_waits_for_in_flight_jobs(
    monkeypatch, resources, tmp_path
):
    """A job cannot have the plugin infrastructure replaced underneath it.

    Installing a plugin set that is not already installed must wait for every
    in-flight job to finish.
    """
    # Spelled differently, so it is a distinct plugin set as far as the install
    # cache is concerned, while behaving identically for OCR purposes.
    other_plugin = './' + NOOP_PLUGIN

    def run(plugin, name):
        ocrmypdf.ocr(
            resources / 'trivial.pdf',
            tmp_path / name,
            optimize=0,
            plugins=[plugin],
            progress_bar=False,
        )

    # Install both sets up front, so the blocking below is attributable to the
    # lock rather than to first-time installation cost.
    run(NOOP_PLUGIN, 'warm_a.pdf')
    run(other_plugin, 'warm_b.pdf')
    ocrmypdf.api._installed_plugins.pop(
        ocrmypdf.api._plugin_cache_key([other_plugin]), None
    )

    first_running = threading.Event()
    release_first = threading.Event()
    second_installed = threading.Event()

    real_run_pipeline = ocrmypdf.api.run_pipeline
    real_setup = ocrmypdf.api.setup_plugin_infrastructure
    holding = threading.Event()

    def spy_run_pipeline(*args, **kwargs):
        if not holding.is_set():
            holding.set()
            first_running.set()
            release_first.wait(timeout=30)
        return real_run_pipeline(*args, **kwargs)

    def spy_setup(*args, **kwargs):
        result = real_setup(*args, **kwargs)
        second_installed.set()
        return result

    monkeypatch.setattr(ocrmypdf.api, 'run_pipeline', spy_run_pipeline)
    monkeypatch.setattr(ocrmypdf.api, 'setup_plugin_infrastructure', spy_setup)

    first = threading.Thread(target=run, args=(NOOP_PLUGIN, 'first.pdf'))
    first.start()
    try:
        assert first_running.wait(timeout=30), "first job never started"
        second = threading.Thread(target=run, args=(other_plugin, 'second.pdf'))
        second.start()
        # The second job needs to install a plugin set that is not present, so
        # it must not proceed while the first job is still running.
        assert not second_installed.wait(timeout=2)
    finally:
        release_first.set()
        first.join(timeout=60)
        second.join(timeout=60)

    assert second_installed.is_set()
    assert (tmp_path / 'first.pdf').exists()
    assert (tmp_path / 'second.pdf').exists()


_SPAWN_SCRIPT = """
import multiprocessing
import sys

import ocrmypdf

if __name__ == '__main__':
    multiprocessing.set_start_method(sys.argv[3])
    ocrmypdf.ocr(
        sys.argv[1],
        sys.argv[2],
        use_threads=False,
        jobs=2,
        optimize=0,
        output_type='pdf',
        progress_bar=False,
        plugins=['tests/plugins/tesseract_cache.py'],
    )
"""


@pytest.mark.parametrize(
    'start_method',
    [
        'spawn',
        pytest.param(
            'forkserver',
            marks=pytest.mark.skipif(
                'forkserver' not in multiprocessing.get_all_start_methods(),
                reason="forkserver not available",
            ),
        ),
    ],
)
def test_process_workers_see_plugin_options(start_method, resources, tmp_path):
    """Plugin option namespaces must resolve in non-forked worker processes.

    Workers started by spawn or forkserver do not inherit the parent's plugin
    option model registry, so ``options.tesseract`` must still work there
    (#1757).
    """
    script = tmp_path / 'spawn_ocr.py'
    script.write_text(_SPAWN_SCRIPT)
    outpdf = tmp_path / 'out.pdf'
    p = subprocess.run(
        [
            sys.executable,
            str(script),
            str(resources / 'trivial.pdf'),
            str(outpdf),
            start_method,
        ],
        capture_output=True,
        text=True,
        cwd=TESTS_ROOT.parent,
        timeout=180,
        check=False,
    )
    assert p.returncode == 0, p.stderr
    assert "has no attribute 'tesseract'" not in p.stderr
    assert outpdf.exists()
