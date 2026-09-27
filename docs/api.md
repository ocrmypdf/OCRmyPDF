% SPDX-FileCopyrightText: 2022 James R. Barlow
% SPDX-License-Identifier: CC-BY-SA-4.0

# Using the OCRmyPDF API

OCRmyPDF originated as a command line program and continues to have this
legacy, but parts of it can be imported and used in other Python
applications.

Some applications may want to consider running ocrmypdf from a
subprocess call anyway, as this provides isolation of its activities.

## Example

OCRmyPDF provides one high-level function to run its main engine from an
application.

```{versionchanged} 17.0
The {func}`ocrmypdf.ocr` function now accepts an {class}`~ocrmypdf.OcrOptions`
object as its first argument, providing a cleaner API with full type hints
and validation. The previous positional argument style remains supported.
```

### Modern API (recommended)

The recommended way to call {func}`ocrmypdf.ocr` is to construct an
{class}`~ocrmypdf.OcrOptions` object with all settings, then pass it
as the sole argument:

```python
import ocrmypdf
from ocrmypdf import OcrOptions

if __name__ == '__main__':  # To ensure correct behavior on Windows and macOS
    options = OcrOptions(
        input_file='input.pdf',
        output_file='output.pdf',
        deskew=True,
        languages=['eng'],
    )
    ocrmypdf.ocr(options)
```

{class}`~ocrmypdf.OcrOptions` is a Pydantic model that provides:

- Full type hints and IDE autocompletion
- Validation of option values at construction time
- Clear documentation of all available options

```{versionadded} 17.0
The {class}`~ocrmypdf.OcrOptions` class is now exported from the top-level
`ocrmypdf` module.
```

### Legacy API

For compatibility with OCRmyPDF < v17, the traditional calling style
with positional arguments is still fully supported:

```python
import ocrmypdf

if __name__ == '__main__':  # To ensure correct behavior on Windows and macOS
    ocrmypdf.ocr('input.pdf', 'output.pdf', deskew=True)
```

With this style, all of the command line arguments are available
and may be passed as equivalent keywords.

A few differences are that `verbose` and `quiet` are not available.
Instead, output should be managed by configuring logging.

### Parent process requirements

The {func}`ocrmypdf.ocr` function runs OCRmyPDF similar to command line
execution. To do this, it will:

- create worker processes or threads
- manage the signal flags of its worker processes
- execute other subprocesses (forking and executing other programs)

The Python process that calls {func}`ocrmypdf.ocr()` must be sufficiently
privileged to perform these actions.

There currently is no option to manage how jobs are scheduled other
than the argument `jobs=` which will limit the number of worker
processes.

Creating a child process to call {func}`ocrmypdf.ocr()` is suggested. That
way your application will survive and remain interactive even if
OCRmyPDF fails for any reason. For example:

```python
from multiprocessing import Process
import ocrmypdf
from ocrmypdf import OcrOptions


def ocrmypdf_process():
    options = OcrOptions(input_file='input.pdf', output_file='output.pdf')
    ocrmypdf.ocr(options)


def call_ocrmypdf_from_my_app():
    p = Process(target=ocrmypdf_process)
    p.start()
    p.join()
```

Programs that call {func}`ocrmypdf.ocr()` should also install a SIGBUS signal
handler (except on Windows), to raise an exception if access to a memory
mapped file fails. OCRmyPDF may use memory mapping.

Several OCR jobs may run concurrently in the same Python interpreter process.

Installing a plugin set mutates interpreter-global state, because of how OCRmyPDF's
plugins and Python's library import system work, and a running job cannot survive
that state being replaced underneath it. {func}`ocrmypdf.ocr()` therefore takes a
readers-writer lock: installing a plugin set takes it exclusively, so it waits for
every job already running, while a job holds it shared for its own run. A plugin set
is installed once per interpreter and reused thereafter, so a job that asks for a
plugin set some earlier job already installed never blocks.

The practical consequence is that concurrent jobs should all use the same plugin
set. Jobs requesting different plugin sets serialize against each other. They must
also use the same `max_image_mpixels`, since Pillow's decompression-bomb limit is
interpreter-global and the last job to set it wins. If you need to run jobs with
differing configurations, use separate processes.

Because a plugin set is installed only once, a plugin module given as a file path is
executed once per interpreter rather than once per call. Plugins must not rely on
being re-executed for each job, and must not store per-job state on the plugin
manager, which concurrent jobs may share.

Note that N concurrent jobs each configured with `jobs=M` may spawn up to N*M
workers, so size `jobs` accordingly.

:::{warning}
On Windows and macOS, the script that calls {func}`ocrmypdf.ocr()` must be
protected by an "ifmain" guard (`if __name__ == '__main__'`). If you do
not take at least one of these steps, process semantics will prevent
OCRmyPDF from working correctly.
:::

### Logging

OCRmyPDF will log under loggers named `ocrmypdf`. In addition, it
imports `pdfminer` and `PIL`, both of which post log messages under
those logging namespaces.

You can configure the logging as desired for your application or call
{func}`ocrmypdf.configure_logging` to configure logging the same way
OCRmyPDF itself does. The command line parameters such as `--quiet`
and `--verbose` have no equivalents in the API; you must use the
provided configuration function or do configuration in a way that suits
your use case.

### Progress monitoring

OCRmyPDF uses the `rich` package to implement its progress bars.
{func}`ocrmypdf.configure_logging` will set up logging output to
`sys.stderr` in a way that is compatible with the display of the
progress bar. Use `ocrmypdf.ocr(...progress_bar=False)` to disable
the progress bar.

### Standard output

OCRmyPDF is strict about not writing to standard output so that
users can safely use it in a pipeline and produce a valid output
file. A caller application will have to ensure it does not write to
standard output either, if it wants to be compatible with this
behavior and support piping to a file. Another benefit of running
OCRmyPDF in a child process, as recommended above, is that it will
not interfere with the parent process's standard output.

### Exceptions

OCRmyPDF may throw standard Python exceptions, `ocrmypdf.exceptions.*`
exceptions, some exceptions related to multiprocessing, and
{exc}`KeyboardInterrupt`. The parent process should provide an exception
handler. OCRmyPDF will clean up its temporary files and worker processes
automatically when an exception occurs.

When OCRmyPDF succeeds conditionally, it returns an integer exit code.

### Bundling with PyInstaller

OCRmyPDF ships a PyInstaller hook, which PyInstaller finds automatically,
so applications that call {func}`ocrmypdf.ocr` can be frozen without extra
`--collect-*` options. The hook bundles OCRmyPDF's builtin plugins, fonts
and color profiles, and the pikepdf data needed for PDF/A output.

The external programs are not bundled. Tesseract and Ghostscript must still
be installed on the target machine and be on the `PATH`, as must any optional
tools you use, such as unpaper or pngquant. Third party plugins must be
bundled by your application.

Like any frozen application that uses multiprocessing, call
{func}`multiprocessing.freeze_support` at the start of your
`if __name__ == '__main__':` block.

### Plugin Development Changes

```{versionchanged} 16.13
Plugin hooks now receive {class}`~ocrmypdf.OcrOptions` objects instead of
`argparse.Namespace`.
```

- {class}`~ocrmypdf.OcrOptions` provides the same attribute access as `Namespace` (duck-typing compatible)
- Plugin developers should update type hints: `from ocrmypdf import OcrOptions`
- Built-in plugins no longer modify options in-place for better immutability

Most existing plugins will continue working without modification due to the
duck-typing compatibility between {class}`~ocrmypdf.OcrOptions` and `Namespace`.
