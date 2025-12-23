# SPDX-FileCopyrightText: 2024 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

"""Validation coordinator for plugin options and cross-cutting concerns."""

from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pluggy

    from ocrmypdf._options import OCROptions

log = logging.getLogger(__name__)


class ValidationCoordinator:
    """Coordinates validation across plugin models and core options."""

    def __init__(self, plugin_manager: pluggy.PluginManager):
        self.plugin_manager = plugin_manager
        self.registry = getattr(plugin_manager, '_option_registry', None)

    def validate_all_options(self, options: OCROptions) -> None:
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

    def _validate_plugin_contexts(self, options: OCROptions) -> None:
        """Validate plugin options that require external context."""
        # For now, we'll run the plugin validation directly since the models
        # are still being integrated. This ensures the validation warnings
        # and checks still work as expected.

        # Run Tesseract validation
        self._validate_tesseract_options(options)

        # Run Optimize validation
        self._validate_optimize_options(options)

    def _validate_tesseract_options(self, options: OCROptions) -> None:
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

        # Check for blocked languages
        from ocrmypdf.exceptions import BadArgsError
        DENIED_LANGUAGES = {'equ', 'osd'}
        if DENIED_LANGUAGES & set(options.languages):
            raise BadArgsError(
                "The following languages are for Tesseract's internal use and should not "
                "be issued explicitly: "
                f"{', '.join(DENIED_LANGUAGES & set(options.languages))}\n"
                "Remove them from the -l/--language argument."
            )

    def _validate_optimize_options(self, options: OCROptions) -> None:
        """Validate optimization options."""
        # Check optimization consistency
        if options.optimize == 0 and any([
            options.png_quality and options.png_quality > 0,
            options.jpeg_quality and options.jpeg_quality > 0
        ]):
            log.warning(
                "The arguments --png-quality and --jpeg-quality "
                "will be ignored because --optimize=0."
            )

    def _validate_cross_cutting_concerns(self, options: OCROptions) -> None:
        """Validate cross-cutting concerns that span multiple plugins."""
        # Validate mutually exclusive OCR options
        exclusive_options = sum(
            1 for opt in [options.force_ocr, options.skip_text, options.redo_ocr] if opt
        )
        if exclusive_options >= 2:
            raise ValueError("Choose only one of --force-ocr, --skip-text, --redo-ocr.")

        # Validate redo_ocr compatibility
        if options.redo_ocr:
            if options.deskew or options.clean_final or options.remove_background:
                raise ValueError(
                    "--redo-ocr is not currently compatible with --deskew, "
                    "--clean-final, and --remove-background"
                )

        # Validate output type compatibility
        if options.output_type == 'none' and str(options.output_file) not in (
            os.devnull, '-'
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
