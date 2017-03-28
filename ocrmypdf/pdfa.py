#!/usr/bin/env python3
# © 2015 James R. Barlow: github.com/jbarlow83
#
# Generate a PDFA_def.ps file for Ghostscript >= 9.14

from string import Template
import codecs
import pkg_resources
import PyPDF2 as pypdf

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
    ascii_hex_bytes = codecs.encode(b'\xfe\xff' + utf16_bytes, 'hex')
    ascii_hex_str = ascii_hex_bytes.decode('ascii').lower()
    return ascii_hex_str


def _get_pdfa_def(icc_profile, icc_identifier, pdfmark):
    # Ghostscript <= 9.21 has a bug where null entries in DOCINFO might produce
    # ERROR: VMerror (-25) on closing pdfwrite device.
    # https://bugs.ghostscript.com/show_bug.cgi?id=697684
    # Work around this by only adding keys that have a nontrivial value
    docinfo_keys = ('/Title', '/Author', '/Subject', '/Creator', '/Keywords')
    docinfo_line_template = '  {key} <{value}>'

    def docinfo_gen():
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
    xmp = pdf.getXmpMetadata()

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

