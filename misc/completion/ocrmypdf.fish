# SPDX-FileCopyrightText: 2022 James R. Barlow
# SPDX-License-Identifier: MIT

complete -c ocrmypdf -x -n __fish_is_first_arg -l version
complete -c ocrmypdf -x -n __fish_is_first_arg -s h -s "?" -l help

complete -c ocrmypdf -r -l sidecar -d "write OCR to text file"
complete -c ocrmypdf -x -s q -l quiet

complete -c ocrmypdf -s r -l rotate-pages -d "rotate pages to correct orientation"
complete -c ocrmypdf -s d -l deskew -d "fix small horizontal alignment skew"
complete -c ocrmypdf -s c -l clean -d "clean document images before OCR"
complete -c ocrmypdf -s i -l clean-final -d "clean document images and keep result"
complete -c ocrmypdf -l remove-vectors -d "don't send vector objects to OCR"

complete -c ocrmypdf -s f -l force-ocr -d "OCR documents that already have printable text"
complete -c ocrmypdf -s s -l skip-text -d "skip OCR on any pages that already contain text"
complete -c ocrmypdf -l redo-ocr -d "redo OCR on any pages that seem to have OCR already"
complete -c ocrmypdf -l invalidate-digital-signatures -d "invalidate digital signatures and allow OCR to proceed"

complete -c ocrmypdf -s k -l keep-temporary-files -d "keep temporary files (debug)"

function __fish_ocrmypdf_languages
    set langs (tesseract --list-langs ^/dev/null)
    set arr (string split '\n' $langs)
    for lang in $arr[2..-1]
        echo $lang
    end
end
complete -c ocrmypdf -x -s l -l language -a '(__fish_ocrmypdf_languages)' -d language

complete -c ocrmypdf -x -l image-dpi -d "assume this DPI if input image DPI is unknown"

function __fish_ocrmypdf_output_type
    echo -e "pdfa\t"(_ "output a PDF/A (default)")
    echo -e "pdf\t"(_ "output a standard PDF")
    echo -e "pdfa-1\t"(_ "output a PDF/A-1b")
    echo -e "pdfa-2\t"(_ "output a PDF/A-2b")
    echo -e "pdfa-3\t"(_ "output a PDF/A-3b")
    echo -e "none\t"(_ "do not produce an output PDF (for example, if you only care about --sidecar)")
end
complete -c ocrmypdf -x -l output-type -a '(__fish_ocrmypdf_output_type)' -d "select PDF output options"

function __fish_ocrmypdf_pdf_renderer
    echo -e "auto\t"(_ "auto select PDF renderer")
    echo -e "hocr\t"(_ "use hOCR renderer")
    echo -e "hocrdebug\t"(_ "uses hOCR renderer in debug mode, showing recognized text")
    echo -e "sandwich\t"(_ "use sandwich renderer")
end
complete -c ocrmypdf -x -l pdf-renderer -a '(__fish_ocrmypdf_pdf_renderer)' -d "select PDF renderer options"

function __fish_ocrmypdf_optimize
    echo -e "0\t"(_ "do not optimize")
    echo -e "1\t"(_ "do safe, lossless optimizations (default)")
    echo -e "2\t"(_ "do some lossy optimizations")
    echo -e "3\t"(_ "do aggressive lossy optimizations (including lossy JBIG2)")
end
complete -c ocrmypdf -x -s O -l optimize -a '(__fish_ocrmypdf_optimize)' -d "select optimization level"

function __fish_ocrmypdf_verbose
    echo -e "0\t"(_ "standard output messages")
    echo -e "1\t"(_ "troubleshooting output messages")
    echo -e "2\t"(_ "debugging output messages")
end
complete -c ocrmypdf -x -s v -l verbose -a '(__fish_ocrmypdf_verbose)' -d "set verbosity level"

complete -c ocrmypdf -x -l no-progress-bar -d "disable the progress bar"

function __fish_ocrmypdf_pdfa_compression
    echo -e "auto\t"(_ "let Ghostscript decide how to compress images")
    echo -e "jpeg\t"(_ "convert color and grayscale images to JPEG")
    echo -e "lossless\t"(_ "convert color and grayscale images to lossless (PNG)")
end
complete -c ocrmypdf -x -l pdfa-image-compression -a '(__fish_ocrmypdf_pdfa_compression)' -d "set PDF/A image compression options"

complete -c ocrmypdf -x -s j -l jobs -d "how many worker processes to use"
complete -c ocrmypdf -x -l title -d "set metadata"
complete -c ocrmypdf -x -l author -d "set metadata"
complete -c ocrmypdf -x -l subject -d "set metadata"
complete -c ocrmypdf -x -l keywords -d "set metadata"
complete -c ocrmypdf -x -l oversample -d "oversample images to this DPI"
complete -c ocrmypdf -x -l skip-big -d "skip OCR on pages larger than this many MPixels"

