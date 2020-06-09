# © 2020 James R. Barlow: github.com/jbarlow83
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

import logging

from ocrmypdf import hookimpl
from ocrmypdf._exec import ghostscript
from ocrmypdf._validation import HOCR_OK_LANGS
from ocrmypdf.exceptions import MissingDependencyError
from ocrmypdf.subprocess import check_external_program

log = logging.getLogger(__name__)


@hookimpl
def check_options(options):
    gs_version = ghostscript.version()
    check_external_program(
        program='gs',
        package='ghostscript',
        version_checker=gs_version,
        need_version='9.15',  # limited by Travis CI / Ubuntu 14.04 backports
    )
    if gs_version in ('9.24', '9.51'):
        raise MissingDependencyError(
            f"Ghostscript {gs_version} contains serious regressions and is not "
            "supported. Please upgrade to a newer version, or downgrade to the "
            "previous version."
        )

    # We have these constraints to check for.
    # 1. Ghostscript < 9.20 mangles multibyte Unicode
    # 2. hocr doesn't work on non-Latin languages (so don't select it)
    is_latin = options.languages.issubset(HOCR_OK_LANGS)
    if gs_version < '9.20' and options.output_type != 'pdf' and not is_latin:
        # https://bugs.ghostscript.com/show_bug.cgi?id=696874
        # Ghostscript < 9.20 fails to encode multibyte characters properly
        msg = (
            "The installed version of Ghostscript does not work correctly "
            "with the OCR languages you specified. Use --output-type pdf or "
            "upgrade to Ghostscript 9.20 or later to avoid this issue."
        )
        msg += f"Found Ghostscript {gs_version}"
        log.warning(msg)

    if options.output_type == 'pdfa':
        options.output_type = 'pdfa-2'

    if options.output_type == 'pdfa-3' and ghostscript.version() < '9.19':
        raise MissingDependencyError(
            "--output-type pdfa-3 requires Ghostscript 9.19 or later"
        )


@hookimpl
def rasterize_pdf_page(
    input_file,
    output_file,
    raster_device,
    raster_dpi,
    pageno,
    page_dpi=None,
    rotation=None,
    filter_vector=False,
):
    ghostscript.rasterize_pdf(
        input_file,
        output_file,
        raster_device=raster_device,
        raster_dpi=raster_dpi,
        pageno=pageno,
        page_dpi=page_dpi,
        rotation=rotation,
        filter_vector=filter_vector,
    )
    return output_file


@hookimpl
def generate_pdfa(pdf_pages, pdfmark, output_file, compression, pdf_version, pdfa_part):
    ghostscript.generate_pdfa(
        pdf_pages=[*pdf_pages, pdfmark],
        output_file=output_file,
        compression=compression,
        pdf_version=pdf_version,
        pdfa_part=pdfa_part,
    )
    return output_file
