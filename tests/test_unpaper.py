# © 2015-17 James R. Barlow: github.com/jbarlow83
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

from pathlib import Path
import pytest
from ocrmypdf.exceptions import ExitCode

# pytest.helpers is dynamic
# pylint: disable=no-member
# pylint: disable=w0612

check_ocrmypdf = pytest.helpers.check_ocrmypdf
run_ocrmypdf = pytest.helpers.run_ocrmypdf
spoof = pytest.helpers.spoof

@pytest.fixture(scope='session')
def spoof_unpaper_oldversion(tmpdir_factory):
    return spoof(tmpdir_factory, unpaper='unpaper_oldversion.py')


@pytest.mark.skipif(True, 
                    reason="needs new fixture implementation")
def test_no_unpaper(resources, no_outpdf):
    # <disable unpaper here>
    p, out, err = run_ocrmypdf(
        resources / 'c02-22.pdf', no_outpdf, '--clean', env=os.environ)
    assert p.returncode == ExitCode.missing_dependency


def test_old_unpaper(spoof_unpaper_oldversion, resources, no_outpdf):
    p, out, err = run_ocrmypdf(
        resources / 'c02-22.pdf', no_outpdf, '--clean', 
        env=spoof_unpaper_oldversion)
    assert p.returncode == ExitCode.missing_dependency


def test_clean(spoof_tesseract_noop, resources, outpdf):
    check_ocrmypdf(resources / 'skew.pdf', outpdf, '-c',
                   env=spoof_tesseract_noop)