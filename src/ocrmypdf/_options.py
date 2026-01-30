# SPDX-FileCopyrightText: 2024 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

"""Internal options model for OCRmyPDF."""

from __future__ import annotations

import json
import logging
import os
import unicodedata
from collections.abc import Sequence
from enum import StrEnum
from io import IOBase
from pathlib import Path
from typing import Any, BinaryIO

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ocrmypdf._defaults import DEFAULT_LANGUAGE, DEFAULT_ROTATE_PAGES_THRESHOLD
from ocrmypdf.exceptions import BadArgsError
from ocrmypdf.helpers import monotonic

# Import plugin option models - these will be available after plugins are loaded
# We'll use forward references and handle imports dynamically

log = logging.getLogger(__name__)

# Module-level registry for plugin option models
# This is populated by setup_plugin_infrastructure() after plugins are loaded
_plugin_option_models: dict[str, type] = {}

PathOrIO = BinaryIO | IOBase | Path | str | bytes


class ProcessingMode(StrEnum):
    """OCR processing mode for handling pages with existing text.

    This enum controls how OCRmyPDF handles pages that already contain text:

    - ``default``: Error if text is found (standard OCR behavior)
    - ``force``: Rasterize all content and run OCR regardless of existing text
    - ``skip``: Skip OCR on pages that already have text
    - ``redo``: Re-OCR pages, stripping old invisible text layer
    """

    default = 'default'
    force = 'force'
    skip = 'skip'
    redo = 'redo'


def _pages_from_ranges(ranges: str) -> set[int]:
    """Convert page range string to set of page numbers."""
    pages: list[int] = []
    page_groups = ranges.replace(' ', '').split(',')
    for group in page_groups:
        if not group:
            continue
        try:
            start, end = group.split('-')
        except ValueError:
            pages.append(int(group) - 1)
        else:
            try:
                new_pages = list(range(int(start) - 1, int(end)))
                if not new_pages:
                    raise BadArgsError(
                        f"invalid page subrange '{start}-{end}'"
                    ) from None
                pages.extend(new_pages)
            except ValueError:
                raise BadArgsError(f"invalid page subrange '{group}'") from None

    if not pages:
        raise BadArgsError(
            f"The string of page ranges '{ranges}' did not contain any recognizable "
            f"page ranges."
        )

    if not monotonic(pages):
        log.warning(
            "List of pages to process contains duplicate pages, or pages that are "
            "out of order"
        )
    if any(page < 0 for page in pages):
        raise BadArgsError("pages refers to a page number less than 1")

    log.debug("OCRing only these pages: %s", pages)
    return set(pages)


