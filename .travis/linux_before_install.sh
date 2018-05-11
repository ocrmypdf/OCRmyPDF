#!/bin/bash
# © 2017 James R. Barlow: github.com/jbarlow83
set -euo pipefail
set -x

pip install --upgrade pip
mkdir -p packages
wget -q 'https://www.dropbox.com/s/vaq0kbwi6e6au80/unpaper_6.1-1.deb?raw=1' -O packages/unpaper_6.1-1.deb
sudo dpkg -i packages/unpaper_6.1-1.deb

if [ ! -f /usr/local/bin/qpdf ]; then
	export QPDF_RELEASE='https://github.com/qpdf/qpdf/releases/download/release-qpdf-8.0.2/qpdf-8.0.2.tar.gz'
	mkdir qpdf
    wget -q $QPDF_RELEASE -O - | tar xz -C qpdf --strip-components=1
    cd qpdf/
	export PATH="/usr/local/opt/ccache/libexec:$PATH"
    ./configure --prefix=/usr
    make -j 2
    sudo make install
    cd ..
fi
