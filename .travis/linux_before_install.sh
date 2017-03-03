#!/bin/bash
set -euo pipefail
set -x

sudo add-apt-repository ppa:vshn/ghostscript -y
sudo add-apt-repository ppa:heyarje/libav-11 -y
sudo apt-get update -qq
sudo apt-get install -y \
	ghostscript \
	tesseract-ocr \
	tesseract-ocr-deu \
	tesseract-ocr-eng \
	tesseract-ocr-fra \
	qpdf \
	poppler-utils \
	libavformat56 \
	libavcodec56 \
	libavutil54 \
	libffi-dev

pip install --upgrade pip
mkdir -p packages
[ -f packages/unpaper_6.1-1.deb ] || wget -q https://dl.dropboxusercontent.com/u/28971240/unpaper_6.1-1.deb -O packages/unpaper_6.1-1.deb
sudo dpkg -i packages/unpaper_6.1-1.deb
