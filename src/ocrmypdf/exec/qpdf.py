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

"""Interface to qpdf executable"""

from io import StringIO

import pikepdf


def version():
    return pikepdf.__libqpdf_version__


def check(input_file, log=None):
    pdf = None
    try:
        pdf = pikepdf.open(input_file)
    except pikepdf.PdfError as e:
        if log:
            log.error(e)
        return False
    else:
        messages = pdf.check()
        for msg in messages:
            if 'error' in msg.lower():
                log.error(msg)
            else:
                log.warning(msg)

        sio = StringIO()
        linearize = None
        try:
            pdf.check_linearization(sio)
        except RuntimeError:
            pass
        else:
            linearize = sio.getvalue()
            if linearize:
                log.warning(linearize)

        if not messages and not linearize:
            return True
        return False
    finally:
        if pdf:
            pdf.close()
