# © 2015 James R. Barlow: github.com/jbarlow83
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

"""
Generate a PDFMARK file for Ghostscript >= 9.14, for PDF/A conversion

pdfmark is an extension to the Postscript language that describes some PDF
features like bookmarks and annotations. It was originally specified Adobe
Distiller, for Postscript to PDF conversion:
https://www.adobe.com/content/dam/acom/en/devnet/acrobat/pdfs/pdfmark_reference.pdf

Ghostscript uses pdfmark for PDF to PDF/A conversion as well. To use Ghostscript
to create a PDF/A, we need to create a pdfmark file with the necessary metadata.

This takes care of the many version-specific bugs and pecularities in
Ghostscript's handling of pdfmark.

"""

from binascii import hexlify
from datetime import datetime
from pathlib import Path
from string import Template
import pkg_resources
import os

from libxmp.utils import file_to_dict
from libxmp import consts


ICC_PROFILE_RELPATH = 'data/sRGB.icc'

SRGB_ICC_PROFILE = pkg_resources.resource_filename(
    'ocrmypdf', ICC_PROFILE_RELPATH)


# This is a template written in PostScript which is needed to create PDF/A
# files, from the Ghostscript documentation. Lines beginning with % are
# comments. Python substitution variables have a '$' prefix.
pdfa_def_template = u"""%!
% Define entries in the document Info dictionary :
/ICCProfile $icc_profile
def

[$docinfo
  /DOCINFO pdfmark

% Define an ICC profile :

[/_objdef {icc_PDFA} /type /stream /OBJ pdfmark
[{icc_PDFA}
<<
  /N currentpagedevice /ProcessColorModel known {
    currentpagedevice /ProcessColorModel get dup /DeviceGray eq
    {pop 1} {
      /DeviceRGB eq
      {3}{4} ifelse
    } ifelse
  } {
    (ERROR, unable to determine ProcessColorModel) == flush
  } ifelse
>> /PUT pdfmark
[{icc_PDFA} ICCProfile (r) file /PUT pdfmark

% Define the output intent dictionary :

[/_objdef {OutputIntent_PDFA} /type /dict /OBJ pdfmark
[{OutputIntent_PDFA} <<
  /Type /OutputIntent             % Must be so (the standard requires).
  /S /GTS_PDFA1                   % Must be so (the standard requires).
  /DestOutputProfile {icc_PDFA}            % Must be so (see above).
  /OutputConditionIdentifier ($icc_identifier)
>> /PUT pdfmark
[{Catalog} <</OutputIntents [ {OutputIntent_PDFA} ]>> /PUT pdfmark
"""


def encode_text_string(s: str) -> str:
    """
    Encode text string to hex string for use in a PDF

    From PDF 32000-1:2008 a string object may be included in hexademical form
    if it is enclosed in angle brackets.  For general Unicode the string should
    be UTF-16 (big endian) with byte order marks.  Many strings including all
    ASCII strings could be encoded as PdfDocEncoding literals provided
    that certain Postscript sequences are escaped.  But it's far simpler to
    encode everything as UTF-16.
    """

    # Sometimes lazy C programmers leave their NULs at the end of strings they
    # insert into PDFs
    # tests/resources/aspect.pdf is one example (created by ImageMagick)
    s = s.replace('\x00', '')

    if s == '':
        return ''

    utf16_bytes = s.encode('utf-16be')
    ascii_hex_bytes = hexlify(b'\xfe\xff' + utf16_bytes)
    ascii_hex_str = ascii_hex_bytes.decode('ascii').lower()
    return ascii_hex_str


def _encode_ascii(s: str) -> str:
    """
    Aggressively strip non-ASCII and PDF escape sequences

    Ghostscript 9.24+ lost support for UTF-16BE in pdfmark files for reasons
    given in GhostPDL commit e997c683. Our temporary workaround is use ASCII
    and drop all non-ASCII characters. A slightly improved alternative would
    be to implement PdfDocEncoding in pikepdf and encode to that, or handle
    metadata there.
    """
    trans = str.maketrans({
        '(': '',
        ')': '',
        '\\': '',
        '\0': ''
    })
    return s.translate(trans).encode('ascii', errors='replace').decode()


