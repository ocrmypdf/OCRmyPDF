These test files are used in OCRmyPDF's test suite. They do not necessarily produce OCR results
at all and are not meant as examples of OCR output. Some are even invalid PDFs that might
crash certain PDF viewers.


Files derived from free sources
===============================

These test resources come from free sources, under either public domain or Creative Commons licenses.
In some cases they were converted from one image format to another without other changes.

.. list-table:: 
    :widths: 20 50 30
    :header-rows: 1

    *   - File
        - Source
        - License
    *   - c02-22.pdf
        - `Project Gutenberg`_, Adventures of Huckleberry Finn, page 22
        - Public Domain
    *   - congress.jpg
        - `US Congressional Records`_
        - Public Domain
    *   - graph.pdf
        - `Wikimedia: Pandas text analysis.png`_
        - Public Domain
    *   - lichtenstein.pdf
        - `Wikimedia: JPEG2000 Lichtenstein`_
        - Creative Commons BY-SA 3.0
    *   - LinnSequencer.jpg, linn.pdf, linn.txt
        - `Wikimedia: LinnSequencer`_
        - Creative Commons BY-SA 3.0


Files generated for this project
================================

The following test resources were crafted specifically for this project, and can be used
under the terms of the license in LICENSE.rst.

.. list-table:: 
    :widths: 20 20 60
    :header-rows: 1

    *   - File
        - Contributor
        - Purpose
    *   - aspect.pdf
        - @jbarlow83
        - test image with 200 x 100 DPI resolution
    *   - blank.pdf
        - @jbarlow83
        - blank PDF
    *   - cmyk.pdf
        - @jbarlow83
        - a CMYK image created in Photoshop
    *   - enormous.pdf
        - @jbarlow83
        - very large PDF page
    *   - epson.pdf
        - @lowesjam
        - a linearized PDF containing some unusual indirect objects, created by an Epson printer; printout of a Wikipedia article (CC BY-SA)
    *   - francais.pdf
        - @jbarlow83
        - a page containing French accents (diacritics)  
    *   - hugemono.pdf
        - @jbarlow83
        - large monochrome 35000x35000 image in JBIG2 encoding 
    *   - invalid.pdf
        - @jbarlow83
        - a PDF file header followed by EOF marker
    *   - masks.pdf
        - @supergrobi
        - file containing explicit masks and a stencil mask drawn without a proper transformation matrix; printout of a German Wikipedia article (CC BY-SA)
    *   - missing_docinfo.pdf
        - @jbarlow83
        - PDF file with no /DocumentInfo section 

Assemblies
==========

These test resources are assemblies from other previously mentioned files, released under the same license terms as their input files.

- cardinal.pdf (four cardinal directions, rotated copies of LinnSequencer.jpg)
- ccitt.pdf (LinnSequencer.jpg, converted to CCITT encoding)
- encrypted_algo4.pdf (congress.jpg, encrypted with algorithm 4 - not supported by PyPDF2)
- graph_ocred.pdf (from graph.pdf)
- jbig2.pdf (congress.jpg, converted to JBIG2 encoding)
- multipage.pdf (from several other files)
- palette.pdf (congress.jpg, converted to a 256-color palette)
- skew.pdf (from c02-22.pdf)
- skew-encrypted.pdf (skew.pdf with encryption - access supported by PyPDF2)


.. _`Wikimedia: LinnSequencer`: https://upload.wikimedia.org/wikipedia/en/b/b7/LinnSequencer_hardware_MIDI_sequencer_brochure_page_2_300dpi.jpg

.. _`Project Gutenberg`: https://www.gutenberg.org/files/76/76-h/76-h.htm#c2

.. _`US Congressional Records`: http://www.baxleystamps.com/litho/meiji/courts_1871.jpg

.. _`Wikimedia: Pandas text analysis.png`: https://en.wikipedia.org/wiki/File:Pandas_text_analysis.png

.. _`Wikimedia: JPEG2000 Lichtenstein`: https://en.wikipedia.org/wiki/JPEG_2000#/media/File:Jpeg2000_2-level_wavelet_transform-lichtenstein.png

.. _`Linux (Wikipedia Article)`: https://de.wikipedia.org/wiki/Linux 