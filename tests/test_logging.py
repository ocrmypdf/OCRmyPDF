# SPDX-FileCopyrightText: 2022 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import logging

from ocrmypdf._pipelines._common import configure_debug_logging


def test_debug_logging(tmp_path):
    # Just exercise the debug logger but don't validate it
    # See https://github.com/pytest-dev/pytest/issues/5502 for pytest logging quirks
    prefix = 'test_debug_logging'
    log = logging.getLogger(prefix)
    _handler, remover = configure_debug_logging(tmp_path / 'test.log', prefix)
    log.info("test message")
    remover()
