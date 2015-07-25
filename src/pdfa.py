#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# © 2015: jbarlow83 (https://github.com/jbarlow83)
#
# Generate a PDFA_def.ps file for Ghostscript >= 9.14

from __future__ import print_function, absolute_import, division
from string import Template
from subprocess import Popen, PIPE
import os


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

[ /Title ($pdf_title)
  /Author ($pdf_author)
  /Subject ($pdf_subject)
  /Keywords ($pdf_keywords)
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


def _get_pdfa_def(icc_profile, icc_identifier, pdfmark):
    t = Template(pdfa_def_template)
    result = t.substitute(icc_profile=icc_profile,
                          icc_identifier=icc_identifier,
                          pdf_title=pdfmark.get('title', ''),
                          pdf_author=pdfmark.get('author', ''),
                          pdf_subject=pdfmark.get('subject', ''),
                          pdf_keywords=pdfmark.get('keywords', ''))
    return result


def _get_postscript_icc_path():
    "Parse Ghostscript's help message to find where iccprofiles are stored"

    p_gs = Popen(['gs', '--help'], close_fds=True, universal_newlines=True,
                 stdout=PIPE, stderr=PIPE)
    out, _ = p_gs.communicate()
    lines = out.splitlines()

    def search_paths(lines):
        seeking = True
        for line in lines:
            if seeking:
                if line.startswith('Search path'):
                    seeking = False
                    continue
            else:
                if line.strip().startswith('/'):
                    yield from (
                        path.strip() for path in line.split(':')
                        if path.strip() != '')
    for root in search_paths(lines):
        path = os.path.realpath(os.path.join(root, '../iccprofiles'))
        if os.path.exists(path):
            return path


def generate_pdfa_def(target_filename, pdfmark, icc='sRGB'):
    if icc == 'sRGB':
        icc_profile = os.path.join(_get_postscript_icc_path(), 'srgb.icc')
    else:
        raise NotImplementedError("Only supporting sRGB")

    ps = _get_pdfa_def(icc_profile, icc, pdfmark)

    # Since PostScript might not handle UTF-8 (it's hard to get a clear
    # answer), insist on ascii
    with open(target_filename, 'w', encoding='ascii') as f:
        f.write(ps)