def encode_pdf_date(d: datetime) -> str:
    """
    Encode Python datetime object as PDF date string

    From Adobe pdfmark manual:
    (D:YYYYMMDDHHmmSSOHH'mm')
    D: is an optional prefix. YYYY is the year. All fields after the year are
    optional. MM is the month (01-12), DD is the day (01-31), HH is the
    hour (00-23), mm are the minutes (00-59), and SS are the seconds
    (00-59). The remainder of the string defines the relation of local
    time to GMT. O is either + for a positive difference (local time is
    later than GMT) or - (minus) for a negative difference. HH' is the
    absolute value of the offset from GMT in hours, and mm' is the
    absolute value of the offset in minutes. If no GMT information is
    specified, the relation between the specified time and GMT is
    considered unknown. Regardless of whether or not GMT
    information is specified, the remainder of the string should specify
    the local time.
    """

    pdfmark_date_fmt = r'%Y%m%d%H%M%S'
    s = d.strftime(pdfmark_date_fmt)

    tz = d.strftime('%z')
    if tz == 'Z' or tz == '':
        # Ghostscript <= 9.23 handles missing timezones incorrectly, so if
        # timezone is missing, move it into GMT.
        # https://bugs.ghostscript.com/show_bug.cgi?id=699182
        s += "+00'00'"
    else:
        sign, tz_hours, tz_mins = tz[0], tz[1:3], tz[3:5]
        s += "{}{}'{}'".format(sign, tz_hours, tz_mins)
    return s


def decode_pdf_date(s: str) -> datetime:
    """
    Decode a pdfmark date to a Python datetime object

    A pdfmark date is a string in a paritcular format. See the pdfmark
    Reference for the specification.

    """
    if s.startswith('D:'):
        s = s[2:]

    # Literal Z00'00', is incorrect but found in the wild,
    # probably made by OS X Quartz -- standardize
    if s.endswith("Z00'00'"):
        s = s.replace("Z00'00'", '+0000')
    elif s.endswith('Z'):
        s = s.replace('Z', '+0000')

    s = s.replace("'", "")  # Remove apos from PDF time strings

    return datetime.strptime(s, r'%Y%m%d%H%M%S%z')


def _get_pdfmark_dates(pdfmark):
    """
    Encode dates in the expected format for pdfmark Postscript

    The best way to deal with amissing date entry is set it to null, because if
    the key is omitted Ghostscript will set it to now - we do not want to erase
    the fact that the value was unknown.  Setting to an empty string breaks
    Ghostscript 9.22 as reported here:
    https://bugs.ghostscript.com/show_bug.cgi?id=699182
    """

    for key in ('/CreationDate', '/ModDate'):
        if key not in pdfmark:
            continue
        if pdfmark[key].strip() == '':
            yield '  {} null'.format(key)
            continue
        date_str = pdfmark[key]
        if date_str.startswith('D:'):
            date_str = date_str[2:]
        try:
            yield '  {} (D:{})'.format(
                    key,
                    encode_pdf_date(decode_pdf_date(date_str)))
        except ValueError:
            yield '  {} null'.format(key)


