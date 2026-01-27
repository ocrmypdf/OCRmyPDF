"""Test JSON serialization of OcrOptions for multiprocessing compatibility."""
from __future__ import annotations

import multiprocessing
from io import BytesIO
from pathlib import Path, PurePath

import pytest

from ocrmypdf._options import OcrOptions
from ocrmypdf.builtin_plugins.tesseract_ocr import TesseractOptions


@pytest.fixture(autouse=True)
def register_plugin_models():
    """Register plugin models for tests."""
    OcrOptions.register_plugin_models({'tesseract': TesseractOptions})
    yield
    # Clean up after test (optional, but good practice)


def worker_function(options_json: str) -> str:
    """Worker function that deserializes OcrOptions from JSON and returns a result."""
    # Register plugin models in worker process
    from ocrmypdf._options import OcrOptions
    from ocrmypdf.builtin_plugins.tesseract_ocr import TesseractOptions

    OcrOptions.register_plugin_models({'tesseract': TesseractOptions})

    # Reconstruct OcrOptions from JSON in worker process
    options = OcrOptions.model_validate_json_safe(options_json)

    # Verify we can access various option types
    # Count only user-added extra_attrs (exclude plugin cache keys starting with '_')
    user_attrs_count = len(
        [k for k in options.extra_attrs.keys() if not k.startswith('_')]
    )
    result = {
        'input_file': str(options.input_file),
        'output_file': str(options.output_file),
        'languages': options.languages,
        'optimize': options.optimize,
        'tesseract_timeout': options.tesseract.timeout,
        'fast_web_view': options.fast_web_view,
        'extra_attrs_count': user_attrs_count,
    }

    # Return as JSON string
    import json

    return json.dumps(result)


def test_json_serialization_multiprocessing():
    """Test that OcrOptions can be JSON serialized and used in multiprocessing."""
    # Create OcrOptions with various field types
    options = OcrOptions(
        input_file=Path('/test/input.pdf'),
        output_file=Path('/test/output.pdf'),
        languages=['eng', 'deu'],
        optimize=2,
        tesseract_timeout=120.0,
        fast_web_view=2.5,
        deskew=True,
        clean=False,
    )

    # Add some extra attributes
    options.extra_attrs['custom_field'] = 'test_value'
    options.extra_attrs['numeric_field'] = 42

    # Serialize to JSON
    options_json = options.model_dump_json_safe()

    # Test that we can deserialize in the main process
    reconstructed = OcrOptions.model_validate_json_safe(options_json)
    assert reconstructed.input_file == options.input_file
    assert reconstructed.output_file == options.output_file
    assert reconstructed.languages == options.languages
    assert reconstructed.optimize == options.optimize
    assert reconstructed.tesseract_timeout == options.tesseract.timeout
    assert reconstructed.fast_web_view == options.fast_web_view
    assert reconstructed.deskew == options.deskew
    assert reconstructed.clean == options.clean
    # Compare user-added extra_attrs (excluding plugin cache keys)
    user_attrs = {k: v for k, v in options.extra_attrs.items() if not k.startswith('_')}
    reconstructed_attrs = {
        k: v for k, v in reconstructed.extra_attrs.items() if not k.startswith('_')
    }
    assert reconstructed_attrs == user_attrs

    # Test multiprocessing with JSON serialization
    with multiprocessing.Pool(processes=2) as pool:
        # Send the JSON string to worker processes
        results = pool.map(worker_function, [options_json, options_json])

    # Verify results from worker processes
    import json

    for result_json in results:
        result = json.loads(result_json)
        assert PurePath(result['input_file']) == PurePath('/test/input.pdf')
        assert PurePath(result['output_file']) == PurePath('/test/output.pdf')
        assert result['languages'] == ['eng', 'deu']
        assert result['optimize'] == 2
        assert result['tesseract_timeout'] == 120.0
        assert result['fast_web_view'] == 2.5
        assert result['extra_attrs_count'] == 2  # custom_field and numeric_field


def test_json_serialization_with_streams():
    """Test JSON serialization with stream objects."""
    input_stream = BytesIO(b'fake pdf data')
    output_stream = BytesIO()

    options = OcrOptions(
        input_file=input_stream,
        output_file=output_stream,
        languages=['eng'],
        optimize=1,
    )

    # Serialize to JSON (streams should be converted to placeholders)
    options_json = options.model_dump_json_safe()

    # Deserialize (streams will be placeholder strings)
    reconstructed = OcrOptions.model_validate_json_safe(options_json)

    # Streams should be converted to placeholder strings
    assert reconstructed.input_file == 'stream'
    assert reconstructed.output_file == 'stream'
    assert reconstructed.languages == ['eng']
    assert reconstructed.optimize == 1


def test_json_serialization_with_none_values():
    """Test JSON serialization handles None values correctly."""
    options = OcrOptions(
        input_file=Path('/test/input.pdf'),
        output_file=Path('/test/output.pdf'),
        languages=['eng'],
        # Many fields will be None by default
    )

    # Serialize to JSON
    options_json = options.model_dump_json_safe()

    # Deserialize
    reconstructed = OcrOptions.model_validate_json_safe(options_json)

    # Verify None values are preserved (check actual defaults from model)
    assert reconstructed.tesseract_timeout == 0.0  # Default value, not None
    assert reconstructed.fast_web_view == 1.0  # Default value, not None
    assert (
        reconstructed.color_conversion_strategy == "LeaveColorUnchanged"
    )  # Default value
    assert reconstructed.pdfa_image_compression is None  # This one is actually None

    # Verify non-None values are preserved
    assert reconstructed.input_file == options.input_file
    assert reconstructed.output_file == options.output_file
    assert reconstructed.languages == options.languages
