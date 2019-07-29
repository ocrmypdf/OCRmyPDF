#! /bin/bash

# TODO: Add "usage" ouput and additional functions like displaying of licences
#       and man pages
#       could be in a similar manner as the AppRun script of qpdf AppImage
#       refer to: https://github.com/qpdf/qpdf/blob/master/appimage/AppRun

HERE="$(dirname "$(readlink -f "${0}")")"

export PATH="$HERE/usr/bin:$HERE/usr/local/bin:$HERE/usr/python/bin:$PATH"
export LD_PRELOAD="$HERE/usr/lib/liblept.so.5"
export LD_LIBRARY_PATH="$HERE/usr/lib:$HERE/usr/lib/x86_64-linux-gnu:$LD_LIBRARY_PATH"
export TESSDATA_PREFIX="$HERE/usr/share/tesseract-ocr/4.00/tessdata"
export GS_LIB="$HERE/usr/share/ghostscript/9.26/lib:$HERE/usr/share/ghostscript/9.26/Resource:$HERE/usr/share/ghostscript/9.26/Resource/Init"

# Allow the AppImage to be symlinked to e.g., /usr/bin/commandname
# or called with ./Some*.AppImage commandname ...
# refer to https://github.com/AppImage/AppImageKit/wiki/Bundling-command-line-tools

if [ ! -z $APPIMAGE ] ; then
  BINARY_NAME=$(basename "$ARGV0")
else
  BINARY_NAME=$(basename "$0")
  export APPDIR="$HERE"       # required for the wrapper scripts of linuxdeploy-plugin-python
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
  MAIN="$HERE/usr/python/bin/ocrmypdf"
fi

exec "${MAIN}" "$@"
