# © 2017 James R. Barlow: github.com/jbarlow83
#
# This file is part of OCRmyPDF.
#
# OCRmyPDF is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OCRmyPDF is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with OCRmyPDF.  If not, see <http://www.gnu.org/licenses/>.

import os
from contextlib import contextmanager
from os import fspath
from pathlib import Path

import pytest

from ocrmypdf import pdfinfo
from ocrmypdf.exceptions import MissingDependencyError
from ocrmypdf.exec import tesseract

# pylint: disable=no-member,w0621
spoof = pytest.helpers.spoof


def _ensure_tess4():
    if tesseract.v4():
        # "tesseract" on $PATH is already v4
        return os.environ.copy()

    if os.environ.get('OCRMYPDF_TESS4'):
        # OCRMYPDF_TESS4 is a hint environment variable that tells us to look
        # somewhere special for tess4 if and only if we need it. This allows
        # setting OCRMYPDF_TESS4 to test tess4 and PATH to point to tess3
        # on a system with both installed.
        env = os.environ.copy()
        tess4 = Path(os.environ['OCRMYPDF_TESS4'])
        assert tess4.is_file()
        env['PATH'] = tess4.parent + ':' + env['PATH']
        env['OCRMYPDF_TESS4'] = os.environ['OCRMYPDF_TESS4']
        return env

    raise EnvironmentError("Can't find Tesseract 4")


@pytest.fixture
def ensure_tess4():
    return _ensure_tess4()


@contextmanager
def modified_os_environ(env):
    old_env = os.environ.copy()
    os.environ.update(env)
    yield
    for key in env:
        del os.environ[key]
        if key in old_env:
            os.environ[key] = old_env[key]


def tess4_available():
    """Check if a tesseract 4 binary is available, even if it's not the
    official "tesseract" on PATH

    """
    try:
        # _ensure_tess4 locates the tess4 binary we are going to check
        env = _ensure_tess4()
        with modified_os_environ(env):
            # Now jump into this environment and make sure it really is Tess4
            return tesseract.v4() and tesseract.has_textonly_pdf()
    except EnvironmentError:
        pass

    return False


# Skip all tests in this file if not tesseract 4
pytestmark = pytest.mark.skipif(
    not tess4_available(), reason="tesseract 4.0 with textonly_pdf feature required"
)

check_ocrmypdf = pytest.helpers.check_ocrmypdf
run_ocrmypdf = pytest.helpers.run_ocrmypdf
spoof = pytest.helpers.spoof


def test_textonly_pdf(ensure_tess4, resources, outdir):
    check_ocrmypdf(
        resources / 'linn.pdf',
        outdir / 'linn_textonly.pdf',
        '--pdf-renderer',
        'sandwich',
        '--sidecar',
        outdir / 'foo.txt',
        env=ensure_tess4,
    )


def test_pagesize_consistency_tess4(ensure_tess4, resources, outpdf):
    from math import isclose

    infile = resources / 'linn.pdf'

    before_dims = pytest.helpers.first_page_dimensions(infile)

    check_ocrmypdf(
        infile,
        outpdf,
        '--pdf-renderer',
        'sandwich',
        '--clean' if pytest.helpers.have_unpaper() else None,
        '--deskew',
        '--remove-background',
        '--clean-final' if pytest.helpers.have_unpaper() else None,
        env=ensure_tess4,
    )

    after_dims = pytest.helpers.first_page_dimensions(outpdf)

    assert isclose(before_dims[0], after_dims[0])
    assert isclose(before_dims[1], after_dims[1])


@pytest.mark.parametrize('basename', ['graph_ocred.pdf', 'cardinal.pdf'])
def test_skip_pages_does_not_replicate(ensure_tess4, resources, basename, outdir):
    infile = resources / basename
    outpdf = outdir / basename

    check_ocrmypdf(
        infile,
        outpdf,
        '--pdf-renderer',
        'sandwich',
        '--force-ocr',
        '--tesseract-timeout',
        '0',
        env=ensure_tess4,
    )

    info_in = pdfinfo.PdfInfo(infile)

    info = pdfinfo.PdfInfo(outpdf)
    for page in info:
        assert len(page.images) == 1, "skipped page was replicated"

    for n in range(len(info_in)):
        assert info[n].width_inches == info_in[n].width_inches


def test_content_preservation(ensure_tess4, resources, outpdf):
    infile = resources / 'masks.pdf'

    check_ocrmypdf(
        infile,
        outpdf,
        '--pdf-renderer',
        'sandwich',
        '--tesseract-timeout',
        '0',
        env=ensure_tess4,
    )

    info = pdfinfo.PdfInfo(outpdf)
    page = info[0]
    assert len(page.images) > 1, "masks were rasterized"


def test_no_languages(ensure_tess4, tmpdir):
    env = ensure_tess4
    (tmpdir / 'tessdata').mkdir()
    env['TESSDATA_PREFIX'] = fspath(tmpdir)

    with modified_os_environ(env):
        with pytest.raises(MissingDependencyError):
            tesseract.languages.cache_clear()
            tesseract.languages()
