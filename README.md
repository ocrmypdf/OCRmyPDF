OCRmyPDF
========

[![Travis build status][travis]](https://travis-ci.org/jbarlow83/OCRmyPDF) [![PyPI version][pypi]](https://pypi.org/project/ocrmypdf/) ![Homebrew version][homebrew] ![ReadTheDocs][docs]

[travis]: https://travis-ci.org/jbarlow83/OCRmyPDF.svg?branch=master "Travis build status"

[pypi]: https://img.shields.io/pypi/v/ocrmypdf.svg "PyPI version"

[homebrew]: https://img.shields.io/homebrew/v/ocrmypdf.svg "Homebrew version"

[docs]: https://readthedocs.org/projects/ocrmypdf/badge/?version=latest "RTD"

OCRmyPDF adds an OCR text layer to scanned PDF files, allowing them to be searched or copy-pasted.

```bash
ocrmypdf                      # it's a scriptable command line program
   -l eng+fra                 # it supports multiple languages
   --rotate-pages             # it can fix pages that are misrotated
   --deskew                   # it can deskew crooked PDFs!
   --title "My PDF"           # it can change output metadata
   --jobs 4                   # it uses multiple cores by default
   --output-type pdfa         # it produces PDF/A by default
   input_scanned.pdf          # takes PDF input (or images)
   output_searchable.pdf      # produces validated PDF output
```

[See the release notes for details on the latest changes](https://ocrmypdf.readthedocs.io/en/latest/release_notes.html).

Main features
-------------

- Generates a searchable [PDF/A](https://en.wikipedia.org/?title=PDF/A) file from a regular PDF
- Places OCR text accurately below the image to ease copy / paste
- Keeps the exact resolution of the original embedded images
- When possible, inserts OCR information as a "lossless" operation without disrupting any other content
- Optimizes PDF images, often producing files smaller than the input file
- If requested deskews and/or cleans the image before performing OCR
- Validates input and output files
- Distributes work across all available CPU cores
- Uses [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) engine to recognize more than [100 languages](https://github.com/tesseract-ocr/tessdata)
- Scales properly to handle files with thousands of pages
- Battle-tested on millions of PDFs

For details: please consult the [documentation](https://ocrmypdf.readthedocs.io/en/latest/).

Motivation
----------

I searched the web for a free command line tool to OCR PDF files on Linux/UNIX: I found many, but none of them were really satisfying.

- Either they produced PDF files with misplaced text under the image (making copy/paste impossible)
- Or they did not handle accents and multilingual characters
- Or they changed the resolution of the embedded images
- Or they generated ridiculously large PDF files
- Or they crashed when trying to OCR
- Or they did not produce valid PDF files
- On top of that none of them produced PDF/A files (format dedicated for long time storage)

...so I decided to develop my own tool.

Installation
------------

Linux, UNIX, and macOS are supported. Windows is not directly supported but there is a Docker image available that runs on Windows.

Users of Debian 9 or later or Ubuntu 16.10 or later may simply

```bash
apt-get install ocrmypdf
```

and users of Fedora 29 or later may simply

```bash
dnf install ocrmypdf
```

and macOS users with Homebrew may simply

```bash
brew install ocrmypdf
```

For everyone else, [see our documentation](https://ocrmypdf.readthedocs.io/en/latest/installation.html) for installation steps.

Languages
---------

OCRmyPDF uses Tesseract for OCR, and relies on its language packs. For Linux users, you can often find packages that provide language packs:

```bash
# Display a list of all Tesseract language packs
apt-cache search tesseract-ocr

# Debian/Ubuntu users
apt-get install tesseract-ocr-chi-sim  # Example: Install Chinese Simplified language back
```

You can then pass the `-l LANG` argument to OCRmyPDF to give a hint as to what languages it should search for. Multiple languages can be requested.

Documentation and support
-------------------------

Once ocrmypdf is installed, the built-in help which explains the command syntax and options can be accessed via:

```bash
ocrmypdf --help
```

Our [documentation is served on Read the Docs](https://ocrmypdf.readthedocs.io/en/latest/index.html).

If you detect an issue, please:

- Check whether your issue is already known
- If no problem report exists on github, please create one here: <https://github.com/jbarlow83/OCRmyPDF/issues>
- Describe your problem thoroughly
- Append the console output of the script when running the debug mode (`-v 1` option)
- If possible provide your input PDF file as well as the content of the temporary folder (using a file sharing service like Dropbox)

Requirements
------------

Runs on CPython 3.5, 3.6 and 3.7. Requires external program installations of Ghostscript, Tesseract OCR, QPDF, and Leptonica. ocrmypdf is pure Python, but uses CFFI to portably generate library bindings.

Press & Media
-------------

- [Going paperless with OCRmyPDF](https://medium.com/@ikirichenko/going-paperless-with-ocrmypdf-e2f36143f46a)
- [Converting a scanned document into a compressed searchable PDF with redactions](https://medium.com/@treyharris/converting-a-scanned-document-into-a-compressed-searchable-pdf-with-redactions-63f61c34fe4c)
- [c't 1-2014, page 59](http://heise.de/-2279695): Detailed presentation of OCRmyPDF v1.0 in the leading German IT magazine c't
- [heise Open Source, 09/2014: Texterkennung mit OCRmyPDF](http://heise.de/-2356670)

Business enquiries
------------------

OCRmyPDF would not be the software that it is today is without companies and users choosing to provide support for feature development and consulting enquiries. We are happy to discuss all enquiries, whether for extending the existing feature set, or integrating OCRmyPDF into a larger system.

License
-------

The OCRmyPDF software is licensed under the GNU GPLv3. Certain files are covered by other licenses, as noted in their source files.

The license for each test file varies, and is noted in tests/resources/README.rst. The documentation is licensed under Creative Commons Attribution-ShareAlike 4.0 (CC-BY-SA 4.0).

OCRmyPDF versions prior to 6.0 were distributed under the MIT License.

Disclaimer
----------

The software is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
