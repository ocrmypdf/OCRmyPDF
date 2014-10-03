Recoding in 5 python modules
==================

- Less platform dependent implementation
- Higher versality (wrt addition of new intput / output file tytes)

The functionality of each module is described below:

Normalize inputs (inputs can be a pdf file, an image, a folder containing images)
----------------

- For pdf:
  - Identify if image already contains fonts
  - If the page needs to be OCRed:
    - Extract the image corresponding to the page and save it in a tmp folder. 3 approaches to extract images:
    - extract raw image from pdf and rotate it according to pdf page rotation
      - if not possible: identify resolution and rasterize
      - if not possible: use default resolution and rasterize
  - If not:
    - Save the page AS-IS in the tmp folder that should contained the final page
- For image(s):
  - Just copy the images with standardized name into the tmp folder containing pages to be OCRed

Preprocess normalized inputs (perform jobs in parallel)
----------------------------

- Orientation (if requested by user)
  - Correct orientation
- Skew angle (if requested by user)
  - Correct skew angle
- Cleaning (if requested by user)
  - Clean image

Perform OCR (perform jobs in parallel)
-----------

- Perform OCR and save resulting hocr file for each respective page (perfom jobs in parallel)

Generate output for each page
-----------------------------

- For pdf (if output file has a "pdf" extension):
  - Generate pdf pages from hocr files (note: pdf pages can already exist if OCR has been skipped for them)
- For txt
  - generate txt file for each page (containing txt located into hocr file)

Build final output
------------------

- For pdf:
  - Concatenate pdf pages
  - Convert to pdf/1-a
  - Verify conformity to pdf/1-a
- For txt
  - Concatenate all txt files into the final output txt file



Tmp folder structure
=========================

- tmp_xxxxx/
  - a_raw_images (either from images or extracted from pdf file)
  - b_preprocessed_images (after deswing anf cleaning)
  - c_ocr_out
  - d_output_pages (one file per page (at first 1 pdf file per page. Later on other formats might be supported)
  - e_output_final (concatenate output pages and conversion into PDF/1-a standard, Later on support other formats)

ocrmypdf arguments
==================

ocrmypdf [-h] [-v] [-k] [-g] [-o dpi] [-f|-s] [-r] [-d] [-c] [-i] [-l lan1[+lan2...]] [-C] inputpath outputfile1 [outputfile2...]

- Overall parameters
  - [-h] : Display this help message
  - [-v] : Increase the verbosity (this option can be used more than once) (e.g. -vvv)
  - [-k] : Do not delete the temporary files
  - [-g] : Activate debug mode (max verbosity, keep tmp files, generate debug pages)
- Normalization parameters:
  - [-o dpi] : If page resolution is lower x dpi, provide OCR engine with an oversampled image. (Can improve OCR results)
  - [-f] : Force to OCR the whole document, even if some page already contain font data (only for pdf inputs)
  - [-s] : If pages contain font data, do not OCR that page, but include the page (as is) in the final output (only for pdf inputs)
- Prepocessing parameters:
  - [-r] : Correct orientation
  - [-d] : Deskew each page
  - [-c] : Clean each page
  - [-i] : Incorporate cleaned image in final output
- OCR parameters:
  - [-l lan1[+lan2...]] : Document language(s). Multiple languages may be specified, separated by '+' characters.
  - [-C cfg] : Pass an additional cofg file to the tesseract OCR engine. (this option can be used more than once)
- output generation parameters:
  - None by now
- input files:
  - inputpath : path to image, pdf file or folder to be processed
- output files:
  - outputfile1 [outputfile2 ...] : *.pdf file or *.txt file to be generated (argumenst can be repeated if both pdf and txt file should be generated 
