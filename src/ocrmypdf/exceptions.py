# SPDX-FileCopyrightText: 2022 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

"""OCRmyPDF's exceptions."""

from __future__ import annotations

from enum import IntEnum
from textwrap import dedent


class ExitCode(IntEnum):
    """OCRmyPDF's exit codes."""

    # pylint: disable=invalid-name
    ok = 0
    bad_args = 1
    input_file = 2
    missing_dependency = 3
    invalid_output_pdf = 4
    file_access_error = 5
    already_done_ocr = 6
    child_process_error = 7
    encrypted_pdf = 8
    invalid_config = 9
    pdfa_conversion_failed = 10
    other_error = 15
    ctrl_c = 130


class ExitCodeException(Exception):
    """An exception which should return an exit code with sys.exit()."""

    exit_code = ExitCode.other_error
    message = ""

    def __str__(self):
        """Return a string representation of the exception."""
        super_msg = super().__str__()  # Don't do str(super())
        if self.message:
            return self.message.format(super_msg)
        return super_msg


class BadArgsError(ExitCodeException):
    """Invalid arguments on the command line or API."""

    exit_code = ExitCode.bad_args


class MissingDependencyError(ExitCodeException):
    """A third-party dependency is missing."""

    exit_code = ExitCode.missing_dependency


class UnsupportedImageFormatError(ExitCodeException):
    """The image format is not supported."""

    exit_code = ExitCode.input_file


class DpiError(ExitCodeException):
    """Missing information about input image DPI."""

    exit_code = ExitCode.input_file


class OutputFileAccessError(ExitCodeException):
    """Cannot access the intended output file path."""

    exit_code = ExitCode.file_access_error


class PriorOcrFoundError(ExitCodeException):
    """This file already has OCR."""

    exit_code = ExitCode.already_done_ocr


class InputFileError(ExitCodeException):
    """Something is wrong with the input file."""

    exit_code = ExitCode.input_file


class SubprocessOutputError(ExitCodeException):
    """A subprocess returned an unexpected error."""

    exit_code = ExitCode.child_process_error


class EncryptedPdfError(ExitCodeException):
    """Input PDF is encrypted."""

    exit_code = ExitCode.encrypted_pdf
    message = dedent(
        """\
        Input PDF is encrypted. The encryption must be removed to
        perform OCR.

        For information about this PDF's security use
            qpdf --show-encryption infilename

        You can remove the encryption using
            qpdf --decrypt [--password=[password]] infilename
        """
    )


class TesseractConfigError(ExitCodeException):
    """Tesseract config can't be parsed."""

    exit_code = ExitCode.invalid_config
    message = "Error occurred while parsing a Tesseract configuration file"


class DigitalSignatureError(InputFileError):
    """PDF has a digital signature."""

    message = dedent(
        """\
        Input PDF has a digital signature. OCR would alter the document,
        invalidating the signature.
        """
    )


class TaggedPDFError(InputFileError):
    """PDF is tagged."""

    message = dedent(
        """\
        This PDF is marked as a Tagged PDF. This often indicates
        that the PDF was generated from an office document and does
        not need OCR. Use --force-ocr, --skip-text or --redo-ocr to
        override this error.
        """
    )


class NonEmbeddedFontsError(InputFileError):
    """Input has non-embedded CID fonts that PDF/A conversion would corrupt.

    PDF/A requires all fonts to be embedded. Ghostscript substitutes and embeds
    a replacement for non-embedded CID (CJK) fonts, which corrupts the
    character-to-Unicode mapping and silently destroys an existing text layer
    (commonly an Adobe Acrobat CJK OCR layer). OCRmyPDF refuses to produce such
    output rather than damage the user's data
    (see https://github.com/ocrmypdf/OCRmyPDF/issues/1561).
    """

    def __init__(self, fonts: set[str]):
        """Build guidance naming the offending fonts."""
        super().__init__()
        font_list = ', '.join(sorted(fonts))
        self.message = dedent(
            f"""\
            The input PDF contains non-embedded CID (character ID) fonts: {font_list}.

            PDF/A requires all fonts to be embedded. Converting to PDF/A would
            make Ghostscript substitute and embed replacement fonts, which
            corrupts CID (e.g. CJK/Chinese-Japanese-Korean) text and silently
            destroys an existing text layer such as one produced by Adobe Acrobat.

            Use --output-type pdf to keep the existing text layer intact without
            PDF/A conversion, or --force-ocr to discard the existing layer and
            rebuild it with embedded fonts.
            """
        )


class ColorConversionNeededError(BadArgsError):
    """PDF needs color conversion to a standard color space.

    Ghostscript reported a DeviceN colorspace with an inappropriate alternate.
    The resulting PDF/A is liable to render incorrectly (often blank) in some
    viewers such as Adobe Reader, so the colorspace must be normalized to a
    common one. RGB, CMYK, and Gray are known to work; LeaveColorUnchanged
    performs no conversion and UseDeviceIndependentColor does not resolve the
    problem (see https://github.com/ocrmypdf/OCRmyPDF/issues/1187).
    """

    # Strategies that can normalize an unusual DeviceN colorspace into one that
    # PDF/A viewers render correctly.
    _effective_strategies = "RGB, CMYK, or Gray"

    def __init__(self, color_conversion_strategy: str = "LeaveColorUnchanged"):
        """Build guidance tailored to the conversion strategy that was used."""
        super().__init__()
        if color_conversion_strategy == "LeaveColorUnchanged":
            self.message = dedent(
                f"""\
                The input PDF has an unusual DeviceN color space that cannot be
                represented in PDF/A; the output may appear blank in some viewers
                such as Adobe Reader. Convert it to a common color space with
                --color-conversion-strategy ({self._effective_strategies}), or use
                --output-type pdf to skip PDF/A conversion and retain the original
                color space.
                """
            )
        else:
            self.message = dedent(
                f"""\
                Color conversion with --color-conversion-strategy
                {color_conversion_strategy} did not resolve the input PDF's unusual
                DeviceN color space; the output may appear blank in some viewers
                such as Adobe Reader. Try a different --color-conversion-strategy
                ({self._effective_strategies}), or use --output-type pdf to skip
                PDF/A conversion and retain the original color space.
                """
            )