class OcrOptions(BaseModel):
    """Internal options model that can masquerade as argparse.Namespace.

    This model provides proper typing and validation while maintaining
    compatibility with existing code that expects argparse.Namespace behavior.
    """

    # I/O options
    input_file: PathOrIO
    output_file: PathOrIO
    sidecar: PathOrIO | None = None
    output_folder: Path | None = None
    work_folder: Path | None = None

    # Core OCR options
    languages: list[str] = Field(default_factory=lambda: [DEFAULT_LANGUAGE])
    output_type: str = 'auto'
    mode: ProcessingMode = ProcessingMode.default

    # Backward compatibility properties for force_ocr, skip_text, redo_ocr
    @property
    def force_ocr(self) -> bool:
        """Backward compatibility alias for mode == ProcessingMode.force."""
        return self.mode == ProcessingMode.force

    @property
    def skip_text(self) -> bool:
        """Backward compatibility alias for mode == ProcessingMode.skip."""
        return self.mode == ProcessingMode.skip

    @property
    def redo_ocr(self) -> bool:
        """Backward compatibility alias for mode == ProcessingMode.redo."""
        return self.mode == ProcessingMode.redo

    # Job control
    jobs: int | None = None
    use_threads: bool = True
    progress_bar: bool = True
    quiet: bool = False
    verbose: int = 0
    keep_temporary_files: bool = False

    # Image processing
    image_dpi: int | None = None
    deskew: bool = False
    clean: bool = False
    clean_final: bool = False
    rotate_pages: bool = False
    remove_background: bool = False
    remove_vectors: bool = False
    oversample: int = 0
    unpaper_args: str | list[str] | None = (
        None  # Can be string or list after validation
    )

    # OCR behavior
    skip_big: float | None = None
    pages: str | set[int] | None = None  # Can be string or set after validation
    invalidate_digital_signatures: bool = False

    # Metadata
    title: str | None = None
    author: str | None = None
    subject: str | None = None
    keywords: str | None = None

    # Optimization
    optimize: int = 1
    jpg_quality: int | None = None
    png_quality: int | None = None
    jbig2_threshold: float = 0.85

    # Compatibility alias for plugins that expect jpeg_quality
    @property
    def jpeg_quality(self):
        """Compatibility alias for jpg_quality."""
        return self.jpg_quality

    @jpeg_quality.setter
    def jpeg_quality(self, value):
        """Compatibility alias for jpg_quality."""
        self.jpg_quality = value

    # Advanced options
    max_image_mpixels: float = 250.0
    pdf_renderer: str = 'auto'
    ocr_engine: str = 'auto'
    rasterizer: str = 'auto'
    rotate_pages_threshold: float = DEFAULT_ROTATE_PAGES_THRESHOLD
    user_words: os.PathLike | None = None
    user_patterns: os.PathLike | None = None
    fast_web_view: float = 1.0
    continue_on_soft_render_error: bool | None = None

    # Tesseract options - also accessible via options.tesseract.<field>
    tesseract_config: list[str] = []
    tesseract_pagesegmode: int | None = None
    tesseract_oem: int | None = None
    tesseract_thresholding: int | None = None
    tesseract_timeout: float = 0.0
    tesseract_non_ocr_timeout: float | None = None
    tesseract_downsample_above: int = 32767
    tesseract_downsample_large_images: bool | None = None

    # Ghostscript options - also accessible via options.ghostscript.<field>
    pdfa_image_compression: str | None = None
    color_conversion_strategy: str = "LeaveColorUnchanged"

    # Optimize/JBIG2 options - also accessible via options.optimize.<field>
    jbig2_threshold: float = 0.85

    # Plugin system
    plugins: Sequence[Path | str] | None = None

    # Store any extra attributes (for plugins and dynamic options)
    extra_attrs: dict[str, Any] = Field(
        default_factory=dict, exclude=True, alias='_extra_attrs'
    )

    @field_validator('languages')
    @classmethod
    def validate_languages(cls, v):
        """Ensure languages list is not empty."""
        if not v:
            return [DEFAULT_LANGUAGE]
        return v

    @field_validator('output_type')
    @classmethod
    def validate_output_type(cls, v):
        """Validate output type is one of the allowed values."""
        valid_types = {'auto', 'pdfa', 'pdf', 'pdfa-1', 'pdfa-2', 'pdfa-3', 'none'}
        if v not in valid_types:
            raise ValueError(f"output_type must be one of {valid_types}")
        return v

    @field_validator('pdf_renderer')
    @classmethod
    def validate_pdf_renderer(cls, v):
        """Validate PDF renderer is one of the allowed values."""
        valid_renderers = {'auto', 'sandwich', 'fpdf2'}
        # Legacy hocr/hocrdebug are accepted but redirected to fpdf2
        legacy_renderers = {'hocr', 'hocrdebug'}
        all_accepted = valid_renderers | legacy_renderers
        if v not in all_accepted:
            raise ValueError(f"pdf_renderer must be one of {all_accepted}")
        return v

    @field_validator('rasterizer')
    @classmethod
    def validate_rasterizer(cls, v):
        """Validate rasterizer is one of the allowed values."""
        valid_rasterizers = {'auto', 'ghostscript', 'pypdfium'}
        if v not in valid_rasterizers:
            raise ValueError(f"rasterizer must be one of {valid_rasterizers}")
        return v

    @field_validator('clean_final')
    @classmethod
    def validate_clean_final(cls, v, info):
        """If clean_final is True, also set clean to True."""
        if v and hasattr(info, 'data') and 'clean' in info.data:
            info.data['clean'] = True
        return v

    @field_validator('jobs')
    @classmethod
    def validate_jobs(cls, v):
        """Validate jobs is a reasonable number."""
        if v is not None and (v < 0 or v > 256):
            raise ValueError("jobs must be between 0 and 256")
        return v

    @field_validator('verbose')
    @classmethod
    def validate_verbose(cls, v):
        """Validate verbose level."""
        if v < 0 or v > 2:
            raise ValueError("verbose must be between 0 and 2")
        return v

    @field_validator('oversample')
    @classmethod
    def validate_oversample(cls, v):
        """Validate oversample DPI."""
        if v < 0 or v > 5000:
            raise ValueError("oversample must be between 0 and 5000")
        return v

    @field_validator('max_image_mpixels')
    @classmethod
    def validate_max_image_mpixels(cls, v):
        """Validate max image megapixels."""
        if v < 0:
            raise ValueError("max_image_mpixels must be non-negative")
        return v

    @field_validator('rotate_pages_threshold')
    @classmethod
    def validate_rotate_pages_threshold(cls, v):
        """Validate rotate pages threshold."""
        if v < 0 or v > 1000:
            raise ValueError("rotate_pages_threshold must be between 0 and 1000")
        return v

    @field_validator('title', 'author', 'keywords', 'subject')
    @classmethod
    def validate_metadata_unicode(cls, v):
        """Validate metadata strings don't contain unsupported Unicode characters."""
        if v is None:
            return v

        for char in v:
            if unicodedata.category(char) == 'Co' or ord(char) >= 0x10000:
                hexchar = hex(ord(char))[2:].upper()
                raise ValueError(
                    f"Metadata string contains unsupported Unicode character: "
                    f"{char} (U+{hexchar})"
                )
        return v

    @field_validator('pages')
    @classmethod
    def validate_pages_format(cls, v):
        """Convert page ranges string to set of page numbers."""
        if v is None:
            return v
        if isinstance(v, set):
            return v  # Already processed

        # Convert string ranges to set of page numbers
        return _pages_from_ranges(v)

    @model_validator(mode='before')
    @classmethod
    def handle_special_cases(cls, data):
        """Handle special cases for API compatibility and legacy options."""
        if isinstance(data, dict):
            # For hOCR API, output_file might not be present
            if 'output_folder' in data and 'output_file' not in data:
                data['output_file'] = '/dev/null'  # Placeholder

            # Convert legacy boolean options (force_ocr, skip_text, redo_ocr) to mode
            force = data.pop('force_ocr', None)
            skip = data.pop('skip_text', None)
            redo = data.pop('redo_ocr', None)

            # Count how many legacy options are set to True
            legacy_set = [
                (force, ProcessingMode.force),
                (skip, ProcessingMode.skip),
                (redo, ProcessingMode.redo),
            ]
            legacy_true = [(val, mode) for val, mode in legacy_set if val]
            legacy_count = len(legacy_true)

            # Get current mode value (may be string or enum)
            current_mode = data.get('mode', ProcessingMode.default)
            if isinstance(current_mode, str):
                current_mode = ProcessingMode(current_mode)
            mode_is_set = current_mode != ProcessingMode.default

            if legacy_count > 1:
                raise ValueError(
                    "Choose only one of --force-ocr, --skip-text, --redo-ocr."
                )

            if legacy_count == 1:
                expected_mode = legacy_true[0][1]
                if mode_is_set and current_mode != expected_mode:
                    legacy_flag = f"--{expected_mode.value.replace('_', '-')}-ocr"
                    raise ValueError(
                        f"Conflicting options: --mode {current_mode.value} "
                        f"cannot be used with {legacy_flag} or similar legacy flag."
                    )
                # Set mode from legacy option
                data['mode'] = expected_mode

        return data

    @model_validator(mode='after')
    def validate_redo_ocr_options(self):
        """Validate options compatible with redo mode."""
        if self.mode == ProcessingMode.redo and (
            self.deskew or self.clean_final or self.remove_background
        ):
            raise ValueError(
                "--redo-ocr (or --mode redo) is not currently compatible with "
                "--deskew, --clean-final, and --remove-background"
            )
        return self

    @model_validator(mode='after')
    def validate_output_type_compatibility(self):
        """Validate output type is compatible with output file."""
        if self.output_type == 'none' and str(self.output_file) not in (
            os.devnull,
            '-',
        ):
            raise ValueError(
                "Since you specified `--output-type none`, the output file "
                f"{self.output_file} cannot be produced. Set the output file to "
                f"`-` to suppress this message."
            )
        return self

    @property
    def lossless_reconstruction(self):
        """Determine lossless_reconstruction based on other options."""
        lossless = not any(
            [
                self.deskew,
                self.clean_final,
                self.mode == ProcessingMode.force,
                self.remove_background,
            ]
        )
        return lossless

    def model_dump_json_safe(self) -> str:
        """Serialize to JSON with special handling for non-serializable types."""
        # Create a copy of the model data for serialization
        data = self.model_dump()

        # Handle special types that don't serialize to JSON directly
        def _serialize_value(value):
            if isinstance(value, Path):
                return {'__type__': 'Path', 'value': str(value)}
            elif (
                isinstance(value, BinaryIO | IOBase)
                or hasattr(value, 'read')
                or hasattr(value, 'write')
            ):
                # Stream object - replace with placeholder
                return {'__type__': 'Stream', 'value': 'stream'}
            elif hasattr(value, '__class__') and 'Iterator' in value.__class__.__name__:
                # Handle Pydantic serialization iterators
                return {'__type__': 'Stream', 'value': 'stream'}
            elif isinstance(value, property):
                # Handle property objects that shouldn't be serialized
                return None
            elif isinstance(value, list | tuple):
                return [_serialize_value(item) for item in value]
            elif isinstance(value, dict):
                return {k: _serialize_value(v) for k, v in value.items()}
            else:
                return value

        # Process all fields
        serializable_data = {}
        for key, value in data.items():
            serialized_value = _serialize_value(value)
            if serialized_value is not None:  # Skip None values from properties
                serializable_data[key] = serialized_value

        # Add extra_attrs, excluding plugin cache entries (they'll be recreated lazily)
        if self.extra_attrs:
            filtered_extra = {
                k: v
                for k, v in self.extra_attrs.items()
                if not k.startswith('_plugin_cache_')
            }
            if filtered_extra:
                serializable_data['_extra_attrs'] = _serialize_value(filtered_extra)

        return json.dumps(serializable_data)

    @classmethod
    def model_validate_json_safe(cls, json_str: str) -> OcrOptions:
        """Reconstruct from JSON with special handling for non-serializable types."""
        data = json.loads(json_str)

        # Handle special types during deserialization
        def _deserialize_value(value):
            if isinstance(value, dict) and '__type__' in value:
                if value['__type__'] == 'Path':
                    return Path(value['value'])
                elif value['__type__'] == 'Stream':
                    # For streams, we'll use a placeholder string
                    return value['value']
                else:
                    return value['value']
            elif isinstance(value, list):
                return [_deserialize_value(item) for item in value]
            elif isinstance(value, dict):
                return {k: _deserialize_value(v) for k, v in value.items()}
            else:
                return value

        # Process all fields
        deserialized_data = {}
        extra_attrs = {}

        for key, value in data.items():
            if key == '_extra_attrs':
                extra_attrs = _deserialize_value(value)
            else:
                deserialized_data[key] = _deserialize_value(value)

        # Create instance
        instance = cls(**deserialized_data)
        instance.extra_attrs = extra_attrs

        return instance

    model_config = ConfigDict(
        extra="forbid",  # Force use of extra_attrs for unknown fields
        arbitrary_types_allowed=True,  # Allow BinaryIO, Path, etc.
        validate_assignment=True,  # Validate on attribute assignment
    )

    @classmethod
    def register_plugin_models(cls, models: dict[str, type]) -> None:
        """Register plugin option model classes for nested access.

        Args:
            models: Dictionary mapping namespace to model class
        """
        global _plugin_option_models
        _plugin_option_models.update(models)

    def _get_plugin_options(self, namespace: str) -> Any:
        """Get or create a plugin options instance for the given namespace.

        This method creates plugin option instances lazily from flat field values.

        Args:
            namespace: The plugin namespace (e.g., 'tesseract', 'optimize')

        Returns:
            An instance of the plugin's option model, or None if not registered
        """
        # Use extra_attrs to cache plugin option instances
        cache_key = f'_plugin_cache_{namespace}'
        if cache_key in self.extra_attrs:
            return self.extra_attrs[cache_key]

        if namespace not in _plugin_option_models:
            raise AttributeError(
                f"Plugin namespace '{namespace}' is not registered. "
                f"Ensure setup_plugin_infrastructure() was called."
            )

        model_class = _plugin_option_models[namespace]

        def _convert_value(value):
            """Convert value to be compatible with plugin model fields."""
            if isinstance(value, os.PathLike):
                return os.fspath(value)
            return value

        # Build kwargs from flat fields
        kwargs = {}
        for field_name in model_class.model_fields:
            # Try namespace_field pattern first (e.g., tesseract_timeout)
            flat_name = f"{namespace}_{field_name}"
            if flat_name in OcrOptions.model_fields:
                value = getattr(self, flat_name)
                if value is not None:
                    kwargs[field_name] = _convert_value(value)
            # Also check direct field name (for fields like jbig2_lossy)
            elif field_name in OcrOptions.model_fields:
                value = getattr(self, field_name)
                if value is not None:
                    kwargs[field_name] = _convert_value(value)
            # Check for special mappings
            elif namespace == 'optimize' and field_name == 'level':
                # 'optimize' field maps to 'level' in OptimizeOptions
                if 'optimize' in OcrOptions.model_fields:
                    value = self.optimize
                    if value is not None:
                        kwargs[field_name] = _convert_value(value)
            elif namespace == 'optimize' and field_name == 'jpeg_quality':
                # jpg_quality maps to jpeg_quality
                if 'jpg_quality' in OcrOptions.model_fields:
                    value = self.jpg_quality
                    if value is not None:
                        kwargs[field_name] = _convert_value(value)

        # Create and cache the plugin options instance
        instance = model_class(**kwargs)
        self.extra_attrs[cache_key] = instance
        return instance

    def __getattr__(self, name: str) -> Any:
        """Support dynamic access to plugin option namespaces.

        This allows accessing plugin options like:
            options.tesseract.timeout
            options.optimize.level

        Plugin models must be registered via register_plugin_models() for
        namespace access to work. Built-in plugins register their models
        during initialization.

        Args:
            name: Attribute name

        Returns:
            Plugin options instance if name is a registered namespace,
            otherwise raises AttributeError
        """
        # Check if this is a plugin namespace
        if name.startswith('_'):
            # Private attributes should not trigger plugin lookup
            raise AttributeError(
                f"'{type(self).__name__}' object has no attribute '{name}'"
            )

        # Try to get plugin options for this namespace
        if name in _plugin_option_models:
            return self._get_plugin_options(name)

        # Check extra_attrs
        if 'extra_attrs' in self.__dict__ and name in self.extra_attrs:
            return self.extra_attrs[name]

        raise AttributeError(
            f"'{type(self).__name__}' object has no attribute '{name}'"
        )
