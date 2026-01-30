# SPDX-FileCopyrightText: 2024 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

"""Validation coordinator for plugin options and cross-cutting concerns."""

from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pluggy

    from ocrmypdf._options import OcrOptions

log = logging.getLogger(__name__)


class ValidationCoordinator:
    """Coordinates validation across plugin models and core options."""

    def __init__(self, plugin_manager: pluggy.PluginManager):
        self.plugin_manager = plugin_manager
        self.registry = getattr(plugin_manager, '_option_registry', None)

    def validate_all_options(self, options: OcrOptions) -> None:
        """Run comprehensive validation on all options.

        This runs validation in the correct order:
        1. Plugin self-validation (already done by Pydantic)
        2. Plugin context validation (requires external context)
        3. Cross-cutting validation (between plugins and core)

        Args:
            options: The options to validate
        """
        # Step 1: Plugin context validation
        self._validate_plugin_contexts(options)

        # Step 2: Cross-cutting validation
        self._validate_cross_cutting_concerns(options)

    def _validate_plugin_contexts(self, options: OcrOptions) -> None:
        """Validate plugin options that require external context."""
        # For now, we'll run the plugin validation directly since the models
        # are still being integrated. This ensures the validation warnings
        # and checks still work as expected.

        # Run Tesseract validation
        self._validate_tesseract_options(options)

        # Run Optimize validation
        self._validate_optimize_options(options)

    def _validate_tesseract_options(self, options: OcrOptions) -> None:
        """Validate Tesseract options."""
        # Check pagesegmode warning
        if options.tesseract.pagesegmode in (0, 2):
            log.warning(
                "The tesseract-pagesegmode you selected will disable OCR. "
                "This may cause processing to fail."
            )

        # Check downsample consistency
        if (
            options.tesseract.downsample_above != 32767
            and not options.tesseract.downsample_large_images
        ):
            log.warning(
                "The --tesseract-downsample-above argument will have no effect unless "
                "--tesseract-downsample-large-images is also given."
            )

        # Note: blocked languages (equ, osd) are checked earlier in
        # check_options_languages() to ensure the check runs before
        # the missing language check.

    def _validate_optimize_options(self, options: OcrOptions) -> None:
        """Validate optimization options."""
        # Check optimization consistency
        if options.optimize == 0 and any(
            [
                options.png_quality and options.png_quality > 0,
                options.jpeg_quality and options.jpeg_quality > 0,
            ]
        ):
            log.warning(
                "The arguments --png-quality and --jpeg-quality "
                "will be ignored because --optimize=0."
            )

    def _validate_cross_cutting_concerns(self, options: OcrOptions) -> None:
        """Validate cross-cutting concerns that span multiple plugins."""
        from ocrmypdf._options import ProcessingMode

        # Handle deprecated pdf_renderer values
        self._handle_deprecated_pdf_renderer(options)

        # Note: Mutual exclusivity of force_ocr/skip_text/redo_ocr is now enforced
        # by the ProcessingMode enum - only one mode can be active at a time.

        # Validate redo mode compatibility
        if options.mode == ProcessingMode.redo and (
            options.deskew or options.clean_final or options.remove_background
        ):
            raise ValueError(
                "--redo-ocr (or --mode redo) is not currently compatible with "
                "--deskew, --clean-final, and --remove-background"
            )

        # Validate output type compatibility
        if options.output_type == 'none' and str(options.output_file) not in (
            os.devnull,
            '-',
        ):
            raise ValueError(
                "Since you specified `--output-type none`, the output file "
                f"{options.output_file} cannot be produced. Set the output file to "
                "`-` to suppress this message."
            )

        # Validate PDF/A image compression compatibility
        if (
            options.ghostscript.pdfa_image_compression
            and options.ghostscript.pdfa_image_compression != 'auto'
            and not options.output_type.startswith('pdfa')
        ):
            log.warning(
                "--pdfa-image-compression argument only applies when "
                "--output-type is one of 'pdfa', 'pdfa-1', or 'pdfa-2'"
            )

    def _handle_deprecated_pdf_renderer(self, options: OcrOptions) -> None:
        """Handle deprecated pdf_renderer values by redirecting to fpdf2."""
        if options.pdf_renderer in ('hocr', 'hocrdebug'):
            log.info(
                "The '%s' PDF renderer has been removed. Using 'fpdf2' instead, "
                "which provides full international language support, proper RTL "
                "rendering, and improved text positioning.",
                options.pdf_renderer,
            )
            # Modify the options object to use fpdf2
            object.__setattr__(options, 'pdf_renderer', 'fpdf2')
