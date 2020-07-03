# © 2015-19 James R. Barlow: github.com/jbarlow83
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

import argparse

from ocrmypdf._version import PROGRAM_NAME as _PROGRAM_NAME
from ocrmypdf._version import __version__ as _VERSION


def numeric(basetype, min_=None, max_=None):
    """Validator for numeric params"""
    min_ = basetype(min_) if min_ is not None else None
    max_ = basetype(max_) if max_ is not None else None

    def _numeric(string):
        value = basetype(string)
        if (min_ is not None and value < min_) or (max_ is not None and value > max_):
            msg = "%r not in valid range %r" % (string, (min_, max_))
            raise argparse.ArgumentTypeError(msg)
        return value

    _numeric.__name__ = basetype.__name__
    return _numeric


class ArgumentParser(argparse.ArgumentParser):
    """Override parser's default behavior of calling sys.exit()

    https://stackoverflow.com/questions/5943249/python-argparse-and-controlling-overriding-the-exit-status-code
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._api_mode = False

    def error(self, message):
        if not self._api_mode:
            super().error(message)
            return
        raise ValueError(message)


class LanguageSetAction(argparse.Action):
    def __init__(self, option_strings, dest, default=None, **kwargs):
        if default is None:
            default = set()
        super().__init__(option_strings, dest, default=default, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        dest = getattr(namespace, self.dest)
        if '+' in values:
            dest.update(lang for lang in values.split('+'))
        else:
            dest.add(values)


def get_parser():
    parser = ArgumentParser(
        prog=_PROGRAM_NAME,
        allow_abbrev=True,
        fromfile_prefix_chars='@',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="""\
Generates a searchable PDF or PDF/A from a regular PDF.

OCRmyPDF rasterizes each page of the input PDF, optionally corrects page
rotation and performs image processing, runs the Tesseract OCR engine on the
image, and then creates a PDF from the OCR information.
""",
        epilog="""\
OCRmyPDF attempts to keep the output file at about the same size.  If a file
contains losslessly compressed images, and images in the output file will be
losslessly compressed as well.

PDF is a page description file that attempts to preserve a layout exactly.
A PDF can contain vector objects (such as text or lines) and raster objects
(images).  A page might have multiple images.  OCRmyPDF is prepared to deal
with the wide variety of PDFs that exist in the wild.

When a PDF page contains text, OCRmyPDF assumes that the page has already
been OCRed or is a "born digital" page that should not be OCRed.  The default
behavior is to exit in this case without producing a file.  You can use the
option --skip-text to ignore pages with text, or --force-ocr to rasterize
all objects on the page and produce an image-only PDF as output.

    ocrmypdf --skip-text file_with_some_text_pages.pdf output.pdf

    ocrmypdf --force-ocr word_document.pdf output.pdf

If you are concerned about long-term archiving of PDFs, use the default option
--output-type pdfa which converts the PDF to a standardized PDF/A-2b.  This
removes some features from the PDF such as Javascript or forms. If you want to
minimize the number of changes made to your PDF, use --output-type pdf.

If OCRmyPDF is given an image file as input, it will attempt to convert the
image to a PDF before processing.  For more control over the conversion of
images to PDF, use the Python package img2pdf or other image to PDF software.

For example, this command uses img2pdf to convert all .png files beginning
with the 'page' prefix to a PDF, fitting each image on A4-sized paper, and
sending the result to OCRmyPDF through a pipe.

    img2pdf --pagesize A4 page*.png | ocrmypdf - myfile.pdf

Online documentation is located at:
    https://ocrmypdf.readthedocs.io/en/latest/introduction.html

