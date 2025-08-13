# SPDX-FileCopyrightText: 2025 The OCRmyPDF authors
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from pathlib import Path

import pytest

from tests.conftest import check_ocrmypdf
import pikepdf
import time


def _doc_ids(path: Path) -> tuple[bytes, bytes]:
    with pikepdf.open(path) as pdf:
        id0, id1 = pdf.trailer.ID
        return bytes(id0), bytes(id1)

@pytest.mark.parametrize("deterministic_id", [True, False])
def test_deterministic_id(resources: Path, tmp_path: Path, deterministic_id: bool):
    # Create two outputs without deterministic-id; IDs should differ over time
    out1 = check_ocrmypdf(
        resources / "trivial.pdf",
        tmp_path / "nd1.pdf",
        "--output-type=pdf",
        "--optimize",
        "0",
        *( ["--deterministic-output"] if deterministic_id else [] ),
    )
    time.sleep(1.1)
    out2 = check_ocrmypdf(
        resources / "trivial.pdf",
        tmp_path / "nd2.pdf",
        "--output-type=pdf",
        "--optimize",
        "0",
        *( ["--deterministic-output"] if deterministic_id else [] ),
    )
    ids1 = _doc_ids(out1)
    ids2 = _doc_ids(out2)
    assert (ids1 == ids2) == deterministic_id
