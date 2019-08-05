#! /bin/bash

HERE="$(dirname "$(readlink -f "${0}")")"

export PATH="$HERE/usr/bin:$HERE/usr/local/bin:$HERE/usr/python/bin:$PATH"
export LD_PRELOAD="$HERE/usr/lib/liblept.so.5"
export LD_LIBRARY_PATH="$HERE/usr/lib:$HERE/usr/lib/x86_64-linux-gnu:$LD_LIBRARY_PATH"
export TESSDATA_PREFIX="$HERE/usr/share/tesseract-ocr/4.00/tessdata"
export GS_LIB="$HERE/usr/share/ghostscript/9.26/lib:$HERE/usr/share/ghostscript/9.26/Resource:$HERE/usr/share/ghostscript/9.26/Resource/Init"

# Allow the AppImage to be symlinked to e.g., /usr/bin/commandname
# or called with ./Some*.AppImage commandname ...
# refer to https://github.com/AppImage/AppImageKit/wiki/Bundling-command-line-tools

if [ ! -z "$APPIMAGE" ] ; then
  BINARY_NAME=$(basename "$ARGV0")
else
  BINARY_NAME=$(basename "$0")
  export APPDIR="$HERE"       # required for the wrapper scripts of linuxdeploy-plugin-python
fi

usage() {
echo "
==============================================================================
                          AppImage for OCRmyPDF
==============================================================================
OCRmyPDF adds an OCR text layer to scanned PDF files, allowing them to be
searched or copy-pasted.

usage:
$ARGV0 [ocrmypdf] [--help] [--list-programs]
                                 [--list-licenses] [--show-license]

ocrmypdf                    execute OCRmyPDF

--help                      show this help message

--list-programs             list all programs contained in this AppImage

--list-licenses             list all licenses contained in this AppImage

--show-license [LICENSE]    show content of license file
"
}

if [ "$1" == "--help" ] ; then
    usage
    exit $?
fi

if [ "$1" == "--list-programs" ] ; then
    pushd "$HERE"
    echo ""
    echo "Run \"$ARGV0\" with one of the following arguments to run the respective program."
    echo ""
    find . -type f -perm /111 ! -path '*/lib/*' -execdir basename {} ";" | sort -u | column
    echo ""
    exit $?
fi

if [ "$1" == "--list-licenses" ] ; then
    pushd "$HERE"
    echo ""
    echo "Run \"$ARGV0\" with one of the following arguments to display the respective license file."
    echo ""
    find . -type f \( ! -path '*/tesseract-ocr-*' -o -path '*/tesseract-ocr-eng/*' \) \
        \( -iname "license*" -o -iname "*copyright*" -o -iname "*copying*" \) -printf "--show-license %P\n" | sort | column
    echo ""
    exit $?
fi

if [ "$1" == "--show-license" ] ; then
    pushd "$HERE"
    shift
    if [ -f "$1" ] ; then
        less -N "$1"
        exit $?
    else
        echo "\"$1\" is not a valid license file path."
        exit 1
    fi
fi

if [ ! -z "$1" ] && [ -e "$HERE/bin/$1" ] ; then
    MAIN="$HERE/bin/$1" ; shift
elif [ ! -z "$1" ] && [ -e "$HERE/usr/bin/$1" ] ; then
    MAIN="$HERE/usr/bin/$1" ; shift
elif [ ! -z "$1" ] && [ -e "$HERE/usr/python/bin/$1" ] ; then
    MAIN="$HERE/usr/python/bin/$1" ; shift
elif [ ! -z "$1" ] && [ -e "$HERE/usr/local/bin/$1" ] ; then
    MAIN="$HERE/usr/local/bin/$1" ; shift
elif [ -e "$HERE/bin/$BINARY_NAME" ] ; then
    MAIN="$HERE/bin/$BINARY_NAME"
elif [ -e "$HERE/usr/bin/$BINARY_NAME" ] ; then
    MAIN="$HERE/usr/bin/$BINARY_NAME"
elif [ -e "$HERE/usr/python/bin/$BINARY_NAME" ] ; then
    MAIN="$HERE/usr/python/bin/$BINARY_NAME"
elif [ -e "$HERE/usr/local/bin/$BINARY_NAME" ] ; then
    MAIN="$HERE/usr/local/bin/$BINARY_NAME"
else
    usage
    exit $?
fi

exec "${MAIN}" "$@"