""",
    )

    parser.add_argument(
        'input_file',
        metavar="input_pdf_or_image",
        help="PDF file containing the images to be OCRed (or '-' to read from "
        "standard input)",
    )
    parser.add_argument(
        'output_file',
        metavar="output_pdf",
        help="Output searchable PDF file (or '-' to write to standard output). "
        "Existing files will be ovewritten. If same as input file, the "
        "input file will be updated only if processing is successful.",
    )
    parser.add_argument(
        '-l',
        '--language',
        dest='languages',
        action=LanguageSetAction,
        help="Language(s) of the file to be OCRed (see tesseract --list-langs for "
        "all language packs installed in your system). Use -l eng+deu for "
        "multiple languages.",
    )
    parser.add_argument(
        '--image-dpi',
        metavar='DPI',
        type=int,
        help="For input image instead of PDF, use this DPI instead of file's.",
    )
    parser.add_argument(
        '--output-type',
        choices=['pdfa', 'pdf', 'pdfa-1', 'pdfa-2', 'pdfa-3'],
        default='pdfa',
        help="Choose output type. 'pdfa' creates a PDF/A-2b compliant file for "
        "long term archiving (default, recommended) but may not suitable "
        "for users who want their file altered as little as possible. 'pdfa' "
        "also has problems with full Unicode text. 'pdf' attempts to "
        "preserve file contents as much as possible. 'pdf-a1' creates a "
        "PDF/A1-b file. 'pdf-a2' is equivalent to 'pdfa'. 'pdf-a3' creates a "
        "PDF/A3-b file.",
    )

    # Use null string '\0' as sentinel to indicate the user supplied no argument,
    # since that is the only invalid character for filepaths on all platforms
    # bool('\0') is True in Python
    parser.add_argument(
        '--sidecar',
        nargs='?',
        const='\0',
        default=None,
        metavar='FILE',
        help="Generate sidecar text files that contain the same text recognized "
        "by Tesseract. This may be useful for building a OCR text database. "
        "If FILE is omitted, the sidecar file be named {output_file}.txt "
        "If FILE is set to '-', the sidecar is written to stdout (a "
        "convenient way to preview OCR quality). The output file and sidecar "
        "may not both use stdout at the same time.",
    )

    parser.add_argument(
        '--version',
        action='version',
        version=_VERSION,
        help="Print program version and exit",
    )

    jobcontrol = parser.add_argument_group("Job control options")
    jobcontrol.add_argument(
        '-j',
        '--jobs',
        metavar='N',
        type=numeric(int, 0, 256),
        help="Use up to N CPU cores simultaneously (default: use all).",
    )
    jobcontrol.add_argument(
        '-q', '--quiet', action='store_true', help="Suppress INFO messages"
    )
    jobcontrol.add_argument(
        '-v',
        '--verbose',
        type=numeric(int, 0, 2),
        default=0,
        const=1,
        nargs='?',
        help="Print more verbose messages for each additional verbose level. Use "
        "`-v 1` typically for much more detailed logging. Higher numbers "
        "are probably only useful in debugging.",
    )
    jobcontrol.add_argument(
        '--no-progress-bar',
        action='store_false',
        dest='progress_bar',
        help=argparse.SUPPRESS,
    )
    jobcontrol.add_argument(
        '--use-threads', action='store_true', help=argparse.SUPPRESS
    )

    metadata = parser.add_argument_group(
        "Metadata options",
        "Set output PDF/A metadata (default: copy input document's metadata)",
    )
    metadata.add_argument(
        '--title', type=str, help="Set document title (place multiple words in quotes)"
    )
    metadata.add_argument('--author', type=str, help="Set document author")
    metadata.add_argument(
        '--subject', type=str, help="Set document subject description"
    )
    metadata.add_argument('--keywords', type=str, help="Set document keywords")

    preprocessing = parser.add_argument_group(
        "Image preprocessing options",
        "Options to improve the quality of the final PDF and OCR",
    )
    preprocessing.add_argument(
        '-r',
        '--rotate-pages',
        action='store_true',
        help="Automatically rotate pages based on detected text orientation",
    )
    preprocessing.add_argument(
        '--remove-background',
        action='store_true',
        help="Attempt to remove background from gray or color pages, setting it "
        "to white ",
    )
    preprocessing.add_argument(
        '-d',
        '--deskew',
        action='store_true',
        help="Deskew each page before performing OCR",
    )
    preprocessing.add_argument(
        '-c',
        '--clean',
        action='store_true',
        help="Clean pages from scanning artifacts before performing OCR, and send "
        "the cleaned page to OCR, but do not include the cleaned page in "
        "the output",
    )
    preprocessing.add_argument(
        '-i',
        '--clean-final',
        action='store_true',
        help="Clean page as above, and incorporate the cleaned image in the final "
        "PDF.  Might remove desired content.",
    )
    preprocessing.add_argument(
        '--unpaper-args',
        type=str,
        default=None,
        help="A quoted string of arguments to pass to unpaper. Requires --clean. "
        "Example: --unpaper-args '--layout double'.",
    )
    preprocessing.add_argument(
        '--oversample',
        metavar='DPI',
        type=numeric(int, 0, 5000),
        default=0,
        help="Oversample images to at least the specified DPI, to improve OCR "
        "results slightly",
    )
    preprocessing.add_argument(
        '--remove-vectors',
        action='store_true',
        help="EXPERIMENTAL. Mask out any vector objects in the PDF so that they "
        "will not be included in OCR. This can eliminate false characters.",
    )
    preprocessing.add_argument(
        '--threshold',
        action='store_true',
        help=(
            "EXPERIMENTAL. Threshold image to 1bpp before sending it to Tesseract "
            "for OCR. Can improve OCR quality compared to Tesseract's thresholder."
        ),
    )

    ocrsettings = parser.add_argument_group("OCR options", "Control how OCR is applied")
    ocrsettings.add_argument(
        '-f',
        '--force-ocr',
        action='store_true',
        help="Rasterize any text or vector objects on each page, apply OCR, and "
        "save the rastered output (this rewrites the PDF)",
    )
    ocrsettings.add_argument(
        '-s',
        '--skip-text',
        action='store_true',
        help="Skip OCR on any pages that already contain text, but include the "
        "page in final output; useful for PDFs that contain a mix of "
        "images, text pages, and/or previously OCRed pages",
    )
    ocrsettings.add_argument(
        '--redo-ocr',
        action='store_true',
        help="Attempt to detect and remove the hidden OCR layer from files that "
        "were previously OCRed with OCRmyPDF or another program. Apply OCR "
        "to text found in raster images. Existing visible text objects will "
        "not be changed. If there is no existing OCR, OCR will be added.",
    )
    ocrsettings.add_argument(
        '--skip-big',
        type=numeric(float, 0, 5000),
        metavar='MPixels',
        help="Skip OCR on pages larger than the specified amount of megapixels, "
        "but include skipped pages in final output",
    )

    optimizing = parser.add_argument_group(
        "Optimization options", "Control how the PDF is optimized after OCR"
    )
    optimizing.add_argument(
        '-O',
        '--optimize',
        type=int,
        choices=range(0, 4),
        default=1,
        help=(
            "Control how PDF is optimized after processing:"
            "0 - do not optimize; "
            "1 - do safe, lossless optimizations (default); "
            "2 - do some lossy optimizations; "
            "3 - do aggressive lossy optimizations (including lossy JBIG2)"
        ),
    )
    optimizing.add_argument(
        '--jpeg-quality',
        type=numeric(int, 0, 100),
        default=0,
        metavar='Q',
        help=(
            "Adjust JPEG quality level for JPEG optimization. "
            "100 is best quality and largest output size; "
            "1 is lowest quality and smallest output; "
            "0 uses the default."
        ),
    )
    optimizing.add_argument(
        '--jpg-quality',
        type=numeric(int, 0, 100),
        default=0,
        metavar='Q',
        dest='jpeg_quality',
        help=argparse.SUPPRESS,  # Alias for --jpeg-quality
    )
    optimizing.add_argument(
        '--png-quality',
        type=numeric(int, 0, 100),
        default=0,
        metavar='Q',
        help=(
            "Adjust PNG quality level to use when quantizing PNGs. "
            "Values have same meaning as with --jpeg-quality"
        ),
    )
    optimizing.add_argument(
        '--jbig2-lossy',
        action='store_true',
        help=(
            "Enable JBIG2 lossy mode (better compression, not suitable for some "
            "use cases - see documentation)."
        ),
    )
    optimizing.add_argument(
        '--jbig2-page-group-size',
        type=numeric(int, 1, 10000),
        default=0,
        metavar='N',
        # Adjust number of pages to consider at once for JBIG2 compression
        help=argparse.SUPPRESS,
    )

    advanced = parser.add_argument_group(
        "Advanced", "Advanced options to control OCRmyPDF"
    )
    advanced.add_argument(
        '--pages',
        type=str,
        help=(
            "Limit OCR to the specified pages (ranges or comma separated), "
            "skipping others"
        ),
    )
    advanced.add_argument(
        '--max-image-mpixels',
        action='store',
        type=numeric(float, 0),
        metavar='MPixels',
        help="Set maximum number of pixels to unpack before treating an image as a "
        "decompression bomb",
        default=128.0,
    )
    advanced.add_argument(
        '--pdf-renderer',
        choices=['auto', 'hocr', 'sandwich'],
        default='auto',
        help="Choose OCR PDF renderer - the default option is to let OCRmyPDF "
        "choose.  See documentation for discussion.",
    )
    advanced.add_argument(
        '--rotate-pages-threshold',
        default=14.0,
        type=numeric(float, 0, 1000),
        metavar='CONFIDENCE',
        help="Only rotate pages when confidence is above this value (arbitrary "
        "units reported by tesseract)",
    )
    advanced.add_argument(
        '--pdfa-image-compression',
        choices=['auto', 'jpeg', 'lossless'],
        default='auto',
        help="Specify how to compress images in the output PDF/A. 'auto' lets "
        "OCRmyPDF decide.  'jpeg' changes all grayscale and color images to "
        "JPEG compression.  'lossless' uses PNG-style lossless compression "
        "for all images.  Monochrome images are always compressed using a "
        "lossless codec.  Compression settings "
        "are applied to all pages, including those for which OCR was "
        "skipped.  Not supported for --output-type=pdf ; that setting "
        "preserves the original compression of all images.",
    )
    advanced.add_argument(
        '--fast-web-view',
        type=numeric(float, 0),
        default=1.0,
        metavar="MEGABYTES",
        help="If the size of file is more than this threshold (in MB), then "
        "linearize the PDF for fast web viewing. This allows the PDF to be "
        "displayed before it is fully downloaded in web browsers, but increases "
        "the space required slightly. By default we skip this for small files "
        "which do not benefit. If the threshold is 0 it will be apply to all files. "
        "Set the threshold very high to disable.",
    )
    advanced.add_argument(
        '--plugin',
        dest='plugins',
        action='append',
        default=[],
        help="Name of plugin to import. Argument may be issued multiple times to "
        "import multiple plugins. Plugins may be specified as module names in "
        "Python syntax, provided they are installed in the same Python (virtual) "
        "environment as ocrmypdf; or you may give the path to the Python file that "
        "contains the plugin. Plugins must conform to the specification in the "
        "OCRmyPDF documentation.",
    )

    debugging = parser.add_argument_group(
        "Debugging", "Arguments to help with troubleshooting and debugging"
    )
    debugging.add_argument(
        '-k',
        '--keep-temporary-files',
        action='store_true',
        help="Keep temporary files (helpful for debugging)",
    )
    return parser


plugins_only_parser = ArgumentParser(
    prog=_PROGRAM_NAME, fromfile_prefix_chars='@', add_help=False, allow_abbrev=False
)
plugins_only_parser.add_argument(
    '--plugin',
    dest='plugins',
    action='append',
    default=[],
    help="Name of plugin to import.",
)
