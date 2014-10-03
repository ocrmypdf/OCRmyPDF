Complete tool reimplementation in python
Segregate the processing into 5 main tasks

  - Normalization of inputs (inputs can be a pdf file, an image, a folder containing images)
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
  - Preprocessing of normalized inputs (perform jobs in parallel)
    - Orientation (if requested by user)
      - Correct orientation
    - Skew angle (if requested by user)
      - Correct skew angle
    - Cleaning (if requested by user)
      - Clean image
  - OCRing (perform jobs in parallel)
    - Perform OCR and save resulting hocr file for each respective page (perfom jobs in parallel)
  - Build output per page
    - For pdf (if output file has a "pdf" extension):
      - Generate pdf pages from hocr files (note: pdf pages can already exist if OCR has been skipped for them)
  - Build final output:
    - For pdf:
      - Concatenate pdf pages
      - Converte to pdf/1-a
      - Verify conformity to pdf/1-a
    

    
New temp folder structure:

  - tmp_xxxxx/
    - a_raw_images (either from images or extracted from pdf file)
      - page_<xxxx>.<extension>
    - b_preprocessed_images (after deswing anf cleaning)
      - page_<xxxx>.<extension>
    - c_hocr_files
      - page_<xxxx>.hocr
    - d_output_pages (one file per page (at first 1 pdf file per page. Later on other formats might be supported)
      - page_<xxxx>.<extension>
    - e_final_output (concatenate output pages and conversion into PDF/1-a standard, Later on support other formats)
      - final.<extension>
