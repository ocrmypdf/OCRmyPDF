These test files are used in OCRmyPDF's test suite. They do not necessarily produce OCR results
at all and are not meant as examples of OCR output. Some are even invalid PDFs that might
crash certain PDF viewers.


Files derived from free sources
===============================

These test resources come from free sources, under either public domain or Creative Commons licenses.
In some cases they were converted from one image format to another without other changes.

+---------------------+--------------------------------------------------------------------------------+
| File                | Source                                                                         |
+=====================+================================================================================+
| c02-22.pdf          | `Project Gutenberg`_, Adventures of Huckleberry Finn, page 22                  |
+---------------------+--------------------------------------------------------------------------------+
| congress.jpg        | `US Congressional Records`_                                                    |
+---------------------+--------------------------------------------------------------------------------+
| graph.pdf           | `Wikimedia: Pandas text analysis.png`_                                         |
+---------------------+--------------------------------------------------------------------------------+
| lichtenstein.pdf    | `Wikimedia: JPEG2000 Lichtenstein`_ (Creative Commons BY-SA 3.0)               |
+---------------------+--------------------------------------------------------------------------------+
| LinnSequencer.jpg,  | `Wikimedia: LinnSequencer`_ (Creative Commons Attribution-ShareAlike 3.0)      |
| linn.pdf, linn.txt  |                                                                                |
+---------------------+--------------------------------------------------------------------------------+
 

Files generated for this project
================================

The following test resources were crafted specifically for this project, and can be used
under the terms of the license in LICENSE.rst.

- blank.pdf (a blank PDF page)
- cmyk.pdf (a CMYK image created in Photoshop)
- enormous.pdf (a very lage page)
- francais.pdf (a page containing French accented characters)
- hugemono.pdf (large monochrome JBIG2 page with pixel dimensions of 35000x35000)
- invalid.pdf (a PDF file header followed by EOF marker)
- missing_docinfo.pdf (PDF file with no /DocumentInfo section)


Assemblies
==========

These test resources are assemblies from other previously mentioned files, released under the same license terms as their input files.

- cardinal.pdf (four cardinal directions, rotated copies of LinnSequencer.jpg)
- ccitt.pdf (LinnSequencer.jpg, converted to CCITT encoding)
- graph_ocred.pdf (from graph.pdf)
- jbig2.pdf (congress.jpg, converted to JBIG2 encoding)
- multipage.pdf (from several other files)
- palette.pdf (congress.jpg, converted to a 256-color palette)
- skew.pdf (from c02-22.pdf)
- skew-encrypted.pdf (skew.pdf with encrypted applied)


.. _`Wikimedia: LinnSequencer`: https://upload.wikimedia.org/wikipedia/en/b/b7/LinnSequencer_hardware_MIDI_sequencer_brochure_page_2_300dpi.jpg

.. _`Project Gutenberg`: https://www.gutenberg.org/files/76/76-h/76-h.htm#c2

.. _`US Congressional Records`: http://www.baxleystamps.com/litho/meiji/courts_1871.jpg

.. _`Wikimedia: Pandas text analysis.png`: https://en.wikipedia.org/wiki/File:Pandas_text_analysis.png

.. _`Wikimedia: JPEG2000 Lichtenstein`: https://en.wikipedia.org/wiki/JPEG_2000#/media/File:Jpeg2000_2-level_wavelet_transform-lichtenstein.png