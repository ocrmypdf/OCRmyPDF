# © 2021 James R. Barlow: github.com/jbarlow83
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from ocrmypdf import hookimpl


@hookimpl
def filter_pdf_page(
    page, image_filename, output_pdf
):  # pylint: disable=unused-argument
    return output_pdf
