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
        if not self.registry:
            return
            
        registered_models = self.registry.get_registered_models()
        
        # Validate Tesseract options with language context
        if 'tesseract' in registered_models:
            from ocrmypdf.builtin_plugins.tesseract_ocr import TesseractOptions
            
            # Create TesseractOptions from legacy fields for validation
            tesseract_data = {
                'config': options.tesseract_config,
                'pagesegmode': options.tesseract_pagesegmode,
                'oem': options.tesseract_oem,
                'thresholding': options.tesseract_thresholding,
                'timeout': options.tesseract_timeout,
                'non_ocr_timeout': options.tesseract_non_ocr_timeout or 180.0,
                'downsample_large_images': options.tesseract_downsample_large_images,
                'downsample_above': options.tesseract_downsample_above,
                'user_words': options.user_words,
                'user_patterns': options.user_patterns,
            }
            # Remove None values
            tesseract_data = {k: v for k, v in tesseract_data.items() if v is not None}
            
            tesseract_options = TesseractOptions(**tesseract_data)
            tesseract_options.validate_with_context(options.languages)
        
        # Validate Optimize options with external program context
        if 'optimize' in registered_models:
            from ocrmypdf.builtin_plugins.optimize import OptimizeOptions
            from ocrmypdf._exec import jbig2enc, pngquant
            
            optimize_data = {
                'level': options.optimize,
                'jpeg_quality': options.jpeg_quality or 0,
                'png_quality': options.png_quality or 0,
                'jbig2_lossy': options.jbig2_lossy or False,
                'jbig2_page_group_size': options.jbig2_page_group_size or 0,
                'jbig2_threshold': options.jbig2_threshold,
            }
            
            optimize_options = OptimizeOptions(**optimize_data)
            external_programs = {
                'pngquant': pngquant.available(),
                'jbig2enc': jbig2enc.available(),
            }
            optimize_options.validate_with_context(external_programs)
    
    def _validate_cross_cutting_concerns(self, options: OCROptions) -> None:
        """Validate cross-cutting concerns that span multiple plugins."""
        # Validate mutually exclusive OCR options
        exclusive_options = sum(
            1 for opt in [options.force_ocr, options.skip_text, options.redo_ocr] if opt
        )
        if exclusive_options >= 2:
            from ocrmypdf.exceptions import BadArgsError
            raise BadArgsError("Choose only one of --force-ocr, --skip-text, --redo-ocr.")
        
        # Validate redo_ocr compatibility
        if options.redo_ocr:
            if options.deskew or options.clean_final or options.remove_background:
                from ocrmypdf.exceptions import BadArgsError
                raise BadArgsError(
                    "--redo-ocr is not currently compatible with --deskew, "
                    "--clean-final, and --remove-background"
                )
        
        # Validate output type compatibility
        if options.output_type == 'none' and str(options.output_file) not in (
            os.devnull, '-'
        ):
            from ocrmypdf.exceptions import BadArgsError
            raise BadArgsError(
                "Since you specified `--output-type none`, the output file "
                f"{options.output_file} cannot be produced. Set the output file to "
                "`-` to suppress this message."
            )
        
        # Validate PDF/A image compression compatibility
        if (options.pdfa_image_compression and 
            options.pdfa_image_compression != 'auto' and 
            not options.output_type.startswith('pdfa')):
            log.warning(
                "--pdfa-image-compression argument only applies when "
                "--output-type is one of 'pdfa', 'pdfa-1', or 'pdfa-2'"
            )
