% SPDX-FileCopyrightText: 2022 James R. Barlow
% SPDX-License-Identifier: CC-BY-SA-4.0

# Plugins

> The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL
> NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and
> "OPTIONAL" in this document are to be interpreted as described in
> RFC 2119.

You can use plugins to customize the behavior of OCRmyPDF at certain points of
interest.

Currently, it is possible to:

- add new command line arguments
- override the decision for whether or not to perform OCR on a particular file
- modify the image is about to be sent for OCR
- modify the page image before it is converted to PDF
- replace the Tesseract OCR with another OCR engine that has similar behavior
- replace Ghostscript with another PDF to image converter (rasterizer) or
  PDF/A generator

OCRmyPDF plugins are based on the Python `pluggy` package and conform to its
conventions. Note that: plugins installed with as setuptools entrypoints are
not checked currently, because OCRmyPDF assumes you may not want to enable
plugins for all files.

See \[OCRmyPDF-EasyOCR\](<https://github.com/ocrmypdf/OCRmyPDF-EasyOCR>) for an
example of a straightforward, fully working plugin.

## Script plugins

Script plugins may be called from the command line, by specifying the name of a file.
Script plugins may be convenient for informal or "one-off" plugins, when a certain
batch of files needs a special processing step for example.

```bash
ocrmypdf --plugin ocrmypdf_example_plugin.py input.pdf output.pdf
```

Multiple plugins may be installed by issuing the `--plugin` argument multiple times.

## Packaged plugins

Installed plugins may be installed into the same virtual environment as OCRmyPDF
is installed into. They may be invoked using Python standard module naming.
If you are intending to distribute a plugin, please package it.

```bash
ocrmypdf --plugin ocrmypdf_fancypants.pockets.contents input.pdf output.pdf
```

OCRmyPDF does not automatically import plugins, because the assumption is that
plugins affect different files differently and you may not want them activated
all the time. The command line or `ocrmypdf.ocr(plugin='...')` must call
for them.

Third parties that wish to distribute packages for ocrmypdf should package them
as packaged plugins, and these modules should begin with the name `ocrmypdf_`
similar to `pytest` packages such as `pytest-cov` (the package) and
`pytest_cov` (the module).

:::{note}
We recommend plugin authors name their plugins with the prefix
`ocrmypdf-` (for the package name on PyPI) and `ocrmypdf_` (for the
module), just like pytest plugins. At the same time, please make it clear
that your package is not official.
:::

## Plugins

You can also create a plugin that OCRmyPDF will always automatically load if both are
installed in the same virtual environment, using a project entrypoint.
OCRmyPDF uses the entrypoint namespace "ocrmypdf".

For example, `pyproject.toml` would need to contain the following, for a plugin named
`ocrmypdf-exampleplugin`:

```toml
[project]
name = "ocrmypdf-exampleplugin"

[project.entry-points."ocrmypdf"]
exampleplugin = "exampleplugin.pluginmodule"
```

## Plugin requirements

OCRmyPDF generally uses multiple worker processes. When a new worker is started,
Python will import all plugins again, including all plugins that were imported earlier.
This means that the global state of a plugin in one worker will not be shared with
other workers. As such, plugin hook implementations should be stateless, relying
only on their inputs. Hook implementations may use their input parameters to
to obtain a reference to shared state prepared by another hook implementation.
Plugins must expect that other instances of the plugin will be running
simultaneously.

The `context` object that is passed to many hooks can be used to share information
about a file being worked on. Plugins must write private, plugin-specific data to
a subfolder named `{options.work_folder}/ocrmypdf-plugin-name`. Plugins MAY
read and write files in `options.work_folder`, but should be aware that their
semantics are subject to change.

OCRmyPDF will delete `options.work_folder` when it has finished OCRing
a file, unless invoked with `--keep-temporary-files`.

The documentation for some plugin hooks contain a detailed description of the
execution context in which they will be called.

Plugins should be prepared to work whether executed in worker threads or worker
processes. Generally, OCRmyPDF uses processes, but has a semi-hidden threaded
argument that simplifies debugging.

## Plugin hooks

A plugin may provide the following hooks. Hooks must be decorated with
`ocrmypdf.hookimpl`, for example:

```python
from ocrmypdf import hookimpl

@hookimpl
def add_options(parser):
    pass
```

The following is a complete list of hooks that are available, and when
they are called.

(firstresult)=

**Note on firstresult hooks**

If multiple plugins install implementations for this hook, they will be called in
the reverse of the order in which they are installed (i.e., last plugin wins).
When each hook implementation is called in order, the first implementation that
returns a value other than `None` will "win" and prevent execution of all other
hooks. As such, you cannot "chain" a series of plugin filters together in this
way. Instead, a single hook implementation should be responsible for any such
chaining operations.

## Examples

- OCRmyPDF's test suite contains several plugins that are used to simulate certain
  test conditions.
- [ocrmypdf-papermerge](https://github.com/papermerge/OCRmyPDF_papermerge) is
  a production plugin that integrates OCRmyPDF and the Papermerge document
  management system.

### Suppressing or overriding other plugins

```{eval-rst}
.. autofunction:: ocrmypdf.pluginspec.initialize
```

### Custom command line arguments

```{eval-rst}
.. autofunction:: ocrmypdf.pluginspec.add_options
```

```{eval-rst}
.. autofunction:: ocrmypdf.pluginspec.check_options
```

### Plugin option models

Plugins can define their own option models using Pydantic. This allows plugins to:

- Define type-safe option structures with validation
- Add CLI arguments that map to their option model fields
- Access options via nested namespaces (e.g., `options.tesseract.timeout`)

```{eval-rst}
.. autofunction:: ocrmypdf.pluginspec.register_options
```

Plugin options can be accessed in two ways:

1. **Flat access** (backward compatible): `options.tesseract_timeout`
2. **Nested access**: `options.tesseract.timeout`

Both access patterns are equivalent and return the same values.

:::{note}
**Plugin Interface Change**: Starting in OCRmyPDF v17.0.0, plugin hooks receive
`OcrOptions` objects instead of `argparse.Namespace` objects. Most plugins will
continue working due to duck-typing compatibility, but plugin developers should
update their type hints accordingly.
:::

### Migration guide for plugin developers

:::{versionadded} 17.0.0
:::

**Update imports:**

```python
from ocrmypdf._options import OcrOptions
```

**Update type hints:**

```python
# Before (v16 and earlier)
def check_options(options: argparse.Namespace) -> None:
    ...

# After (v17+)
def check_options(options: OcrOptions) -> None:
    ...
```

**Attribute access unchanged:**

```python
# These work exactly as before
options.languages
options.output_type
options.tesseract_timeout
```

**Remove in-place modifications:**

```python
# Before (v16 pattern - no longer recommended)
def check_options(options):
    options.some_computed_value = compute_value(options)

# After (v17 pattern - compute at point of use)
def some_function(options):
    computed = compute_value(options)
    use_computed(computed)
```

### Execution and progress reporting

```{eval-rst}
.. autoclass:: ocrmypdf.pluginspec.ProgressBar
    :members:
    :special-members: __init__, __enter__, __exit__
```

```{eval-rst}
.. autoclass:: ocrmypdf.pluginspec.Executor
    :members:
    :special-members: __call__
```

```{eval-rst}
.. autofunction:: ocrmypdf.pluginspec.get_logging_console
```

```{eval-rst}
.. autofunction:: ocrmypdf.pluginspec.get_executor
```

```{eval-rst}
.. autofunction:: ocrmypdf.pluginspec.get_progressbar_class
```

### Applying special behavior before processing

```{eval-rst}
.. autofunction:: ocrmypdf.pluginspec.validate
```

### PDF page to image

```{eval-rst}
.. autofunction:: ocrmypdf.pluginspec.rasterize_pdf_page
```

### Modifying intermediate images

```{eval-rst}
.. autofunction:: ocrmypdf.pluginspec.filter_ocr_image
```

```{eval-rst}
.. autofunction:: ocrmypdf.pluginspec.filter_page_image
```

```{eval-rst}
.. autofunction:: ocrmypdf.pluginspec.filter_pdf_page
```

### OCR engine

```{eval-rst}
.. autofunction:: ocrmypdf.pluginspec.get_ocr_engine
```

```{eval-rst}
.. autoclass:: ocrmypdf.pluginspec.OcrEngine
    :members:

    .. automethod:: __str__
```

```{eval-rst}
.. autoclass:: ocrmypdf.pluginspec.OrientationConfidence
```

### PDF/A production

```{eval-rst}
.. autofunction:: ocrmypdf.pluginspec.generate_pdfa
```

### PDF optimization

```{eval-rst}
.. autofunction:: ocrmypdf.pluginspec.optimize_pdf
```

```{eval-rst}
.. autofunction:: ocrmypdf.pluginspec.is_optimization_enabled
```

### Working with OcrElement trees

:::{versionadded} 17.0.0
:::

OCRmyPDF v17 introduces the `OcrElement` dataclass for representing OCR
output in an engine-agnostic format. This enables plugins to work with
OCR results without parsing hOCR XML.

**Key classes:**

```python
from ocrmypdf import OcrElement, OcrClass, BoundingBox

# OcrElement - represents any OCR structural unit
page = OcrElement(
    ocr_class=OcrClass.PAGE,
    bbox=BoundingBox(0, 0, 612, 792),
    children=[...]
)

# BoundingBox - axis-aligned bounding box (left, top, right, bottom)
bbox = BoundingBox(left=100, top=50, right=300, bottom=80)

# OcrClass - constants for element types
OcrClass.PAGE      # "ocr_page"
OcrClass.LINE      # "ocr_line"
OcrClass.WORD      # "ocrx_word"
OcrClass.PARAGRAPH # "ocr_par"
```

**Navigating the tree:**

```python
# Get all words in a page
words = page.words  # Returns list[OcrElement]

# Get all lines
lines = page.lines

# Get combined text
text = page.get_text_recursive()

# Iterate by class
for para in page.paragraphs:
    print(para.get_text_recursive())
```

**OCR engine plugins:**

Plugins implementing custom OCR engines can now output `OcrElement` trees
directly via the `generate_ocr()` method, bypassing hOCR entirely:

```python
from pathlib import Path
from ocrmypdf.pluginspec import OcrEngine
from ocrmypdf import OcrElement, OcrClass, BoundingBox

class MyOcrEngine(OcrEngine):
    def generate_ocr(
        self,
        input_file: Path,
        options,
        context,
    ) -> OcrElement:
        # Perform OCR and return OcrElement tree directly
        # No need to generate hOCR XML
        return OcrElement(
            ocr_class=OcrClass.PAGE,
            bbox=BoundingBox(0, 0, width, height),
            dpi=300,
            children=[
                OcrElement(
                    ocr_class=OcrClass.LINE,
                    bbox=BoundingBox(100, 50, 500, 80),
                    children=[
                        OcrElement(
                            ocr_class=OcrClass.WORD,
                            bbox=BoundingBox(100, 50, 200, 80),
                            text="Hello",
                        ),
                        # ... more words
                    ]
                ),
                # ... more lines
            ]
        )

    def supports_generate_ocr(self) -> bool:
        return True  # Indicate this engine uses generate_ocr()
```

This approach is simpler than generating hOCR and allows modern OCR
engines to integrate more naturally with OCRmyPDF.
