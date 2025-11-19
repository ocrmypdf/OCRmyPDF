# SPDX-License-Identifier: MPL-2.0
"""RapidOCR engine implementation."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Set

import numpy as np
from PIL import Image
from PIL import ImageEnhance

from ocrmypdf.pluginspec import OrientationConfidence, OcrEngine

log = logging.getLogger(__name__)

# Make the debug messages more visible
log.info("Initializing RapidOCR engine module")

# Try to import RapidOCR and track its availability
RAPIDOCR_AVAILABLE = False
IMPORT_ERROR_MESSAGE = ""

try:
    # Import with verbose logging to diagnose any issues
    log.info("Attempting to import RapidOCR...")
    from rapidocr_onnxruntime import RapidOCR

    # Get version info
    rapidocr_version = "unknown"
    try:
        # Try to get version directly
        from rapidocr_onnxruntime import __version__ as rapidocr_version
    except ImportError:
        # Try to get version from the package metadata
        try:
            import pkg_resources

            rapidocr_version = pkg_resources.get_distribution(
                "rapidocr_onnxruntime"
            ).version
        except (pkg_resources.DistributionNotFound, ImportError):
            # Try to get version from the module object
            try:
                rapidocr_version = getattr(RapidOCR, "__version__", "unknown")
            except (AttributeError, TypeError):
                log.warning("RapidOCR version not available")

    # Test if RapidOCR can actually be initialized
    try:
        test_engine = RapidOCR(use_angle_cls=False)
        RAPIDOCR_AVAILABLE = True
        log.info(
            f"✓ RapidOCR successfully imported and initialized, version: {rapidocr_version}"
        )
    except Exception as e:
        IMPORT_ERROR_MESSAGE = f"RapidOCR initialization failed: {str(e)}"
        log.warning(f"✗ {IMPORT_ERROR_MESSAGE}")

except ImportError as e:
    IMPORT_ERROR_MESSAGE = str(e)
    rapidocr_version = 'not installed'
    log.warning(f"✗ RapidOCR import failed: {IMPORT_ERROR_MESSAGE}")


class RapidOcrEngine(OcrEngine):
    """Implements OCR with RapidOCR."""

    def __init__(self):
        """Initialize the RapidOCR engine."""
        if not RAPIDOCR_AVAILABLE:
            log.warning("RapidOCR engine initialized but the library is not available")
        else:
            log.info("RapidOCR engine initialized successfully")

    @staticmethod
    def version() -> str:
        """Return the version of RapidOCR."""
        if not RAPIDOCR_AVAILABLE:
            return "not installed"
        return rapidocr_version

    @staticmethod
    def creator_tag(options) -> str:
        """Return a creator tag for PDF metadata."""
        return f"RapidOCR {RapidOcrEngine.version()}"

    def __str__(self):
        return f"RapidOCR {self.version()}"

    @staticmethod
    def languages(options) -> Set[str]:
        """Return the languages supported by RapidOCR."""
        # RapidOCR primarily supports Chinese, English and other languages
        # but does not have the same language-specific models as Tesseract
        # Return a set of common languages it works well with
        return {'chi_sim', 'chi_tra', 'eng'}

    @staticmethod
    def get_orientation(input_file: Path, options) -> OrientationConfidence:
        """Return the orientation detected by RapidOCR."""
        # RapidOCR doesn't have built-in orientation detection like Tesseract
        # Returning default value - could be enhanced with custom algo
        return OrientationConfidence(angle=0, confidence=0.0)

    @staticmethod
    def get_deskew(input_file: Path, options) -> float:
        """Return deskew angle (degrees)."""
        # Return 0 as RapidOCR doesn't have direct deskew calculation
        return 0.0

    @staticmethod
    def generate_hocr(
        input_file: Path, output_hocr: Path, output_text: Path, options
    ) -> None:
        """Generate HOCR file from the OCR results."""
        if not RAPIDOCR_AVAILABLE:
            error_msg = f"rapidocr_onnxruntime is not installed: {IMPORT_ERROR_MESSAGE}"
            log.error(error_msg)
            raise ImportError(
                f"{error_msg}\nInstall it with: pip install rapidocr_onnxruntime"
            )

        try:
            # Load image
            image = Image.open(input_file)
            # Convert to numpy array for RapidOCR
            img_array = np.array(image)

            # Pre-process the image to improve detection
            # Increase contrast
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.5)  # Increase contrast by 50%

            # Or try padding the image
            padded = Image.new(
                image.mode, (image.width, image.height + 20), (255, 255, 255)
            )
            padded.paste(image, (0, 0))
            img_array = np.array(padded)

            # Initialize RapidOCR with configured options
            rapidocr = RapidOCR(
                use_angle_cls=getattr(options, 'rapidocr_use_angle_cls', False),
                lang=getattr(options, 'rapidocr_lang', 'en'),
            )

            # Perform OCR - handle different return value patterns
            log.debug(f"Running RapidOCR on image with shape: {img_array.shape}")
            result = rapidocr(img_array)
            log.info(f"RapidOCR returned result type: {type(result)}")

            # Print complete result for debugging
            if isinstance(result, list):
                log.info(f"Got list with {len(result)} items")
                if len(result) > 0:
                    sample_item = result[0]
                    log.info(
                        f"First result item type: {type(sample_item)}, value: {sample_item}"
                    )
            elif isinstance(result, tuple):
                log.info(f"Got tuple with {len(result)} items")
                for i, item in enumerate(result):
                    if i < 2:  # Only log first two items to avoid excessive output
                        log.info(f"Tuple item {i}: type={type(item)}, value={item}")
            else:
                log.info(f"Got unexpected result type: {type(result)}")

            # Inspect the result structure to determine format
            if isinstance(result, list):
                # Format appears to be direct data from PaddleOCR
                # Each element is [box_coordinates, text, confidence]
                text_results = []
                boxes_list = []

                for item in result:
                    if len(item) == 3:  # [box, text, confidence]
                        box_coords, text, confidence = item
                        text_results.append((text, float(confidence)))
                        boxes_list.append(box_coords)
                        log.debug(f"Added text '{text}' with box {box_coords}")
                    else:
                        log.warning(f"Unexpected result item format: {item}")

                log.info(f"Extracted {len(text_results)} text elements from RapidOCR")
            elif isinstance(result, tuple) and len(result) >= 2:
                # The output is a tuple with (result_list, timing_info)
                # Where result_list is a list of [box_coords, text, confidence] triplets
                result_list = result[0]
                if isinstance(result_list, list):
                    text_results = []
                    boxes_list = []

                    log.info(
                        f"Processing tuple result with {len(result_list)} text items"
                    )

                    # Process each detection item from tuple result
                    for item in result_list:
                        if isinstance(item, list) and len(item) == 3:
                            box_coords, text, confidence = item
                            text_results.append((text, float(confidence)))
                            boxes_list.append(box_coords)
                            log.debug(
                                f"Added text from tuple: '{text}' with confidence {confidence}"
                            )
                        else:
                            log.warning(
                                f"Unexpected item format in tuple result: {item}"
                            )

                    log.info(
                        f"Extracted {len(text_results)} text elements from tuple result"
                    )
                else:
                    text_results = []
                    boxes_list = []
                    log.warning(f"Unexpected format in tuple result[0]: {result_list}")
            else:
                # Fallback
                text_results = []
                boxes_list = []
                log.warning(f"Unrecognized RapidOCR result format: {result}")

            # Generate plain text content
            if text_results:
                if isinstance(text_results[0], tuple):
                    # Format: [(text, confidence), ...]
                    text_content = '\n'.join(text for text, _ in text_results)
                else:
                    # Format: [text, ...]
                    text_content = '\n'.join(str(text) for text in text_results)
            else:
                text_content = ''

            # Debug info
            log.debug(f"Extracted text count: {len(text_results)}")
            if boxes_list:
                log.debug(f"Box list count: {len(boxes_list)}")
                log.debug(f"Sample box format: {boxes_list[0]}")

            # Generate HOCR content
            hocr_content = _generate_hocr_from_rapidocr(
                text_results, boxes_list, image.width, image.height, input_file.name
            )

            # Write HOCR and plain text output
            output_hocr.write_text(hocr_content, encoding='utf-8')
            output_text.write_text(text_content, encoding='utf-8')

        except Exception as e:
            log.error(f"RapidOCR processing error: {str(e)}")
            import traceback

            log.error(f"Stack trace: {traceback.format_exc()}")
            # Create empty files to avoid downstream errors
            output_hocr.write_text('', encoding='utf-8')
            output_text.write_text('[RapidOCR processing error]', encoding='utf-8')

    @staticmethod
    def generate_pdf(
        input_file: Path, output_pdf: Path, output_text: Path, options
    ) -> None:
        """Generate a PDF with OCR results."""
        # First generate HOCR
        temp_hocr = output_pdf.with_suffix('.hocr')
        RapidOcrEngine.generate_hocr(input_file, temp_hocr, output_text, options)

        # Use the existing HocrTransform for converting HOCR to PDF
        # This is a simplified approach - a full implementation would create PDF directly
        from ocrmypdf.hocrtransform import HocrTransform

        if temp_hocr.stat().st_size > 0:
            # Get DPI from image
            try:
                image = Image.open(input_file)
                if 'dpi' in image.info:
                    dpi = image.info['dpi'][0]  # Use x-resolution
                else:
                    dpi = 300  # Default DPI
            except Exception:
                dpi = 300  # Default fallback

            transform = HocrTransform(hocr_filename=str(temp_hocr), dpi=dpi)
            transform.to_pdf(
                out_filename=output_pdf,
                image_filename=input_file,
                invisible_text=True,
            )
        else:
            # If HOCR generation failed, create an empty PDF
            output_pdf.write_bytes(b'')


def _generate_hocr_from_rapidocr(result, boxes_list, width, height, filename):
    """Generate HOCR content from RapidOCR results."""
    hocr = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">',
        '<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">',
        '<head>',
        '  <title>RapidOCR Results</title>',
        '  <meta http-equiv="Content-Type" content="text/html;charset=utf-8"/>',
        '  <meta name="ocr-system" content="RapidOCR"/>',
        '</head>',
        '<body>',
        f'  <div class="ocr_page" id="page_1" title="image {filename}; bbox 0 0 {width} {height}">',
    ]

    # If there are no results, create an empty page
    if not result:
        hocr.append('  </div>')
        hocr.append('</body>')
        hocr.append('</html>')
        return '\n'.join(hocr)

    # Add paragraphs and lines
    hocr.append('    <div class="ocr_carea" id="block_1">')
    hocr.append('      <p class="ocr_par">')

    # Check if boxes_list has same length as result
    boxes_match = len(boxes_list) == len(result)

    # Handle case where boxes are provided directly along with the text
    for i, item in enumerate(result):
        text = None
        confidence = 0.9
        box = None

        # Extract text, confidence, box based on format
        if isinstance(item, tuple) and len(item) == 2:
            # Item is (text, confidence)
            text, confidence = item
            if boxes_match and i < len(boxes_list):
                box = boxes_list[i]
        elif isinstance(item, str):
            # Item is just text
            text = item
            if boxes_match and i < len(boxes_list):
                box = boxes_list[i]

        # If we couldn't determine text, skip this item
        if text is None:
            continue

        # If we have valid box coordinates, use them
        if box is not None:
            _add_hocr_word(hocr, i, text, confidence, box)
        else:
            # Create fallback positioning
            x = width // 4
            y = height // 4 + (i * 20)
            max_x = x + (width // 2)
            max_y = y + 20

            hocr.append(
                f'        <span class="ocr_line" id="line_{i + 1}" '
                f'title="bbox {x} {y} {max_x} {max_y}">'
            )
            hocr.append(
                f'          <span class="ocrx_word" id="word_{i + 1}" '
                f'title="bbox {x} {y} {max_x} {max_y}; '
                f'x_conf {confidence * 100:.2f}">{text}</span>'
            )
            hocr.append('        </span>')

    # Close all open tags
    hocr.append('      </p>')
    hocr.append('    </div>')
    hocr.append('  </div>')
    hocr.append('</body>')
    hocr.append('</html>')

    return '\n'.join(hocr)


def _add_hocr_word(hocr, index, text, confidence, box):
    """Add a word to the hOCR output."""
    # Handle different box formats

    # Case 1: Box is a list of 4 points with [x,y] coordinates
    # Format: [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
    if (
        isinstance(box, list)
        and len(box) == 4
        and all(isinstance(pt, list) and len(pt) == 2 for pt in box)
    ):
        x_coords = [pt[0] for pt in box]
        y_coords = [pt[1] for pt in box]
        x = min(x_coords)
        y = min(y_coords)
        max_x = max(x_coords)
        max_y = max(y_coords)

    # Case 2: Box is a flattened list of 8 coordinates
    # Format: [x1,y1,x2,y2,x3,y3,x4,y4]
    elif isinstance(box, list) and len(box) == 8:
        x_coords = [box[0], box[2], box[4], box[6]]
        y_coords = [box[1], box[3], box[5], box[7]]
        x = min(x_coords)
        y = min(y_coords)
        max_x = max(x_coords)
        max_y = max(y_coords)

    # Case 3: Box is a simple rectangle [x,y,width,height]
    elif isinstance(box, list) and len(box) == 4:
        x, y, max_x, max_y = box

    # Default case or other formats
    else:
        log.warning(f"Unrecognized box format: {box}")
        x, y, max_x, max_y = 0, 0, 100, 20

    # Convert coordinates to integers to avoid floating point issues
    x = int(round(x))
    y = int(round(y))
    max_x = int(round(max_x))
    max_y = int(round(max_y))

    # Handle confidence - ensure it's a number
    try:
        conf = float(confidence)
    except (TypeError, ValueError):
        conf = 0.9

    # Add line and word elements
    line_id = f"line_{index + 1}"
    word_id = f"word_{index + 1}"

    hocr.append(
        f'        <span class="ocr_line" id="{line_id}" '
        f'title="bbox {x} {y} {max_x} {max_y}">'
    )
    hocr.append(
        f'          <span class="ocrx_word" id="{word_id}" '
        f'title="bbox {x} {y} {max_x} {max_y}; '
        f'x_conf {conf * 100:.2f}">{text}</span>'
    )
    hocr.append('        </span>')