complete -c ocrmypdf -x -l jpeg-quality -d "JPEG quality [0..100]"
complete -c ocrmypdf -x -l png-quality -d "PNG quality [0..100]"
complete -c ocrmypdf -x -l jbig2-lossy -d "enable lossy JBIG2 (see docs)"
complete -c ocrmypdf -x -l jbig2-threshold -d "JBIG2 compression threshold (see docs)"
complete -c ocrmypdf -x -l max-image-mpixels -d "image decompression bomb threshold"
complete -c ocrmypdf -x -l pages -d "apply OCR to only the specified pages"
complete -c ocrmypdf -x -l tesseract-config -d "set custom tesseract config file"

function __fish_ocrmypdf_tesseract_pagesegmode
    echo -e "0\t"(_ "orientation and script detection (OSD) only")
    echo -e "1\t"(_ "automatic page segmentation with OSD")
    echo -e "2\t"(_ "automatic page segmentation, but no OSD, or OCR")
    echo -e "3\t"(_ "fully automatic page segmentation, but no OSD (default)")
    echo -e "4\t"(_ "assume a single column of text of variable sizes")
    echo -e "5\t"(_ "assume a single uniform block of vertically aligned text")
    echo -e "6\t"(_ "assume a single uniform block of text")
    echo -e "7\t"(_ "treat the image as a single text line")
    echo -e "8\t"(_ "treat the image as a single word")
    echo -e "9\t"(_ "treat the image as a single word in a circle")
    echo -e "10\t"(_ "treat the image as a single character")
    echo -e "11\t"(_ "sparse text - find as much text as possible in no particular order")
    echo -e "12\t"(_ "sparse text with OSD")
    echo -e "13\t"(_ "raw line - treat the image as a single text line")
end
complete -c ocrmypdf -x -l tesseract-pagesegmode -a '(__fish_ocrmypdf_tesseract_pagesegmode)' -d "set tesseract --psm"

function __fish_ocrmypdf_tesseract_oem
    echo -e "0\t"(_ "legacy engine only")
    echo -e "1\t"(_ "neural nets LSTM engine only")
    echo -e "2\t"(_ "legacy + LSTM engines")
    echo -e "3\t"(_ "default, based on what is available")
end
complete -c ocrmypdf -x -l tesseract-oem -a '(__fish_ocrmypdf_tesseract_oem)' -d "set tesseract --oem"

function __fish_ocrmypdf_tesseract_thresholding
    echo -e "auto\t"(_ "let OCRmyPDF pick thresholding (current always uses otsu)")
    echo -e "otsu\t"(_ "legacy Otsu thresholding")
    echo -e "adaptive-otsu\t"(_ "use adaptive Otsu thresholding")
    echo -e "sauvola\t"(_ "use Sauvola thresholding")
end
complete -c ocrmypdf -x -l tesseract-thresholding -a '(__fish_ocrmypdf_tesseract_thresholding)' -d "set tesseract thresholding method (needs Tesseract 5.x)"

complete -c ocrmypdf -x -l tesseract-timeout -d "maximum number of seconds to wait for OCR"
complete -c ocrmypdf -x -l rotate-pages-threshold -d "page rotation confidence"

complete -c ocrmypdf -r -l user-words -d "specify location of user words file"
complete -c ocrmypdf -r -l user-patterns -d "specify location of user patterns file"
complete -c ocrmypdf -x -l fast-web-view -d "if file size if above this amount in MB, linearize PDF"

function __fish_ocrmypdf_color_conversion_strategy
    echo -e "LeaveColorUnchanged\t"(_ "do not convert color spaces (default)")
    echo -e "CMYK\t"(_ "convert all color spaces to CMYK")
    echo -e "Gray\t"(_ "convert all color spaces to grayscale")
    echo -e "RGB\t"(_ "convert all color spaces to RGB")
    echo -e "UseDeviceIndependentColor\t"(_ "convert all color spaces to ICC-based color spaces")
end

complete -c ocrmypdf -x -l color-conversion-strategy -a '(__fish_ocrmypdf_color_conversion_strategy)' -d "set color conversion strategy"

function __fish_ocrmypdf_input_file_given
    set -l tokens (commandline -opc)
    for token in $tokens
        if string match -q -r '^-' -- $token
            continue
        end
        if test -f "$token"
            return 0
        end
    end
    return 1
end

complete -c ocrmypdf -x -n 'not __fish_ocrmypdf_input_file_given' -a "(__fish_complete_suffix .pdf)" -d "input file"
