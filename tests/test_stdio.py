# SPDX-FileCopyrightText: 2022 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import io
import os
import sys
from pathlib import Path
from subprocess import DEVNULL, PIPE, run

import pytest

from ocrmypdf import _stdoutprotect
from ocrmypdf._version import __version__
from ocrmypdf.helpers import check_pdf

from .conftest import run_ocrmypdf


def test_stdin(ocrmypdf_exec, resources, outpdf):
    input_file = str(resources / 'francais.pdf')
    output_file = str(outpdf)

    # Runs: ocrmypdf - output.pdf < testfile.pdf
    with Path(input_file).open('rb') as input_stream:
        p_args = ocrmypdf_exec + [
            '-',
            output_file,
            '--plugin',
            'tests/plugins/tesseract_noop.py',
        ]
        run(p_args, capture_output=True, stdin=input_stream, check=True)


def test_stdout(ocrmypdf_exec, resources, outpdf):
    if 'COV_CORE_DATAFILE' in os.environ:
        pytest.skip("Coverage uses stdout")

    input_file = str(resources / 'francais.pdf')
    output_file = str(outpdf)

    # Runs: ocrmypdf francais.pdf - > test_stdout.pdf
    with Path(output_file).open('wb') as output_stream:
        p_args = ocrmypdf_exec + [
            input_file,
            '-',
            '--plugin',
            'tests/plugins/tesseract_noop.py',
        ]
        run(p_args, stdout=output_stream, stderr=PIPE, stdin=DEVNULL, check=True)

    assert check_pdf(output_file)


def test_stdout_protected_from_pollution(ocrmypdf_exec, resources, outpdf):
    if 'COV_CORE_DATAFILE' in os.environ:
        pytest.skip("Coverage uses stdout")

    input_file = str(resources / 'francais.pdf')
    output_file = str(outpdf)

    # A plugin deliberately writes garbage to stdout during the run. With stdout
    # protection active, that garbage must be diverted to stderr and never reach
    # the PDF we are writing to stdout.
    with Path(output_file).open('wb') as output_stream:
        p_args = ocrmypdf_exec + [
            input_file,
            '-',
            '--plugin',
            'tests/plugins/tesseract_noop.py',
            '--plugin',
            'tests/plugins/stdout_polluter.py',
        ]
        p = run(p_args, stdout=output_stream, stderr=PIPE, stdin=DEVNULL, check=True)

    assert check_pdf(output_file), "PDF on stdout was corrupted"
    with Path(output_file).open('rb') as f:
        assert b'POLLUTION' not in f.read(), "pollution leaked into the PDF"
    assert b'POLLUTION' in p.stderr, "pollution was not diverted to stderr"


@pytest.mark.skipif(os.name == 'nt', reason='Windows does not support /dev/null')
def test_dev_null(resources):
    if 'COV_CORE_DATAFILE' in os.environ:
        pytest.skip("Coverage uses stdout")

    p = run_ocrmypdf(
        resources / 'trivial.pdf',
        os.devnull,
        '--force-ocr',
        '--plugin',
        'tests/plugins/tesseract_noop.py',
    )
    assert p.returncode == 0, "could not send output to /dev/null"
    assert len(p.stdout) == 0, "wrote to stdout"


# --- argparse output must survive stdout protection ---
#
# run() installs stdout protection before argparse sees the command line, so
# anything argparse prints would land on stderr unless it is routed back to the
# preserved real stdout. `ver=$(ocrmypdf --version)` has to work.


def test_version_goes_to_stdout(ocrmypdf_exec):
    p = run(ocrmypdf_exec + ['--version'], capture_output=True, text=True, check=True)
    assert p.stdout.strip() == __version__
    assert __version__ not in p.stderr


def test_help_goes_to_stdout(ocrmypdf_exec):
    p = run(ocrmypdf_exec + ['--help'], capture_output=True, text=True, check=True)
    assert p.stdout.startswith('usage: OCRmyPDF')
    assert 'usage: OCRmyPDF' not in p.stderr


def test_argparse_error_goes_to_stderr(ocrmypdf_exec):
    p = run(
        ocrmypdf_exec + ['--no-such-option'],
        capture_output=True,
        text=True,
        check=False,
    )
    assert p.returncode != 0
    assert 'error:' in p.stderr
    assert p.stdout == ''


# --- stdout protection unit tests ---
#
# protect_stdout() mutates process-global file descriptors, so the only test
# that installs it for real runs in a subprocess. Everything else exercises the
# paths that decline to install protection, and must leave the module inert.


