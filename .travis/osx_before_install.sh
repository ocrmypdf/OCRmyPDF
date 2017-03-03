#!/bin/bash
set -euo pipefail
set -x

brew update

brew install openjpeg jbig2dec libtiff     # image libraries
brew install qpdf
brew install ghostscript
brew install python3
brew install libxml2 libffi leptonica
brew install unpaper   # optional
brew install tesseract

pip3 install --upgrade pip
pip3 install wheel
