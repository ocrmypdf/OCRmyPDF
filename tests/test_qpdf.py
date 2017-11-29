# © 2017 James R. Barlow: github.com/jbarlow83

import logging
import resource
import pytest

from ocrmypdf.exec import ghostscript, tesseract, qpdf
from ocrmypdf.pdfinfo import PdfInfo


@pytest.mark.skipif(
    qpdf.version() < '7.0.0',
    reason="negzero.pdf crashes earlier versions")
def test_qpdf_negative_zero(resources, outpdf):
    negzero = resources / 'negzero.pdf'
    hugemono = resources / 'hugemono.pdf'
    # raises exception on err
    qpdf.merge([str(negzero), str(hugemono)], outpdf, log=logging.getLogger())
    

@pytest.mark.timeout(15)
@pytest.mark.parametrize('max_files,skip', [
    (2, 0),  # Can we merge correctly without opening more than 2 files at once?
    (16, 0), # And does this work properly when we can one-shot it?
    (2, 1),  # Or playing with even/odd
    (3, 0)   # Or odd step size
    ])
def test_qpdf_merge_correctness(resources, outpdf, max_files, skip):
    # All of these must be only one page long
    inputs = [
        '2400dpi.pdf', 'aspect.pdf', 'blank.pdf', 'ccitt.pdf', 
        'linn.pdf', 'masks.pdf', 'poster.pdf', 'overlay.pdf',
        'skew.pdf', 'trivial.pdf']
    
    input_files = [str(resources / f) for f in inputs]

    qpdf.merge(
        input_files[skip:], outpdf, log=logging.getLogger(), 
        max_files=max_files)
    assert len(PdfInfo(outpdf).pages) == len(input_files[skip:])
    

@pytest.mark.timeout(15)
@pytest.mark.skipif(
    True, 
    reason='qpdf binary cannot open multiple files multiple times')
def test_page_merge_ulimit(resources, outpdf):
    # Ensure we can merge pages without opening one file descriptor per page
    ulimits = resource.getrlimit(resource.RLIMIT_NOFILE)
    page_count = ulimits[0]
    print(page_count)
    input_files = [str(resources / 'trivial.pdf')] * page_count

    qpdf.merge(input_files, outpdf, log=logging.getLogger())

