% SPDX-FileCopyrightText: 2022 James R. Barlow
% SPDX-License-Identifier: CC-BY-SA-4.0

# Common error messages

## Page already has text

:::{code}
ERROR -    1: page already has text! – aborting (use --force-ocr to force OCR)
:::

You ran ocrmypdf on a file that already contains printable text or a
hidden OCR text layer (it can\'t quite tell the difference). You
probably don\'t want to do this, because the file is already searchable.

As the error message suggests, your options are:

-   `ocrmypdf --force-ocr` to
    `rasterize <raster-vector>`{.interpreted-text role="ref"} all vector
    content and run OCR on the images. This is useful if a previous OCR
    program failed, or if the document contains a text watermark.
-   `ocrmypdf --skip-text` to skip OCR and other processing on any pages
    that contain text. Text pages will be copied into the output PDF
    without modification.
-   `ocrmypdf --redo-ocr` to scan the file for any existing OCR
    (non-printing text), remove it, and do OCR again. This is one way to
    take advantage of improvements in OCR accuracy. Printable vector
    text is excluded from OCR, so this can be used on files that contain
    a mix of digital and scanned files.

## Input file \'filename\' is not a valid PDF

OCRmyPDF checks files with pikepdf, a library that in turn uses libqpdf
to fixes errors in PDFs, before it tries to work on them. In most cases
this happens because the PDF is corrupt and truncated (incomplete file
copying) and not much can be done.

You can try rewriting the file with Ghostscript:

:::{code} bash
gs -o output.pdf -dSAFER -sDEVICE=pdfwrite input.pdf
:::

`pdftk` can also rewrite PDFs:

:::{code} bash
pdftk input.pdf cat output output.pdf
:::

Sometimes Acrobat can repair PDFs with its [Preflight
tool](https://helpx.adobe.com/acrobat/using/correcting-problem-areas-preflight-tool.html).

(tesseract-config-missing)=

## Tesseract cannot open its config file \'hocr\' or \'txt\'

:::{code}
ERROR - Tesseract cannot open its config file 'hocr'.
:::

OCRmyPDF asks Tesseract to produce `hocr` and `txt` output. Tesseract
reads the instructions for these output formats from configuration files
named `hocr` and `txt` that live in the `configs/` subdirectory of its
`tessdata` folder. If those files are missing, Tesseract prints
`read_params_file: Can't open hocr`, exits without error, and produces no
output.

This usually happens when a `tessdata` directory was assembled by hand --
for example, by downloading individual `.traineddata` files from
[tessdata_best](https://github.com/tesseract-ocr/tessdata_best) and
pointing `TESSDATA_PREFIX` at them -- because those repositories do not
include the `configs/` directory. A complete Tesseract installation from
your operating system\'s package manager includes it.

To fix this, ensure the `configs/hocr` and `configs/txt` files exist in
the `tessdata` directory that Tesseract is using. Copying the `configs/`
directory from a full Tesseract installation is sufficient. See
{envvar}`TESSDATA_PREFIX` for more on selecting an alternate `tessdata`
folder.
