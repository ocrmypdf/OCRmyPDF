#!/usr/local/bin/python2
##############################################################################
# Copyright (c) 2013-14: fritz-hh from Github (https://github.com/fritz-hh)
##############################################################################

import argparse
from argparse import RawTextHelpFormatter

if __name__ == '__main__':

    parser = argparse.ArgumentParser(prog="ocrmypdf", description="OCRmyPDF adds an OCR text layer to scanned PDF files, allowing them to be searched", formatter_class=RawTextHelpFormatter)
    parser.add_argument('-v', '--verbove', action='count', help="Increase the verbosity (this option can be used more than once) (e.g. -vvv)")
    parser.add_argument('-k', '--keep-tmp', action='store_true', help="Do not delete the temporary files")
    parser.add_argument('-g', '--debug', action='store_true', 
        help="Activate debug mode:\n" + 
        "- Generates a PDF file containing each page twice (once with the image, once without the image\n" +
        "       but with the OCRed text as well as the detected bounding boxes)\n" +
        "- Set the verbosity to the highest possible\n" +
        "- Do not delete the temporary files")
    parser.add_argument('-d', '--deskew', action='store_true', help="Deskew each page before performing OCR")
    parser.add_argument('-c', '--clean', action='store_true', help="Clean each page before performing OCR")
    parser.add_argument('-i', action='store_true', help="Incorporate the cleaned image in the final PDF file (by default the original image, or the deskewed image if the -d option is set)")
    parser.add_argument('-o', '--oversample', metavar='dpi', type=int, 
        help="If the resolution of an image is lower than dpi value provided as argument, provide the OCR engine with\n" +
        "an oversampled image having the latter dpi value. This can improve the OCR results but can lead to a larger output PDF file.\n" +
        "(default: no oversampling performed)")
    group_sf = parser.add_mutually_exclusive_group()
    group_sf.add_argument('-f', action='store_true', 
        help="Force to OCR the whole document, even if some page already contain font data.\n" +
        "(which should not be the case for PDF files built from scnanned images)\n" +
        "Any text data will be rendered to raster format and then fed through OCR.")
    group_sf.add_argument('-s', action='store_true', help="If pages contain font data, do not OCR that page, but include the page (as is) in the final output.")
    parser.add_argument('-l', '--language', metavar='lan', 
        help="Language(s) of the PDF file. The language should be set correctly in order to get good OCR results.\n" +
        "Any language supported by tesseract is supported (Tesseract uses 3-character ISO 639-2 language codes)\n" +
        "Multiple languages may be specified, separated by '+' characters.\n" +
        "(The default language is defined in the config file)")
    parser.add_argument('-C', '--tess-config', metavar='file', 
        help="Pass an additional configuration file to the tesseract OCR engine.\n" +
        "(this option can be used more than once)\n" +
        "Note 1: The configuration file must be available in the \"tessdata/configs\" folder of your tesseract installation")
    parser.add_argument('inputfile', help="PDF file to be OCRed")
    parser.add_argument('outputfile', help="The PDF/A file that will be generated")

    args = parser.parse_args()
