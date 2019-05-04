# ocrmypdf completion                                     -*- shell-script -*-

_ocrmypdf()
{
    local cur prev cword words split
    _init_completion -s || return

    case $prev in
        --version|-h|--help)
            return
            ;;
        --user-words|--user-patterns|--tesseract-config)
            _filedir
            return
            ;;
        --output-type)
            COMPREPLY=( $( compgen -W 'pdfa pdf pdfa-1 pdfa-2 pdfa-3' -- \
                "$cur" ) )
            return
            ;;
        --pdf-renderer)
            COMPREPLY=( $( compgen -W 'auto hocr sandwich' -- "$cur" ) )
            return
            ;;
        --pdfa-image-compression)
            COMPREPLY=( $( compgen -W 'auto jpeg lossless' -- "$cur" ) )
            return
            ;;
        -O|--optimize|--tesseract-oem)
            COMPREPLY=( $( compgen -W '{0..3}' -- "$cur" ) )
            return
            ;;
        --jpeg-quality|--png-quality)
            COMPREPLY=( $( compgen -W '{0..100}' -- "$cur" ) )
            return
            ;;
        -l|--language)
            COMPREPLY=$( command tesseract --list-langs 2>/dev/null )
            COMPREPLY=( $( compgen -W '${COMPREPLY[@]##*:}' -- "$cur" ) )
            return
            ;;
        --image-dpi|--oversample|--skip-big|--max-image-mpixels|\
        --tesseract-timeout|--rotate-pages-threshold)
            COMPREPLY=( $( compgen -P "$cur" -W '{0..9}' ) )
            return
            ;;
        -j|--jobs)
            COMPREPLY=( $( compgen -W '{1..'$( _ncpus )'}' -- "$cur" ) )
            return
            ;;
        -v|--verbose)
            COMPREPLY=( $( compgen -W '{1..9}' -- "$cur" ) ) # max level ?
            return
            ;;
        --tesseract-pagesegmode)
            COMPREPLY=( $( compgen -W '{1..13}' -- "$cur" ) )
            return
            ;;
        --sidecar|--title|--author|--subject|--keywords|--unpaper-args)
            # argument required but no completions available
            return
            ;;
    esac

    $split && return

    if [[ $cur == -* ]]; then
        COMPREPLY=( $( compgen -W '--language --image-dpi --output-type
            --sidecar --version --jobs --quiet --verbose --title --author
            --subject --keywords --rotate-pages --remove-background --deskew
            --clean --clean-final --unpaper-args --oversample --remove-vectors
            --mask-barcodes --threshold --force-ocr --skip-text --redo-ocr
            --skip-big --jpeg-quality --png-quality --jbig2-lossy
            --max-image-mpixels --tesseract-config --tesseract-pagesegmode
            --help --tesseract-oem --pdf-renderer --tesseract-timeout
            --rotate-pages-threshold --pdfa-image-compression --user-words
            --user-patterns --keep-temporary-files --flowchart --output-type' \
            --  "$cur" ) )
        return
    else
        _filedir
        return
    fi
} &&
complete -F _ocrmypdf ocrmypdf

# ex: filetype=sh
