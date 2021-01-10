# © 2021 James R. Barlow: github.com/jbarlow83
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import logging

import pytest

from ocrmypdf._sync import configure_debug_logging


def test_debug_logging(tmp_path):
    # Just exercise the debug logger but don't validate it
    # See https://github.com/pytest-dev/pytest/issues/5502 for pytest logging quirks
    prefix = 'test_debug_logging'
    log = logging.getLogger(prefix)
    handler = configure_debug_logging(tmp_path / 'test.log', prefix)
    log.info("test message")
    log.removeHandler(handler)
