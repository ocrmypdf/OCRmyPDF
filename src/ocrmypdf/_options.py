# SPDX-FileCopyrightText: 2024 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

"""Internal options model for OCRmyPDF."""

from __future__ import annotations

import json
import logging
import os
import unicodedata
from argparse import Namespace
from collections.abc import Iterable, Sequence
from copy import copy
from io import IOBase
from pathlib import Path
from typing import Any, BinaryIO, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ocrmypdf._defaults import DEFAULT_LANGUAGE, DEFAULT_ROTATE_PAGES_THRESHOLD
from ocrmypdf.exceptions import BadArgsError
from ocrmypdf.helpers import monotonic

log = logging.getLogger(__name__)

PathOrIO = Union[BinaryIO, IOBase, Path, str, bytes]


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


class OCROptions(BaseModel):
    """Internal options model that can masquerade as argparse.Namespace.

    This model provides proper typing and validation while maintaining
    compatibility with existing code that expects argparse.Namespace behavior.
    """

    # I/O options
    input_file: PathOrIO
    output_file: PathOrIO
    sidecar: PathOrIO | None = None

    # Core OCR options
    languages: list[str] = Field(default_factory=lambda: [DEFAULT_LANGUAGE])
    output_type: str = 'pdfa'
    force_ocr: bool = False
    skip_text: bool = False
    redo_ocr: bool = False

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
    optimize: int | None = None
    jpg_quality: int | None = None
    png_quality: int | None = None
    jbig2_lossy: bool | None = None
    jbig2_page_group_size: int | None = None
    jbig2_threshold: float | None = None

    # Advanced options
    max_image_mpixels: float = 250.0
    pdf_renderer: str = 'auto'
    tesseract_config: Iterable[str] | None = None
    tesseract_pagesegmode: int | None = None
    tesseract_oem: int | None = None
    tesseract_thresholding: int | None = None
    tesseract_timeout: float | None = None
    tesseract_non_ocr_timeout: float | None = None
    tesseract_downsample_above: int | None = None
    tesseract_downsample_large_images: bool | None = None
    rotate_pages_threshold: float = DEFAULT_ROTATE_PAGES_THRESHOLD
    pdfa_image_compression: str | None = None
    color_conversion_strategy: str | None = None
    user_words: os.PathLike | None = None
    user_patterns: os.PathLike | None = None
    fast_web_view: float | None = None
    continue_on_soft_render_error: bool | None = None

    # Plugin system
    plugins: Sequence[Path | str] | None = None


    # Store any extra attributes (for plugins and dynamic options)
    extra_attrs: dict[str, Any] = Field(
        default_factory=dict, exclude=True, alias='_extra_attrs'
    )

    def __getattr__(self, name: str) -> Any:
        """Allow attribute access like argparse.Namespace."""
        if name in self.extra_attrs:
            return self.extra_attrs[name]
        raise AttributeError(
            f"'{type(self).__name__}' object has no attribute '{name}'"
        )

    def __setattr__(self, name: str, value: Any) -> None:
        """Allow attribute setting like argparse.Namespace."""
        if name.startswith('_') or name in type(self).model_fields:
            super().__setattr__(name, value)
        else:
            if not hasattr(self, 'extra_attrs'):
                super().__setattr__('extra_attrs', {})
            self.extra_attrs[name] = value

    def __delattr__(self, name: str) -> None:
        """Allow attribute deletion like argparse.Namespace."""
        if name in type(self).model_fields:
            super().__delattr__(name)
        elif name in self.extra_attrs:
            del self.extra_attrs[name]
        else:
            raise AttributeError(
                f"'{type(self).__name__}' object has no attribute '{name}'"
            )

    @classmethod
    def from_namespace(cls, ns: Namespace) -> OCROptions:
        """Convert argparse.Namespace to OCROptions."""
        # Extract known fields
        known_fields = {}
        extra_attrs = {}

        for key, value in vars(ns).items():
            if key in cls.model_fields:
                known_fields[key] = value
            else:
                extra_attrs[key] = value

        # Handle special cases for hOCR API
        if 'output_folder' in extra_attrs and 'output_file' not in known_fields:
            known_fields['output_file'] = '/dev/null'  # Placeholder

        # Handle case where input_file is missing (e.g., in _hocr_to_ocr_pdf)
        if 'work_folder' in extra_attrs and 'input_file' not in known_fields:
            known_fields['input_file'] = '/dev/null'  # Placeholder

        instance = cls(**known_fields)
        instance.extra_attrs = extra_attrs
        return instance

    def to_namespace(self) -> Namespace:
        """Convert back to argparse.Namespace for compatibility."""
        ns = Namespace()

        # Add pydantic fields
        for field_name in type(self).model_fields:
            field_value = getattr(self, field_name)
            setattr(ns, field_name, field_value)

        # Add extra attributes (including computed ones like lossless_reconstruction)
        for key, value in self.extra_attrs.items():
            setattr(ns, key, value)

        return ns

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
        valid_types = {'pdfa', 'pdf', 'pdfa-1', 'pdfa-2', 'pdfa-3', 'none'}
        if v not in valid_types:
            raise ValueError(f"output_type must be one of {valid_types}")
        return v

    @field_validator('pdf_renderer')
    @classmethod
    def validate_pdf_renderer(cls, v):
        """Validate PDF renderer is one of the allowed values."""
        valid_renderers = {'auto', 'hocr', 'sandwich', 'hocrdebug'}
        if v not in valid_renderers:
            raise ValueError(f"pdf_renderer must be one of {valid_renderers}")
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
        """Handle special cases for API compatibility."""
        if isinstance(data, dict):
            # For hOCR API, output_file might not be present
            if 'output_folder' in data and 'output_file' not in data:
                data['output_file'] = '/dev/null'  # Placeholder
            # Handle pdf_renderer 'auto' case
            if data.get('pdf_renderer') == 'auto':
                data['pdf_renderer'] = 'hocr'  # Default to hocr for auto
        return data

    @model_validator(mode='after')
    def validate_exclusive_ocr_options(self):
        """Ensure only one of force_ocr, skip_text, redo_ocr is set."""
        exclusive_options = sum(
            1 for opt in [self.force_ocr, self.skip_text, self.redo_ocr] if opt
        )
        if exclusive_options >= 2:
            raise ValueError("Choose only one of --force-ocr, --skip-text, --redo-ocr.")
        return self

    @model_validator(mode='after') 
    def validate_output_type_compatibility(self):
        """Validate output type is compatible with output file."""
        if self.output_type == 'none' and str(self.output_file) not in (os.devnull, '-'):
            raise ValueError(
                "Since you specified `--output-type none`, the output file "
                f"{self.output_file} cannot be produced. Set the output file to "
                f"`-` to suppress this message."
            )
        return self

    @model_validator(mode='after')
    def set_lossless_reconstruction(self):
        """Set lossless_reconstruction based on other options."""
        lossless = not any([
            self.deskew,
            self.clean_final, 
            self.force_ocr,
            self.remove_background,
        ])
        
        if not lossless and self.redo_ocr:
            raise ValueError(
                "--redo-ocr is not currently compatible with --deskew, "
                "--clean-final, and --remove-background"
            )
        
        # Set the computed attribute
        self.extra_attrs['lossless_reconstruction'] = lossless
        return self

    def model_dump_json_safe(self) -> str:
        """Serialize to JSON with special handling for non-serializable types."""
        # Create a copy of the model data for serialization
        data = self.model_dump()
        
        # Handle special types that don't serialize to JSON directly
        def _serialize_value(value):
            if isinstance(value, Path):
                return {'__type__': 'Path', 'value': str(value)}
            elif hasattr(value, 'read') or hasattr(value, 'write'):
                # Stream object - replace with placeholder
                return {'__type__': 'Stream', 'value': 'stream'}
            elif isinstance(value, (list, tuple)):
                return [_serialize_value(item) for item in value]
            elif isinstance(value, dict):
                return {k: _serialize_value(v) for k, v in value.items()}
            else:
                return value
        
        # Process all fields
        serializable_data = {}
        for key, value in data.items():
            serializable_data[key] = _serialize_value(value)
        
        # Add extra_attrs
        if self.extra_attrs:
            serializable_data['_extra_attrs'] = _serialize_value(self.extra_attrs)
        
        return json.dumps(serializable_data)
    
    @classmethod
    def model_validate_json_safe(cls, json_str: str) -> OCROptions:
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
