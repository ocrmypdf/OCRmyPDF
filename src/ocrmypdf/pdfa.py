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

# Generate a PDFA_def.ps file for Ghostscript >= 9.14

from string import Template
from binascii import hexlify
from datetime import datetime
from xml.parsers.expat import ExpatError
import pkg_resources
import PyPDF2 as pypdf
from defusedxml.minidom import parseString as defused_parseString
from unittest.mock import patch

ICC_PROFILE_RELPATH = 'data/sRGB.icc'

SRGB_ICC_PROFILE = pkg_resources.resource_filename(
    'ocrmypdf', ICC_PROFILE_RELPATH)


# This is a template written in PostScript which is needed to create PDF/A
# files, from the Ghostscript documentation. Lines beginning with % are
# comments. Python substitution variables have a '$' prefix.
pdfa_def_template = u"""%!
% This is derived from Ghostscript's template for creating a PDF/A document.
% This is a small PostScript program that includes some necessary information
% to create a PDF/A compliant file.

% Define entries in the document Info dictionary :
/ICCProfile ($icc_profile)
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
    '''Encode text string to hex string for use in a PDF

    From PDF 32000-1:2008 a string object may be included in hexademical form
    if it is enclosed in angle brackets.  For general Unicode the string should
    be UTF-16 (big endian) with byte order marks.  Many strings including all
    ASCII strings could be encoded as PdfDocEncoding literals provided
    that certain Postscript sequences are escaped.  But it's far simpler to
    encode everything as UTF-16.
    '''

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


def encode_pdf_date(d: datetime) -> str:
    """Encode Python datetime object as PDF date string

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
    """Encode dates for pdfmark Postscript.  The best way to deal with a
    missing date entry is set it to null, because if the key is omitted 
    Ghostscript will set it to now - we do not want to erase the fact that
    the value was unknown.  Setting to an empty string breaks Ghostscript
    9.22 as reported here:
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


def _get_pdfa_def(icc_profile, icc_identifier, pdfmark):
    """Create a Postscript file for Ghostscript.  pdfmark contains the various
    objects as strings; these must be encoded in ASCII, and dates have a 
    special format."""

    # Ghostscript <= 9.21 has a bug where null entries in DOCINFO might produce
    # ERROR: VMerror (-25) on closing pdfwrite device.
    # https://bugs.ghostscript.com/show_bug.cgi?id=697684
    # Work around this by only adding keys that have a nontrivial value
    docinfo_keys = ('/Title', '/Author', '/Subject', '/Creator', '/Keywords')
    docinfo_line_template = '  {key} <{value}>'

    def docinfo_gen():
        yield from _get_pdfmark_dates(pdfmark)
        for key in docinfo_keys:
            if key in pdfmark and pdfmark[key].strip() != '':
                line = docinfo_line_template.format(
                    key=key, value=encode_text_string(pdfmark[key]))
                yield line
    docinfo = '\n'.join(docinfo_gen())

    t = Template(pdfa_def_template)
    result = t.substitute(icc_profile=icc_profile,
                          icc_identifier=icc_identifier,
                          docinfo=docinfo)
    return result


def generate_pdfa_ps(target_filename, pdfmark, icc='sRGB'):
    if icc == 'sRGB':
        icc_profile = SRGB_ICC_PROFILE
    else:
        raise NotImplementedError("Only supporting sRGB")

    ps = _get_pdfa_def(icc_profile, icc, pdfmark)

    # We should have encoded everything to pure ASCII by this point, and
    # to be safe, only allow ASCII in PostScript
    with open(target_filename, 'w', encoding='ascii') as f:
        f.write(ps)


def file_claims_pdfa(filename):
    """Determines if the file claims to be PDF/A compliant

    Checking if a file is a truly compliant PDF/A is a massive undertaking
    that no open source tool does properly.  Some commercial tools are
    generally reliable (Acrobat).

    This checks if the XMP metadata contains a PDF/A marker.
    """
    pdf = pypdf.PdfFileReader(filename)
    try:
        # Monkeypatch PyPDF2 to use defusedxml as its XML parser, for safety
        with patch('xml.dom.minidom.parseString', new=defused_parseString):
            xmp = pdf.getXmpMetadata()
    except ExpatError:
        return {'pass': False, 'output': 'pdf',
                'conformance': 'Invalid XML metadata'}

    try:
        pdfa_nodes = xmp.getNodesInNamespace(
            aboutUri='',
            namespace='http://www.aiim.org/pdfa/ns/id/')
    except AttributeError:
        return {'pass': False, 'output': 'pdf',
                'conformance': 'No XMP metadata'}

    pdfa_dict = {attr.localName: attr.value for attr in pdfa_nodes}
    if not pdfa_dict:
        return {'pass': False, 'output': 'pdf',
                'conformance': 'No XMP metadata'}

    part_conformance = pdfa_dict['part'] + pdfa_dict['conformance']
    valid_part_conforms = {'1A', '1B', '2A', '2B', '2U', '3A', '3B', '3U'}

    conformance = 'PDF/A-{}'.format(
        part_conformance)

    if part_conformance in valid_part_conforms:
        pdfa_dict['pass'] = True
        pdfa_dict['output'] = 'pdfa'
    pdfa_dict['conformance'] = conformance

    return pdfa_dict

