#! /bin/bash

set -x
set -e

# use RAM disk if possible
if [ "$CI" == "" ] && [ -d /dev/shm ]; then
    TEMP_BASE=/dev/shm
else
    TEMP_BASE=/tmp
fi

BUILD_DIR=$(mktemp -d -p "$TEMP_BASE" OCRmyPDF-AppImage-build-XXXXXX)

cleanup () {
    if [ -d "$BUILD_DIR" ]; then
        rm -rf "$BUILD_DIR"
    fi
}

trap cleanup EXIT

# store repo root as variable
REPO_ROOT=$(readlink -f "$(dirname "$(dirname "$0")")")
OLD_CWD=$(readlink -f .)

pushd "$BUILD_DIR"

mkdir -p AppDir
mkdir -p PackageDir
mkdir -p jbig2

# download linuxdeploy AppImage and linuxdeploy-plugin-python AppImage
wget https://github.com/TheAssassin/linuxdeploy/releases/download/continuous/linuxdeploy-x86_64.AppImage
# wget https://github.com/niess/linuxdeploy-plugin-python/releases/download/continuous/linuxdeploy-plugin-python-x86_64.AppImage

# use adapted linuxdeploy-plugin-python instead of the original one (otherwise OCRmyPDF breaks)
wget https://github.com/FPille/linuxdeploy-plugin-python/releases/download/continuous/linuxdeploy-plugin-python-x86_64.AppImage

chmod +x linuxdeploy*.AppImage


ARCH=$(uname -i)
export ARCH


# .desktop file
cat > ocrmypdf.desktop <<\EOF
[Desktop Entry]
Name=ocrmypdf
Type=Application
Exec=ocrmypdf
Icon=ocrmypdf
Terminal=true
Comment=OCRmyPDF adds an OCR text layer to scanned PDF files, allowing them to be searched
Categories=Graphics;Scanning;OCR;
EOF


# download logo and convert it to desktop icon
# requires Imagemagick (convert)
wget https://raw.githubusercontent.com/jbarlow83/OCRmyPDF/master/docs/images/logo-social.png
convert logo-social.png -resize 512x512\> -size 512x512 xc:white +swap -gravity center -composite ocrmypdf.png


# download and intsall packages required by OCRmyPDF
pushd PackageDir
packages=(tesseract-ocr tesseract-ocr-all libavformat56 ghostscript qpdf pngquant)

for i in "${packages[@]}"
do
    apt-get -d -o dir::cache="$PWD" -o Debug::NoLocking=1 install "$i" -y
done

wget -q 'https://www.dropbox.com/s/vaq0kbwi6e6au80/unpaper_6.1-1.deb?raw=1' -O unpaper_6.1-1.deb

find . -type f -name \*.deb -exec dpkg-deb -X {} "$BUILD_DIR"/AppDir \;
popd


# compile and install jbig2
# requires libleptonica-dev, zlib1g-dev
wget -q https://github.com/agl/jbig2enc/archive/0.29.tar.gz -O - | \
     tar xz -C jbig2 --strip-components=1
pushd jbig2
./autogen.sh
./configure --prefix="$BUILD_DIR"/AppDir/usr
make && make install
popd


# remove unnecessary data from AppDir
pushd "$BUILD_DIR"/AppDir
[ -d etc ] && rm -rf ./etc
[ -d var ] && rm -rf ./var
popd


# export LD_LIBRARY_PATH so that dependencies of shared libraries can be deployed by linuxdeploy-x86_64.AppImage
export LD_LIBRARY_PATH="$BUILD_DIR/AppDir/usr/lib:$BUILD_DIR/AppDir/usr/lib/x86_64-linux-gnu:$LD_LIBRARY_PATH"

#OCRMYPDF_VERSION=8.3.2   # exported in .travis.yml file
export PIP_REQUIREMENTS="ocrmypdf==$OCRMYPDF_VERSION"
export VERSION="$OCRMYPDF_VERSION"
export OUTPUT=OCRmyPDF-"$VERSION"-"$ARCH".AppImage
export PYTHON_SOURCE=https://www.python.org/ftp/python/3.6.8/Python-3.6.8.tgz

./linuxdeploy-x86_64.AppImage --appdir AppDir --plugin python \
    -d ocrmypdf.desktop -i ocrmypdf.png \
    --custom-apprun "$REPO_ROOT"/appimage/AppRun.sh --output appimage


# move AppImage back to old CWD
mv "$OUTPUT" "$OLD_CWD"/

popd
