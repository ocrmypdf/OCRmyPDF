Complete tool reimplementation in python
Segregate the processing into 4 main tasks

  - Normalization of inputs. 
    - Inputs can be:
      - a PDF file
      - one or several images of any type
    - What preprocessing does:
      - In case of PDF file:
        - If the page needs to be OCRed:
          - Extract the image corresponding to the page and save it in a tmp folder. 3 approaches to extract the image:
            - extract raw image from pdf
            - if not possible: identify resolution and rasterize page
            - if not possible: use default resolution and rasterize
        - If not:
          - Save the page AS-IS in the tmp folder that should contained the final page
      - In case of separate images:
        - Just copy the images with standardized name into the tmp folder containing pages to be OCRed
  - Preprocessing of normalized inputs (perform jobs in parallel)
    - Identify orientation and skew angle
    - deskew / rotate image
    - Clean image
  - OCRing (perform jobs in parallel)
    - Just perform OCR in save resulting hocr file for each respective page (to be 
  - Build output (currently only PDF file generation will be supported)
    

    
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
