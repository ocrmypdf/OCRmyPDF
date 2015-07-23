#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# © 2015: jbarlow83 (https://github.com/jbarlow83)
#
# Generate a PDFA_def.ps file for Ghostscript >= 9.14

from __future__ import print_function, absolute_import, division
from string import Template


pdfa_def_template = u"""%!
% This is a sample prefix file for creating a PDF/A document.
% Feel free to modify entries marked with "Customize".
% This assumes an ICC profile to reside in the file (ISO Coated sb.icc),
% unless the user modifies the corresponding line below.

% Define entries in the document Info dictionary :
/ICCProfile ($icc_profile)
def

[ /Title ($pdf_title)
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


def _get_pdfa_def(icc_profile, pdf_title, icc_identifier):
    t = Template(pdfa_def_template)
    result = t.substitute(icc_profile=icc_profile,
                          pdf_title=pdf_title,
                          icc_identifier=icc_identifier)
    return result


def generate_pdfa_def(target_filename, pdf_title='', icc='sRGB'):
    # How does find this directory on other platforms?
    if icc == 'sRGB':
        icc_profile = '/usr/local/share/ghostscript/iccprofiles/srgb.icc'
    else:
        raise NotImplementedError("Only supporting sRGB")

    ps = _get_pdfa_def(icc_profile, pdf_title, icc)

    # Since PostScript might not handle UTF-8 (it's hard to get a clear
    # answer), insist on ascii
    with open(target_filename, 'w', encoding='ascii') as f:
        f.write(ps)
