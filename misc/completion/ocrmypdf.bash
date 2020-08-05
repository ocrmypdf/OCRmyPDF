# ocrmypdf completion                                     -*- shell-script -*-

# Copyright 2019 Frank Pille
# Copyright 2020 Alex Willner
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

set -o errexit

_ocrmypdf()
{
    local cur prev cword words split

    # Homebrew on Macs have version 1.3 of bash-completion which doesn't include - see #502
    if declare -F _init_completions >/dev/null 2>&1; then
        _init_completion -s || return
    else
        COMPREPLY=()
        _get_comp_words_by_ref cur prev words cword
    fi

    if [[ $cur == -* ]]; then
        COMPREPLY=( $( compgen -W '--language --image-dpi --output-type
            --sidecar --version --jobs --quiet --verbose --title --author
            --subject --keywords --rotate-pages --remove-background --deskew
            --clean --clean-final --unpaper-args --oversample --remove-vectors
            --threshold --force-ocr --skip-text --redo-ocr
            --skip-big --jpeg-quality --png-quality --jbig2-lossy
            --max-image-mpixels --tesseract-config --tesseract-pagesegmode
            --help --tesseract-oem --pdf-renderer --tesseract-timeout
            --rotate-pages-threshold --pdfa-image-compression --user-words
            --user-patterns --keep-temporary-files --output-type
            --no-progress-bar --pages --fast-web-view' \
            --  "$cur" ) )
        return
    else
        _filedir
        return
    fi

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
            COMPREPLY=( $( compgen -W '{0..2}' -- "$cur" ) ) # max level ?
            return
            ;;
        --tesseract-pagesegmode)
            COMPREPLY=( $( compgen -W '{1..13}' -- "$cur" ) )
            return
            ;;
        --sidecar|--title|--author|--subject|--keywords|--unpaper-args|--pages|--fast-web-view)
            # argument required but no completions available
            return
            ;;
    esac

    $split && return
} &&
complete -F _ocrmypdf ocrmypdf

set +o errexit

# ex: filetype=sh
