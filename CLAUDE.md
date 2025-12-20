# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

OCRmyPDF adds an OCR text layer to scanned PDF files, making them searchable. It uses Tesseract OCR and Ghostscript as external dependencies.

## Common Commands

```bash
# Run all tests (uses pytest-xdist for parallel execution)
pytest

# Run a single test file
pytest tests/test_main.py

# Run a specific test
pytest tests/test_main.py::test_function_name

# Run tests with coverage
pytest --cov=src/ocrmypdf --cov-report=html

# Run slow tests (disabled by default)
pytest --runslow

# Lint and format
ruff check src/
ruff format src/

# Type checking
mypy src/ocrmypdf
```

## Architecture

### Entry Points
- **CLI**: `src/ocrmypdf/__main__.py` → `src/ocrmypdf/cli.py` parses arguments
- **Python API**: `src/ocrmypdf/api.py` provides `ocr()` function for programmatic use

### Core Pipeline
The OCR pipeline is in `src/ocrmypdf/_pipeline.py` and `src/ocrmypdf/_pipelines/`. Processing flow:
1. Input validation and triage (PDF vs image)
2. PDF info extraction (`src/ocrmypdf/pdfinfo/`)
3. Page-by-page OCR processing (parallelized)
4. PDF/A generation and optimization

### Options Model
`src/ocrmypdf/_options.py` contains `OCROptions`, a Pydantic model that validates all CLI and API options. Options validation happens in `src/ocrmypdf/_validation.py` with cross-cutting validation in `src/ocrmypdf/_validation_coordinator.py`.

### Plugin System
OCRmyPDF uses `pluggy` for extensibility. Key files:
- `src/ocrmypdf/pluginspec.py`: Defines all hook specifications
- `src/ocrmypdf/builtin_plugins/`: Default implementations
  - `tesseract_ocr.py`: Tesseract OCR engine
  - `ghostscript.py`: PDF rasterization and PDF/A generation
  - `optimize.py`: PDF optimization

Plugins can replace the OCR engine, add CLI arguments, or modify image processing.

### External Tool Wrappers
`src/ocrmypdf/_exec/` contains wrappers for external tools:
- `ghostscript.py`: PDF rasterization, PDF/A conversion
- `tesseract.py`: OCR engine interface
- `unpaper.py`: Image preprocessing (deskew, clean)
- `jbig2enc.py`, `pngquant.py`: Image optimization

### Job Context
- `PdfContext`: Document-level context passed through pipeline
- `PageContext`: Per-page context for parallel processing

## Testing

Tests are in `tests/` with fixtures defined in `tests/conftest.py`. Key fixtures:
- `resources`: Path to test PDF/image files in `tests/resources/`
- `outpdf`: Temporary output PDF path
- `check_ocrmypdf()`: Run OCR and assert valid output
- `run_ocrmypdf_api()`: Run via API, returns ExitCode
- `run_ocrmypdf()`: Run as subprocess

## External Dependencies

Requires system packages: Tesseract OCR, Ghostscript. Optional: unpaper, jbig2enc, pngquant.

## License

MPL-2.0 for core code. Tests and docs use CC-BY-SA-4.0.
