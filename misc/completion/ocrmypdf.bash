# SPDX-FileCopyrightText: 2021 Frank Pille
# SPDX-FileCopyrightText: 2020 Alex Willner
# SPDX-License-Identifier: MIT

set -o errexit

__ocrmypdf_arguments()
{
    local arguments="\
--help                          (show help message)
--language                      (language(s) of the file to be OCRed)
--image-dpi                     (assume this DPI if input image DPI is unknown)
--output-type                   (select PDF output options)
--sidecar                       (write OCR to text file)
--version                       (print program version and exit)
--jobs                          (how many worker processes to use)
--quiet                         (suppress INFO messages)
--verbose                       (set verbosity level)
--title                         (set metadata)
--author                        (set metadata)
--subject                       (set metadata)
--keywords                      (set metadata)
--rotate-pages                  (rotate pages to correct orientation)
--remove-background             (attempt to remove background from pages)
--deskew                        (fix small horizontal alignment skew)
--clean                         (clean document images before OCR)
--clean-final                   (clean document images and keep result)
--unpaper-args                  (a quoted string of arguments to pass to unpaper)
--oversample                    (oversample images to this DPI)
--remove-vectors                (don\'t send vector objects to OCR)
--threshold                     (threshold images before OCR)
--force-ocr                     (OCR documents that already have printable text)
--skip-text                     (skip OCR on any pages that already contain text)
--redo-ocr                      (redo OCR on any pages that seem to have OCR already)
--invalidate-digital-signatures (remove digital signatures from PDF)
--skip-big                      (skip OCR on pages larger than this many MPixels)
--optimize                      (select optimization level)
--jpeg-quality                  (JPEG quality [0..100])
--png-quality                   (PNG quality [0..100])
--jbig2-lossy                   (enable lossy JBIG2 (see docs))
--jbig2-threshold               (set JBIG2 threshold (see docs))
--pages                         (apply OCR to only the specified pages)
--max-image-mpixels             (image decompression bomb threshold)
--pdf-renderer                  (select PDF renderer options)
--rotate-pages-threshold        (page rotation confidence)
--pdfa-image-compression        (set PDF/A image compression options)
--fast-web-view                 (if file size if above this amount in MB linearize PDF)
--plugin                        (name of plugin to import)
--keep-temporary-files          (keep temporary files (debug)
--tesseract-config              (set custom tesseract config file)
--tesseract-pagesegmode         (set tesseract --psm)
--tesseract-oem                 (set tesseract --oem)
--tesseract-thresholding        (set tesseract image thresholding)
--tesseract-timeout             (maximum number of seconds to wait for OCR)
--user-words                    (specify location of user words file)
--user-patterns                 (specify location of user patterns file)
--no-progress-bar               (disable the progress bar)
--color-conversion-strategy     (select color conversion strategy)
"

    COMPREPLY=( $( compgen -W "$arguments" -- "$cur") )

    # Remove description if only one completion exists
    if [[ ${#COMPREPLY[*]} -eq 1 ]]; then
        COMPREPLY=( ${COMPREPLY[0]%% *} )
    fi
}

__ocrmypdf_output-type()
{
    local choices="pdfa   (output a PDF/A (default))
pdf    (output a standard PDF)
pdfa-1 (output a PDF/A-1b)
pdfa-2 (output a PDF/A-2b)
pdfa-3 (output a PDF/A-3b)
none   (do not produce an output PDF (for example, if you only care about --sidecar))"

    COMPREPLY=( $( compgen -W "$choices" -- "$cur") )

    # Remove description if only one completion exists
    if [[ ${#COMPREPLY[*]} -eq 1 ]]; then
        COMPREPLY=( ${COMPREPLY[0]%% *} )
    fi
}

__ocrmypdf_verbose()
{
    local choices="0  (standard output messages)
1  (troubleshooting output messages)
2  (debugging output messages)"

    COMPREPLY=( $( compgen -W "$choices" -- "$cur") )

    # Remove description if only one completion exists
    if [[ ${#COMPREPLY[*]} -eq 1 ]]; then
        COMPREPLY=( ${COMPREPLY[0]%% *} )
    fi
}

__ocrmypdf_optimize()
{
    local choices="0  (do not optimize)
1  (do safe, lossless optimizations (default))
2  (do some lossy optimizations)
3  (do aggressive lossy optimizations (including lossy JBIG2))"

    COMPREPLY=( $( compgen -W "$choices" -- "$cur") )

    # Remove description if only one completion exists
    if [[ ${#COMPREPLY[*]} -eq 1 ]]; then
        COMPREPLY=( ${COMPREPLY[0]%% *} )
    fi
}

__ocrmypdf_pdf-renderer()
{
    local choices="auto      (auto select PDF renderer)
hocr      (use hOCR renderer)
hocrdebug (uses hOCR renderer in debug mode, showing recognized text)
sandwich  (use sandwich renderer)"

    COMPREPLY=( $( compgen -W "$choices" -- "$cur") )

    # Remove description if only one completion exists
    if [[ ${#COMPREPLY[*]} -eq 1 ]]; then
        COMPREPLY=( ${COMPREPLY[0]%% *} )
    fi
}

__ocrmypdf_pdfa-image-compression()
{
    local choices="auto     (let Ghostscript decide how to compress images)
jpeg     (convert color and grayscale images to JPEG)
lossless (convert color and grayscale images to lossless (PNG))"

    COMPREPLY=( $( compgen -W "$choices" -- "$cur") )

    # Remove description if only one completion exists
    if [[ ${#COMPREPLY[*]} -eq 1 ]]; then
        COMPREPLY=( ${COMPREPLY[0]%% *} )
    fi
}

__ocrmypdf_tesseract-pagesegmode()
{
    local choices="0  (orientation and script detection (OSD) only)
1  (automatic page segmentation with OSD)
2  (automatic page segmentation, but no OSD, or OCR)
3  (fully automatic page segmentation, but no OSD (default))
4  (assume a single column of text of variable sizes)
5  (assume a single uniform block of vertically aligned text)
6  (assume a single uniform block of text)
7  (treat the image as a single text line)
8  (treat the image as a single word)
9  (treat the image as a single word in a circle)
10 (treat the image as a single character)
11 (sparse text - find as much text as possible in no particular order)
12 (sparse text with OSD)
13 (raw line - treat the image as a single text line)"

    COMPREPLY=( $( compgen -W "$choices" -- "$cur") )

    # Remove description if only one completion exists
    if [[ ${#COMPREPLY[*]} -eq 1 ]]; then
        COMPREPLY=( ${COMPREPLY[0]%% *} )
    fi
}

__ocrmypdf_tesseract-oem()
{
    local choices="0 (legacy engine only)
1 (neural nets LSTM engine only)
2 (legacy + LSTM engines)
3 (default, based on what is available)"

    COMPREPLY=( $( compgen -W "$choices" -- "$cur") )

    # Remove description if only one completion exists
    if [[ ${#COMPREPLY[*]} -eq 1 ]]; then
        COMPREPLY=( ${COMPREPLY[0]%% *} )
    fi
}

__ocrmypdf_tesseract-thresholding()
{
    local choices="auto          (let OCRmyPDF pick thresholding - current always uses otsu)
otsu          (use hOCR renderer)
adaptive-otsu (use adaptive Otsu thresholding)
sauvola       (use Sauvola thresholding)"

    COMPREPLY=( $( compgen -W "$choices" -- "$cur") )
    # Remove description if only one completion exists
    if [[ ${#COMPREPLY[*]} -eq 1 ]]; then
        COMPREPLY=( ${COMPREPLY[0]%% *} )
    fi
}

__ocrmypdf_color-conversion-strategy()
{
    local choices="LeaveColorUnchanged (default)
CMYK (convert to CMYK)
Gray (convert to grayscale)
RGB (convert to RGB)
UseDeviceIndependentColor (convert with device independent color)"

    COMPREPLY=( $( compgen -W "$choices" -- "$cur") )
    # Remove description if only one completion exists
    if [[ ${#COMPREPLY[*]} -eq 1 ]]; then
        COMPREPLY=( ${COMPREPLY[0]%% *} )
    fi
}

__ocrmypdf_check_previous()
{
    case $prev in
        -h|--help|--version)
            return 0
            ;;
        -l|--language)
            COMPREPLY=$( command tesseract --list-langs 2>/dev/null )
            COMPREPLY=( $( compgen -W '${COMPREPLY[@]##*:}' -- "$cur" ) )
            return 0
            ;;
        --output-type)
            __ocrmypdf_output-type
            return 0
            ;;
        -j|--jobs)
            COMPREPLY=( $( compgen -W '{1..'$( _ncpus )'}' -- "$cur" ) )
            return 0
            ;;
        -v|--verbose)
            __ocrmypdf_verbose
            return 0
            ;;
        -O|--optimize)
            __ocrmypdf_optimize
            return 0
            ;;
        --pdf-renderer)
            __ocrmypdf_pdf-renderer
            return 0
            ;;
        --pdfa-image-compression)
            __ocrmypdf_pdfa-image-compression
            return 0
            ;;
        --tesseract-pagesegmode)
            __ocrmypdf_tesseract-pagesegmode
            return 0
            ;;
        --tesseract-oem)
            __ocrmypdf_tesseract-oem
            return 0
            ;;
        --tesseract-thresholding)
            __ocrmypdf_tesseract-thresholding
            return 0
            ;;

        --title|--author|--subject|--keywords|--unpaper-args|--pages|--plugin|\
        --jpeg-quality|--png-quality|--image-dpi|--oversample|--skip-big|--max-image-mpixels|\
        --tesseract-timeout|--rotate-pages-threshold|--fast-web-view)
            # argument required but no completions available
            return 0
            ;;
        --tesseract-config|--user-words|--user-patterns|--sidecar)
            _filedir
            return 0
            ;;
        --color-conversion-strategy)
            __ocrmypdf_color-conversion-strategy
            return 0
            ;;
    esac

    return 1
}

_ocrmypdf()
{
    local OLDIFS="$IFS"
    local IFS=$'\n'

    local cur prev

    # Homebrew on Macs have version 1.3 of bash-completion which doesn't include - see #502
    if declare -F _init_completion >/dev/null 2>&1; then
      _init_completion  || return
    else
        COMPREPLY=()
        _get_comp_words_by_ref cur prev
    fi

    if __ocrmypdf_check_previous -ne 0; then
        return
    fi

    if [[ "$cur" == -* ]]; then
        __ocrmypdf_arguments
    else
        _filedir
    fi

    IFS="$OLDIFS"

    return
} &&
complete -F _ocrmypdf ocrmypdf

set +o errexit

# ex: filetype=sh
