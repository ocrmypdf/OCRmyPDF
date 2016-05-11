#!/usr/bin/env python3
# © 2015 James R. Barlow: github.com/jbarlow83
#
# Generate a PDFA_def.ps file for Ghostscript >= 9.14

from __future__ import print_function, absolute_import, division
from string import Template
import codecs
import pkg_resources

ICC_PROFILE_RELPATH = 'data/sRGB.icc'

SRGB_ICC_PROFILE = pkg_resources.resource_filename(
    'ocrmypdf', ICC_PROFILE_RELPATH)


# This is a template written in PostScript which is needed to create PDF/A
# files, from the Ghostscript documentation. Lines beginning with % are
# comments. Python substitution variables have a '$' prefix.
pdfa_def_template = u"""%!
% This is a sample prefix file for creating a PDF/A document.
% Feel free to modify entries marked with "Customize".
% This assumes an ICC profile to reside in the file (ISO Coated sb.icc),
% unless the user modifies the corresponding line below.

% Define entries in the document Info dictionary :
/ICCProfile ($icc_profile)
def

[ /Title <$title>
  /Author <$author>
  /Subject <$subject>
  /Keywords <$keywords>
  /Creator <$creator>
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
    be UTF-16 (big endian) with byte order marks.  A non-hexademical
    representation is doable but this is preferable since it allows the output
    Postscript file to be completely ASCII and no escaping of Postscript
    characters is necessary.
    '''
    if s == '':
        return ''
    utf16_bytes = s.encode('utf-16be')
    ascii_hex_bytes = codecs.encode(b'\xfe\xff' + utf16_bytes, 'hex')
    ascii_hex_str = ascii_hex_bytes.decode('ascii').lower()
    return ascii_hex_str


def _get_pdfa_def(icc_profile, icc_identifier, pdfmark):
    pdfmark_utf16 = {k: encode_text_string(v) for k, v in pdfmark.items()}

    t = Template(pdfa_def_template)
    result = t.substitute(icc_profile=icc_profile,
                          icc_identifier=icc_identifier,
                          title=pdfmark_utf16.get('title', ''),
                          author=pdfmark_utf16.get('author', ''),
                          subject=pdfmark_utf16.get('subject', ''),
                          creator=pdfmark_utf16.get('creator', ''),
                          keywords=pdfmark_utf16.get('keywords', ''))
    return result


def generate_pdfa_def(target_filename, pdfmark, icc='sRGB'):
    if icc == 'sRGB':
        icc_profile = SRGB_ICC_PROFILE
    else:
        raise NotImplementedError("Only supporting sRGB")

    ps = _get_pdfa_def(icc_profile, icc, pdfmark)

    # Since PostScript might not handle UTF-8 (it's hard to get a clear
    # answer), insist on ascii
    with open(target_filename, 'w', encoding='ascii') as f:
        f.write(ps)
