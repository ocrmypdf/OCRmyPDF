# SPDX-FileCopyrightText: 2022 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

"""Command line interface customization and validation."""

from __future__ import annotations

import argparse
from argparse import ArgumentParser
from collections.abc import Callable, Mapping
from typing import Any, TypeVar

from ocrmypdf._defaults import DEFAULT_ROTATE_PAGES_THRESHOLD
from ocrmypdf._defaults import PROGRAM_NAME as _PROGRAM_NAME
from ocrmypdf._options import OcrOptions, ProcessingMode, TaggedPdfMode
from ocrmypdf._plugin_manager import OcrmypdfPluginManager
from ocrmypdf._version import __version__ as _VERSION

T = TypeVar('T', int, float)


def numeric(basetype: Callable[[Any], T], min_: T | None = None, max_: T | None = None):
    """Validator for numeric command line parameters.

    Stipulates that the value must be of type basetype (typically int or float), and
    optionally, within the range [min_, max_].
    """
    min_ = basetype(min_) if min_ is not None else None
    max_ = basetype(max_) if max_ is not None else None

    def _numeric(s: str) -> T:
        value = basetype(s)
        if (min_ is not None and value < min_) or (max_ is not None and value > max_):
            raise argparse.ArgumentTypeError(
                f"{s!r} not in valid range {(min_, max_)!r}"
            )
        return value

    _numeric.__name__ = basetype.__name__
    return _numeric


def str_to_int(mapping: Mapping[str, int]):
    """Accept text on command line and convert to integer."""

    def _str_to_int(s: str) -> int:
        try:
            return mapping[s]
        except KeyError:
            raise argparse.ArgumentTypeError(
                f"{s!r} must be one of: {', '.join(mapping.keys())}"
            ) from None

    return _str_to_int


