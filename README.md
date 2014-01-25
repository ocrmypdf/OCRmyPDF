OCRmyPDF
========

OCRmyPDF adds an OCR text layer to scanned PDF files, allowing them to be searched

To get the script usage, call: sh ./OCRmyPDF.sh -h

Main features
--------

- Generates a searchable PDF/A file from a PDF file containing only images
- Places OCRed text accurately below the image to ease copy / paste
- Keeps the exact resolution of the original embedded images
    - or if requested oversamples the images before OCRing so as to get better results 
- If requested deskews and / or clean the image before performing OCR
- Validates the generated file against the PDF/A specification using jhove
- Provides debug mode to enable easy verification of the OCR results
- Processes several pages in parallel if more than one CPU core is available

For details: please consult the release notes

Motivation
----------

I searched the web for a free command line tool to OCR PDF files on linux/unix:
I found many, but none of them were really satisfying.
- Either they produced PDF files with misplaced text under the image (making copy/paste impossible)
- Or they did not display correctly some escaped html characters located in the hocr file produced by the OCR engine
- Or they changed the resolution of the embedded images
- Or they generated PDF file having a ridiculous big size
- Or they crashed when trying to OCR some of my PDF files
- Or they did not produce valid PDF files (even though they were readable with my current PDF reader) 
- On top of that none of them produced PDF/A files (format dedicated for long time storage / archiving)

... so I decided to develop my own tool (using various existing scripts as an inspiration)

Install
-------

Download OCRmyPDF here: https://github.com/fritz-hh/OCRmyPDF/releases

Copy the file in onto your linux/unix machine and extract it.

Run: "sh ./OCRmyPDF.sh -h" to get the script usage

If not yet installed, the script will notify you about dependencies that need to be installed.
The script requires specific versions of the dependencies. Older version than the ones mentioned in the release notes are likely not to be compatible to OCRmyPDF.

Support
-------

In case you detect an issue, please:

- Check if your issue is already known
- If no problem report exists on github, please create one here: https://github.com/fritz-hh/OCRmyPDF/issues
- Describe your problem thoroughly
- Append the console output of the script when running the debug mode (-g option)
- If possible provide your input PDF file as well as the content of the temporary folder (using a file sharing service like www.file-upload.net)

Press & Media
-------------

- c't 1-2014, page 59: Detailed presentation of OCRmyPDF v1.0 in the leading german IT magazine c't (http://www.heise.de/ct/inhalt/2014/1/58/)

Disclaimer
----------

The software is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
