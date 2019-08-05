#! /bin/bash

set -x
set -e

chmod +x OCRmyPDF*.AppImage

# run OCRmyPDF to test if the AppImage can ocr a test file
run_appimage()
{
    echo ""
    ./OCRmyPDF*.AppImage --help
    echo ""
    ./OCRmyPDF*.AppImage --list-programs
    echo ""
    ./OCRmyPDF*.AppImage --list-licenses
    echo ""
    ./OCRmyPDF*.AppImage ocrmypdf -l deu -s -d --jbig2-lossy --optimize 1 "$TRAVIS_BUILD_DIR"/test/test.pdf output.pdf
    echo ""
}


# check AppImage for common issues
run_appimagelint()
{
    wget https://github.com/TheAssassin/appimagelint/releases/download/continuous/appimagelint-x86_64.AppImage
    chmod +x appimagelint-x86_64.AppImage
    ./appimagelint-x86_64.AppImage OCRmyPDF*.AppImage
}


# extract the OCRmyPDF AppImage, install pytest & test requirements and run pytest
run_pytest()
{
    git clone --depth=1 --branch "v$OCRMYPDF_VERSION" https://github.com/jbarlow83/OCRmyPDF.git
    ./OCRmyPDF*.AppImage --appimage-extract

    pushd squashfs-root
    ./AppRun python3 -m pip install pytest
    ./AppRun python3 -m pip install -r ../OCRmyPDF/requirements/test.txt
    ./AppRun python3 -m pytest ../OCRmyPDF -n auto
    popd
}


run_appimage

run_appimagelint

# run_pytest



