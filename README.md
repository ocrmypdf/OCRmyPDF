# OCRmyPDF-AppImage  [![Build Status](https://travis-ci.com/FPille/OCRmyPDF-AppImage.svg?branch=master)](https://travis-ci.com/FPille/OCRmyPDF-AppImage)
[AppImage][APPIMAGE] for [OCRmyPDF][OCRMYPDF]

## Usage
Download OCRmyPDF*.AppImage, make it executable and run it.
```
wget https://github.com/FPille/OCRmyPDF-AppImage/releases/download/continuous/OCRmyPDF-8.3.2-x86_64.AppImage
chmod +x OCRmyPDF*.AppImage
./OCRmyPDF*.AppImage --help
```  
  
  Beside OCRmyPDF additional command line programs can be run with this AppImage like:
* ghostscript
* img2pdf
* pngquant
* python3.6
* qpdf
* tesseract
* unpaper  

Just use the program name as first parameter plus options:
```
./OCRmyPDF*.AppImage tesseract -v
tesseract 4.1.0
 leptonica-1.76.0
  libjpeg 8d (libjpeg-turbo 1.3.0) : libpng 1.2.50 : libtiff 4.0.3 : zlib 1.2.11 : libwebp 0.4.0 : libopenjp2 2.3.0
 Found AVX2
 Found AVX
 Found SSE
```
Or create a symlink for the corresponding program:
```
ln -s OCRmyPDF*.AppImage tesseract
./tesseract --list-langs
```


[APPIMAGE]: https://appimage.org
[OCRMYPDF]: https://github.com/jbarlow83/OCRmyPDF