@pytest.fixture
def unprotected_stdout():
    """Guarantee stdout protection is inert, and stays that way afterwards."""
    if _stdoutprotect._active:
        pytest.skip("stdout protection is already active in this process")
    yield
    assert not _stdoutprotect._active, "test installed stdout protection in-process"
    assert _stdoutprotect._saved_fd is None, "test duplicated a file descriptor"


class _FdlessStdout:
    """A stdout replacement backed by an OS file descriptor we control."""

    def __init__(self, fileno_result):
        self._fileno_result = fileno_result
        self.flushed = False

    def fileno(self):
        if isinstance(self._fileno_result, Exception):
            raise self._fileno_result
        return self._fileno_result

    def flush(self):
        self.flushed = True


def test_protect_stdout_declines_without_fileno(monkeypatch, unprotected_stdout):
    """An in-memory stdout has no file descriptor to protect."""
    monkeypatch.setattr(sys, 'stdout', io.StringIO())
    assert _stdoutprotect.protect_stdout() is False


@pytest.mark.parametrize(
    'error',
    [
        AttributeError("no fileno"),
        OSError("detached"),
        ValueError("closed file"),
    ],
)
def test_protect_stdout_declines_when_fileno_raises(
    monkeypatch, unprotected_stdout, error
):
    """Any failure to obtain the descriptor declines protection, never raises."""
    monkeypatch.setattr(sys, 'stdout', _FdlessStdout(error))
    assert _stdoutprotect.protect_stdout() is False


def test_protect_stdout_declines_when_dup_fails(monkeypatch, unprotected_stdout):
    """If the descriptor cannot be duplicated, fd 1 must be left untouched."""
    fake_stdout = _FdlessStdout(1)
    monkeypatch.setattr(sys, 'stdout', fake_stdout)

    def refuse_dup(fd):
        raise OSError("out of file descriptors")

    real_dup2 = os.dup2
    dup2_calls = []

    def recording_dup2(fd, fd2, *args, **kwargs):
        dup2_calls.append((fd, fd2))
        return real_dup2(fd, fd2, *args, **kwargs)

    monkeypatch.setattr(os, 'dup', refuse_dup)
    monkeypatch.setattr(os, 'dup2', recording_dup2)

    assert _stdoutprotect.protect_stdout() is False
    assert dup2_calls == [], "fd 1 was redirected despite dup() failing"
    assert fake_stdout.flushed, "stdout should be flushed before being duplicated"


def test_accessors_report_inactive_when_protection_not_installed(unprotected_stdout):
    """Callers must be able to detect that they should use sys.stdout instead."""
    assert _stdoutprotect.get_protected_stdout_fd() is None
    assert _stdoutprotect.protected_stdout_isatty() is None


PROTECT_STDOUT_CHILD = """
import os, sys
from ocrmypdf._stdoutprotect import (
    get_protected_stdout_fd,
    protect_stdout,
    protected_stdout_isatty,
)

assert get_protected_stdout_fd() is None, 'fd reported before protection'
assert protected_stdout_isatty() is None, 'isatty reported before protection'

assert protect_stdout() is True, 'protection not installed'
assert protect_stdout() is True, 'repeat call did not report already-active'

fd = get_protected_stdout_fd()
assert isinstance(fd, int) and fd != 1, f'bad protected fd {fd!r}'
# The real stdout here is a pipe, and the saved descriptor must report on it,
# not on stderr which fd 1 now points to.
assert protected_stdout_isatty() is False, 'isatty did not consult the saved fd'

os.write(1, b'POLLUTION-FD')
sys.stdout.write('POLLUTION-PRINT')
sys.stdout.flush()
os.write(fd, b'REAL-STDOUT-PAYLOAD')
"""


@pytest.mark.skipif(os.name == 'nt', reason='POSIX file descriptor semantics')
def test_protected_stdout_diverts_stray_writes_to_stderr():
    """Installed for real: fd 1 goes to stderr, the saved fd carries the payload."""
    p = run(
        [sys.executable, '-c', PROTECT_STDOUT_CHILD],
        capture_output=True,
        stdin=DEVNULL,
        check=False,
    )
    assert p.returncode == 0, p.stderr.decode('utf-8', 'replace')
    assert b'REAL-STDOUT-PAYLOAD' in p.stdout, "payload did not reach the real stdout"
    assert b'POLLUTION-FD' not in p.stdout, "raw fd 1 write corrupted real stdout"
    assert b'POLLUTION-PRINT' not in p.stdout, "print() corrupted real stdout"
    assert b'POLLUTION-FD' in p.stderr, "fd 1 write was not diverted to stderr"
    assert b'POLLUTION-PRINT' in p.stderr, "print() was not diverted to stderr"
