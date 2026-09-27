# SPDX-FileCopyrightText: 2022 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import shutil
from unittest.mock import MagicMock

from ocrmypdf.helpers import check_pdf


def test_pdf_error(resources):
    assert check_pdf(resources / 'blank.pdf')
    assert not check_pdf(__file__)


def test_check_pdf_reports_progress(resources):
    percents = []
    assert check_pdf(resources / 'blank.pdf', progress=percents.append)
    assert percents
    assert percents[-1] == 100


class _RecordingProgressBar:
    instances: list[_RecordingProgressBar] = []

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.completed: list[int] = []
        _RecordingProgressBar.instances.append(self)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def update(self, n=1, *, completed=None):
        self.completed.append(completed)


def test_report_output_pdf_shows_check_progress(resources, outpdf):
    from ocrmypdf._options import OcrOptions
    from ocrmypdf._pipelines._common import report_output_pdf
    from ocrmypdf.exceptions import ExitCode

    shutil.copy(resources / 'blank.pdf', outpdf)
    options = OcrOptions(
        input_file=resources / 'blank.pdf',
        output_file=outpdf,
        output_type='pdf',
        progress_bar=True,
    )
    plugin_manager = MagicMock()
    plugin_manager.get_progressbar_class.return_value = _RecordingProgressBar
    _RecordingProgressBar.instances.clear()

    exitcode = report_output_pdf(
        options, resources / 'blank.pdf', [], plugin_manager=plugin_manager
    )

    assert exitcode == ExitCode.ok
    (pbar,) = _RecordingProgressBar.instances
    assert pbar.kwargs['desc'] == "Checking output"
    assert not pbar.kwargs['disable']
    assert pbar.completed[-1] == 100