class LanguageSetAction(argparse.Action):
    """Manages a list of languages."""

    def __init__(self, option_strings, dest, default=None, **kwargs):
        """Initialize the action."""
        if default is None:
            default = list()
        super().__init__(option_strings, dest, default=default, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        """Add a language to the set."""
        dest = getattr(namespace, self.dest)
        if isinstance(values, str) and '+' in values:
            [dest.append(lang) for lang in values.split('+')]
        else:
            dest.append(values)


def get_parser():
    """Get the main CLI parser."""
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
        "Existing files will be overwritten. If same as input file, the "
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
        help="When the input file is an image, not a PDF, use this DPI instead "
        "of the DPI claimed by the input file. If the input does not claim a "
        "sensible DPI, this option will be required.",
    )
    parser.add_argument(
        '--output-type',
        choices=['auto', 'pdfa', 'pdf', 'pdfa-1', 'pdfa-2', 'pdfa-3', 'none'],
        default='auto',
        help="Choose output type. 'auto' (default) produces best-effort PDF/A "
        "without requiring Ghostscript - uses verapdf validation when available, "
        "otherwise passes through as PDF/A if safe (input already PDF/A or "
        "force-ocr was used), or falls back to regular PDF. 'pdfa' creates a "
        "PDF/A-2b compliant file for long term archiving (requires Ghostscript "
        "as fallback). 'pdf' minimizes changes to the input file. 'pdfa-1' "
        "creates a PDF/A-1b file. 'pdfa-2' is equivalent to 'pdfa'. 'pdfa-3' "
        "creates a PDF/A-3b file. 'none' will produce no output, which may be "
        "helpful if only the --sidecar is desired.",
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
        "If FILE is omitted, the sidecar file be named {output_file}.txt; the next "
        "argument must NOT be the name of the input PDF. "
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
        '--use-threads', action='store_true', default=True, help=argparse.SUPPRESS
    )
    jobcontrol.add_argument(
        '--no-use-threads',
        action='store_false',
        dest='use_threads',
        help=argparse.SUPPRESS,
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

    ocrsettings = parser.add_argument_group("OCR options", "Control how OCR is applied")
    ocrsettings.add_argument(
        '-m',
        '--mode',
        choices=[mode.value for mode in ProcessingMode],
        default=ProcessingMode.default.value,
        help="Processing mode for pages with existing text. "
        "'default' errors if text is found. "
        "'force' rasterizes all content and runs OCR (same as --force-ocr). "
        "'skip' skips pages with existing text (same as --skip-text). "
        "'redo' re-OCRs pages, replacing old invisible text (same as --redo-ocr).",
    )
    # Legacy flags for backward compatibility - these set the mode internally
    ocrsettings.add_argument(
        '-f',
        '--force-ocr',
        action='store_true',
        help="Rasterize any text or vector objects on each page, apply OCR, and "
        "save the rastered output (this rewrites the PDF). "
        "Equivalent to --mode force.",
    )
    ocrsettings.add_argument(
        '-s',
        '--skip-text',
        action='store_true',
        help="Skip OCR on any pages that already contain text, but include the "
        "page in final output; useful for PDFs that contain a mix of "
        "images, text pages, and/or previously OCRed pages. "
        "Equivalent to --mode skip.",
    )
    ocrsettings.add_argument(
        '--redo-ocr',
        action='store_true',
        help="Attempt to detect and remove the hidden OCR layer from files that "
        "were previously OCRed with OCRmyPDF or another program. Apply OCR "
        "to text found in raster images. Existing visible text objects will "
        "not be changed. If there is no existing OCR, OCR will be added. "
        "Equivalent to --mode redo.",
    )
    ocrsettings.add_argument(
        '--skip-big',
        type=numeric(float, 0, 5000),
        metavar='MPixels',
        help="Skip OCR on pages larger than the specified amount of megapixels, "
        "but include skipped pages in final output",
    )
    ocrsettings.add_argument(
        '--invalidate-digital-signatures',
        action='store_true',
        help="Normally, OCRmyPDF will refuse to OCR a PDF that has a digital "
        "signature. This option allows OCR to proceed, but the digital signature "
        "will be invalidated.",
    )
    ocrsettings.add_argument(
        '--tagged-pdf-mode',
        choices=[mode.value for mode in TaggedPdfMode],
        default=TaggedPdfMode.default.value,
        help="Control behavior when a Tagged PDF is encountered. "
        "'default' errors if --mode is default, otherwise warns. "
        "'ignore' always warns but continues processing.",
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
        help="Set maximum number of megapixels to unpack before treating an image as a "
        "decompression bomb",
        default=250.0,
    )
    advanced.add_argument(
        '--pdf-renderer',
        choices=['auto', 'hocr', 'sandwich', 'hocrdebug', 'fpdf2'],
        default='auto',
        help="Choose OCR PDF renderer. 'auto' (recommended) uses fpdf2, which "
        "provides full international language support including RTL scripts, "
        "proper text positioning, and invisible text that becomes visible when "
        "selected. 'sandwich' renders text as a background layer. Legacy 'hocr' "
        "and 'hocrdebug' options are deprecated and will use fpdf2.",
    )
    advanced.add_argument(
        '--ocr-engine',
        choices=['auto', 'tesseract', 'none'],
        default='auto',
        help="OCR engine to use. 'auto' (default) selects the best available engine. "
        "'tesseract' uses Tesseract OCR. "
        "'none' skips OCR entirely, useful for PDF/A conversion or image processing "
        "without text recognition.",
    )
    advanced.add_argument(
        '--rasterizer',
        choices=['auto', 'ghostscript', 'pypdfium'],
        default='auto',
        help="Choose PDF page rasterizer. 'auto' prefers pypdfium when available, "
        "falling back to Ghostscript. 'pypdfium' is faster but requires the "
        "pypdfium2 package. 'ghostscript' uses the traditional Ghostscript rasterizer.",
    )
    advanced.add_argument(
        '--rotate-pages-threshold',
        default=DEFAULT_ROTATE_PAGES_THRESHOLD,
        type=numeric(float, 0, 1000),
        metavar='CONFIDENCE',
        help="Only rotate pages when confidence is above this value (arbitrary "
        "units reported by tesseract)",
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
        '--continue-on-soft-render-error',
        action='store_true',
        help="Continue processing pages after a recoverable PDF rendering error. "
        "A recoverable error is one that does not prevent the page from being "
        "rendered, but may result in visual differences compared to the input "
        "file. Missing fonts are a typical source of these errors.",
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


def namespace_to_options(ns) -> OcrOptions:
    """Convert argparse.Namespace to OcrOptions.

    This function encapsulates CLI-specific knowledge of how command line
    arguments map to our internal options model.
    """
    # Extract known fields
    known_fields = {}
    extra_attrs = {}

    # Legacy boolean flags that map to mode - handled by OcrOptions model validator
    legacy_mode_flags = {'force_ocr', 'skip_text', 'redo_ocr'}

    for key, value in vars(ns).items():
        if key in OcrOptions.model_fields:
            known_fields[key] = value
        elif key in legacy_mode_flags:
            # Pass legacy flags to OcrOptions for conversion to mode
            known_fields[key] = value
        else:
            extra_attrs[key] = value

    # Handle special cases for hOCR API
    if 'output_folder' in extra_attrs and 'output_file' not in known_fields:
        known_fields['output_file'] = '/dev/null'  # Placeholder

    # Handle case where input_file is missing (e.g., in _hocr_to_ocr_pdf)
    if 'work_folder' in extra_attrs and 'input_file' not in known_fields:
        known_fields['input_file'] = '/dev/null'  # Placeholder

    instance = OcrOptions(**known_fields)
    instance.extra_attrs = extra_attrs
    return instance


def get_options_and_plugins(
    args=None,
) -> tuple[OcrOptions, OcrmypdfPluginManager]:
    """Parse command line arguments and return OcrOptions and plugin manager.

    This is the main entry point for CLI argument processing. It handles
    plugin discovery, argument parsing, and conversion to our internal
    options model.

    Args:
        args: Command line arguments. If None, uses sys.argv.

    Returns:
        Tuple of (OcrOptions, PluginManager)
    """
    # Import here to avoid circular imports
    from ocrmypdf.api import setup_plugin_infrastructure

    # First pass: get plugins so we can register their options
    pre_options, _unused = plugins_only_parser.parse_known_args(args=args)

    # Set up plugin infrastructure with proper initialization
    plugin_manager = setup_plugin_infrastructure(plugins=pre_options.plugins)

    # Get parser and let plugins add their options
    parser = get_parser()
    plugin_manager.add_options(parser=parser)

    # Parse all arguments
    namespace = parser.parse_args(args=args)

    # Convert to OcrOptions
    options = namespace_to_options(namespace)

    return options, plugin_manager