def _get_pdfa_def(icc_profile, icc_identifier, pdfmark, ascii_docinfo=False):
    """
    Create a Postscript pdfmark file for Ghostscript.

    pdfmark contains the various objects as strings; these must be encoded in
    ASCII, and dates have a special format.

    :param icc_profile: filename of the ICC profile to include in pdfmark
    :param icc_identifier: ICC identifier such as 'sRGB'
    :param pdfmark: a dictionary containing keys to include the pdfmark
    :param ascii_docinfo: if True, the docinfo block must be encoded in pure
        ASCII and may not contain UTF-16BE-BOM-hex encoded strings, as
        required for Ghostscript 9.24+

    :returns: a string containing the entire pdfmark

    """

    # Ghostscript <= 9.21 has a bug where null entries in DOCINFO might produce
    # ERROR: VMerror (-25) on closing pdfwrite device.
    # https://bugs.ghostscript.com/show_bug.cgi?id=697684
    # Work around this by only adding keys that have a nontrivial value
    docinfo_keys = ('/Title', '/Author', '/Subject', '/Creator', '/Keywords')

    def docinfo_gen():
        if not ascii_docinfo:
            docinfo_line_template = '  {key} <{value}>'
            encode = encode_text_string
        else:
            docinfo_line_template = '  {key} ({value})'
            encode = _encode_ascii
        yield from _get_pdfmark_dates(pdfmark)
        for key in docinfo_keys:
            if key in pdfmark and pdfmark[key].strip() != '':
                line = docinfo_line_template.format(
                    key=key, value=encode(pdfmark[key]))
                yield line
    docinfo = '\n'.join(docinfo_gen())

    t = Template(pdfa_def_template)
    result = t.substitute(icc_profile=icc_profile,
                          icc_identifier=icc_identifier,
                          docinfo=docinfo)
    return result


def generate_pdfa_ps(target_filename, pdfmark, icc='sRGB', ascii_docinfo=False):
    if icc == 'sRGB':
        icc_profile = SRGB_ICC_PROFILE
    else:
        raise NotImplementedError("Only supporting sRGB")

    # pdfmark must contain the full path to the ICC profile, and pdfmark must
    # also encoded in ASCII. ocrmypdf can be installed anywhere, including to
    # paths that have a non-ASCII character in the filename. Ghostscript
    # accepts hex-encoded strings and converts them to byte strings, so
    # we encode the path with fsencode() and use the hex representation.
    # UTF-16 not accepted here. (Even though ASCII encodable is the usual case,
    # do this always to avoid making it a rare conditional.)
    bytes_icc_profile = os.fsencode(icc_profile)
    hex_icc_profile = hexlify(bytes_icc_profile)
    icc_profile = '<' + hex_icc_profile.decode('ascii') + '>'

    ps = _get_pdfa_def(icc_profile, icc, pdfmark, ascii_docinfo=ascii_docinfo)

    # We should have encoded everything to pure ASCII by this point, and
    # to be safe, only allow ASCII in PostScript
    Path(target_filename).write_text(ps, encoding='ascii')


def file_claims_pdfa(filename):
    """Determines if the file claims to be PDF/A compliant

    Checking if a file is a truly compliant PDF/A is a massive undertaking
    that no open source tool does properly.  Some commercial tools are
    generally reliable (Acrobat).

    This checks if the XMP metadata contains a PDF/A marker.
    """

    xmp = file_to_dict(filename)
    if not xmp:
        return {'pass': False, 'output': 'pdf',
                'conformance': 'No XMP metadata'}

    if not consts.XMP_NS_PDFA_ID in xmp:
        return {'pass': False, 'output': 'pdf',
                'conformance': 'No PDF/A metadata in XMP'}

    pdfa_node = xmp[consts.XMP_NS_PDFA_ID]
    def read_node(node, key):
        return next(
            (v for k, v, meta in node if k == key), ''
        )

    part = read_node(pdfa_node, 'pdfaid:part')
    conformance = read_node(pdfa_node, 'pdfaid:conformance')

    part_conformance = part + conformance
    valid_part_conforms = {'1A', '1B', '2A', '2B', '2U', '3A', '3B', '3U'}

    conformance = 'PDF/A-{}'.format(
        part_conformance)

    pdfa_dict = {}
    if part_conformance in valid_part_conforms:
        pdfa_dict['pass'] = True
        pdfa_dict['output'] = 'pdfa'
    pdfa_dict['conformance'] = conformance

    return pdfa_dict
