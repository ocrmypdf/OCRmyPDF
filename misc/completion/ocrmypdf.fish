complete -c ocrmypdf -l version
complete -c ocrmypdf -l help

complete -c ocrmypdf -l sidecar -r -d "write OCR to text file"
complete -c ocrmypdf -s q -l quiet

complete -c ocrmypdf -s r -l rotate-pages -d "rotate pages to correct orientation"
complete -c ocrmypdf -s d -l deskew -d "fix small horizontal alignment skew"
complete -c ocrmypdf -s c -l clean -d "clean document images before OCR"
complete -c ocrmypdf -s i -l clean-final -d "clean document images and keep result"
complete -c ocrmypdf -l remove-vectors -d "don't send vector objects to OCR"
complete -c ocrmypdf -l mask-barcodes -d "mask barcodes from OCR"
complete -c ocrmypdf -l threshold -d "threshold images before OCR"

complete -c ocrmypdf -s f -l force-ocr -d "OCR documents that already have printable text"
complete -c ocrmypdf -s s -l skip-ocr -d "skip OCR on pages that text, otherwise try OCR"
complete -c ocrmypdf -l redo-ocr -d "redo OCR on any pages that seem to have OCR already"

complete -c ocrmypdf -s k -l keep-temporary-files -d "keep temporary files (debug)"

complete -c ocrmypdf -x -s l -l language -d 'language'
complete -c ocrmypdf -x -s l -l language -a '(tesseract --list-langs)'

complete -c ocrmypdf -x -l image-dpi -d "assume this DPI if input image DPI is unknown"

function __fish_ocrmypdf_output_type
    echo -e "pdfa\t"(_ "output a PDF/A (default)")
    echo -e "pdf\t"(_ "output a standard PDF")
    echo -e "pdfa-1\t"(_ "output a PDF/A-1b")
    echo -e "pdfa-2\t"(_ "output a PDF/A-2b")
    echo -e "pdfa-3\t"(_ "output a PDF/A-3b")
end
complete -c ocrmypdf -x -l output-type -a '(__fish_ocrmypdf_output_type)' -d "select PDF output options"

function __fish_ocrmypdf_pdf_renderer
    echo -e "auto\t"(_ "auto select PDF renderer")
    echo -e "hocr\t"(_ "use hocr renderer")
    echo -e "sandwich\t"(_ "use sandwich renderer")
end
complete -c ocrmypdf -x -l pdf-render -a '(__fish_ocrmypdf_pdf_renderer)' -d "select PDF renderer options"

function __fish_ocrmypdf_optimize
    echo -e "0\t"(_ "do not optimize")
    echo -e "1\t"(_ "do safe, lossless optimizations (default)")
    echo -e "2\t"(_ "do some lossy optimizations")
    echo -e "3\t"(_ "do aggressive lossy optimizations (including lossy JBIG2)")
end
complete -c ocrmypdf -x -s O -l optimize -a '(__fish_ocrmypdf_optimize)' -d "select optimization level"

complete -c ocrmypdf -x -s j -l jobs -d "how many worker processes to use"
complete -c ocrmypdf -x -s v -a '(seq 1 9)'
complete -c ocrmypdf -x -l title -d "set metadata"
complete -c ocrmypdf -x -l author -d "set metadata"
complete -c ocrmypdf -x -l subject -d "set metadata"
complete -c ocrmypdf -x -l keywords -d "set metadata"
complete -c ocrmypdf -x -l oversample -d "oversample images to this DPI"
complete -c ocrmypdf -x -l skip-big -d "skip OCR on pages larger than this many MPixels"

complete -c ocrmypdf -x -l jpeg-quality -d "JPEG quality [0..100]"
complete -c ocrmypdf -x -l png-quality -d "PNG quality [0..100]"
complete -c ocrmypdf -x -l jbig2-lossy -d "enable lossy JBIG2 (see docs)"
complete -c ocrmypdf -x -l max-image-mpixels -d "image decompression bomb threshold"
complete -c ocrmypdf -x -l tesseract-config -d "set custom tesseract config file"
complete -c ocrmypdf -x -l tesseract-pagesegmode -d "set tesseract --psm"
complete -c ocrmypdf -x -l tesseract-oem -d "set tesseract --oem"
complete -c ocrmypdf -x -l tesseract-timeout -d "maximum number of seconds to wait for OCR"
complete -c ocrmypdf -x -l rotate-pages-threshold -d "page rotation confidence"
complete -c ocrmypdf -x -l pdfa-image-compression -a 'auto jpeg lossless' -d "set PDF/A image compression options"

complete -c ocrmypdf -x -a "(__fish_complete_suffix .pdf)"
