# SPDX-FileCopyrightText: 2026 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

"""Internal values passed between functions are frozen, slotted dataclasses."""

from __future__ import annotations

import dataclasses
import pickle
from importlib import import_module
from pathlib import Path

import pytest

CONTAINERS = [
    ('ocrmypdf._exec.ghostscript', 'StyleLostSubstitution'),
    ('ocrmypdf._exec.unpaper', '_UnpaperIO'),
    ('ocrmypdf._graft', 'Fpdf2PageInfo'),
    ('ocrmypdf._graft', 'Fpdf2ParsedPage'),
    ('ocrmypdf._graft', '_StrippedContent'),
    ('ocrmypdf._metadata', 'ZonedPdfDate'),
    ('ocrmypdf._pageboxes', 'BoxRepair'),
    ('ocrmypdf._pageboxes', 'BoxRepairMessage'),
    ('ocrmypdf._pageboxes', '_ParsedBox'),
    ('ocrmypdf._pipeline', 'RasterDpi'),
    ('ocrmypdf._pipeline', 'OcrEngineOutput'),
    ('ocrmypdf._pipeline', 'FinishedPdf'),
    ('ocrmypdf._pipeline', 'FileSizeRatio'),
    ('ocrmypdf._pipeline', 'CompressedRange'),
    ('ocrmypdf._pipelines._common', 'HOCRResult'),
    ('ocrmypdf._pipelines._common', 'IntermediateImages'),
    ('ocrmypdf._pipelines._common', 'PageImages'),
    ('ocrmypdf._validation', 'InputFile'),
    ('ocrmypdf.builtin_plugins.ghostscript', '_JpegSignature'),
    ('ocrmypdf.builtin_plugins.ghostscript', '_JpegStream'),
    ('ocrmypdf.builtin_plugins.pypdfium', '_RenderedBitmap'),
    ('ocrmypdf.builtin_plugins.pypdfium', '_OutputImage'),
    ('ocrmypdf.builtin_plugins.rapidocr_ocr', 'RecModel'),
    ('ocrmypdf.builtin_plugins.rapidocr_ocr', 'OrientationLines'),
    ('ocrmypdf.builtin_plugins.rapidocr_ocr', 'OrientationCrops'),
    ('ocrmypdf.builtin_plugins.rapidocr_ocr', '_EngineConfig'),
    ('ocrmypdf.builtin_plugins.rapidocr_ocr', '_PageImage'),
    ('ocrmypdf.builtin_plugins.rapidocr_ocr', '_ReadingEdges'),
    ('ocrmypdf.builtin_plugins.rapidocr_ocr', '_WordQuad'),
    ('ocrmypdf.builtin_plugins.rapidocr_ocr', '_InkMetrics'),
    ('ocrmypdf.builtin_plugins.rapidocr_ocr', '_Column'),
    ('ocrmypdf.builtin_plugins.rapidocr_ocr', '_Band'),
    ('ocrmypdf.builtin_plugins.rapidocr_ocr', '_LineShape'),
    ('ocrmypdf.builtin_plugins.rapidocr_ocr', 'ModelFile'),
    ('ocrmypdf.builtin_plugins.rapidocr_ocr', 'ModelOrientation'),
    ('ocrmypdf.builtin_plugins.rapidocr_ocr', 'AxisVotes'),
    ('ocrmypdf.font.system_font_provider', '_NotoCandidate'),
    ('ocrmypdf.fpdf_renderer.renderer', 'CoordinateTransform'),
    ('ocrmypdf.fpdf_renderer.renderer', 'WordRenderData'),
    ('ocrmypdf.optimize', '_ImageXrefs'),
    ('ocrmypdf.optimize', '_JpegResult'),
    ('ocrmypdf.optimize', '_DeflateResult'),
    ('ocrmypdf.subprocess._run', '_ProcessSetup'),
]


@pytest.mark.parametrize(
    'module, name', CONTAINERS, ids=[f'{m}.{n}' for m, n in CONTAINERS]
)
def test_container_is_frozen_slotted_dataclass(module, name):
    cls = getattr(import_module(module), name)
    assert dataclasses.is_dataclass(cls)
    assert cls.__dataclass_params__.frozen
    assert '__slots__' in vars(cls)


def test_hocr_result_survives_worker_boundary():
    from ocrmypdf._pipelines._common import HOCRResult

    result = HOCRResult(pageno=3, hocr=Path('a.hocr'), orientation_correction=90)
    assert pickle.loads(pickle.dumps(result)) == result
    assert HOCRResult.from_json(result.to_json()) == result
    with pytest.raises(dataclasses.FrozenInstanceError):
        result.textpdf = Path('b.pdf')  # type: ignore[misc]
