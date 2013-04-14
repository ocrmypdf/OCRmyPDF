#!/bin/sh
echo "usage: ./scan-archive.sh filename.pdf"

LAN="eng"
KEEP_TMP="1"

infile="$1"

tmp="./tmp"
FILE_SIZEPAGES="$tmp/infile-page-sizes.txt"

# delete tmp files
rm -r -f "${tmp}"
mkdir -p "${tmp}"

# get the size of each pdf page (width / height) in pt (inch*72)
echo "Extracting size of each page (in pt)"
identify -format "%w %h\n" "$infile" > "$FILE_SIZEPAGES"
sed -I "" '/^$/d' "$FILE_SIZEPAGES"	# removing empty lines (last one should be)
numpages=`cat "$FILE_SIZEPAGES" | wc -l`
echo "PDF file has $numpages pages"

# Itterate the pages of the pdf file
page="1"
cat "$FILE_SIZEPAGES" | while read pageSize ; do

	echo "Page $page: Computing embedded image resolution"
	# get width / height of PDF page
	heightPDF=`echo $pageSize | cut -f1 -d" "`
	widthPDF=`echo $pageSize | cut -f2 -d" "`
	# extract raw image from pdf file to compute resolution
	# unfortunatelly this image may not be rotated as in the pdf...
	# so we will have to extract it again later
	pdfimages -f $page -l $page -j "$infile" "$tmp/${page}_orig" 1>&2	
	# count number of extracted images
	nbImg=`ls -1 "$tmp/${page}_orig"* | wc -l`
	[ $nbImg -ne "1" ] && echo "Not exactly 1 image on page $page. Exiting" && exit 1
	# Get the characteristic of the extracted image
	origImg=`ls -1 "$tmp/${page}_orig"*`
	origImg_woext=`echo "$origImg" | sed 's/\.[^.]*$//'`
	origImg_ext=`echo "$origImg" | sed 's/^.*[.]//'`
	propImg=`identify -format "%w %h %[colorspace]" "$origImg"`
	heightImg=`echo "$propImg" | cut -f1 -d" "`
	widthImg=`echo "$propImg" | cut -f2 -d" "`
	colorspaceImg=`echo "$propImg" | cut -f3 -d" "`
	# compute the resolution of the whole page (taking into account all images)
	dpi=$(($heightImg*72/$heightPDF))
	echo "Page $page: Resolution: ${dpi} dpi"

	# extract current page as image with right rotation
	echo "Page $page: Extracting image as ppm/pgm"
	if [ $colorspaceImg == "Gray" ]; then
		ext="pgm"
		opt="-gray"
	else
		ext="ppm"
		opt=""		
	fi
	pdftoppm -f $page -l $page -r $dpi $opt $infile > "${tmp}/${page}.$ext"

	# improve quality of the image with unpaper to get better OCR results
	echo "Page $page: Preprocessing image with unpaper"
	unpaper --dpi $dpi --mask-scan-size 100 \
		--no-grayfilter --no-blackfilter --no-mask-center --no-border-align \
		"$tmp/$page.$ext" "$tmp/$page.forocr.$ext" 1> /dev/null

	# perform OCR
	echo "Page $page: Performing OCR"
	tesseract -l "$LAN" "$tmp/$page.forocr.$ext" "$tmp/$page.hocr" hocr 1> /dev/null 2> /dev/null 
	mv "${tmp}/${page}.hocr.html" "$tmp/$page.hocr"

	# compress image to be put inside the pdf file
	echo "Page $page: Compressing image for final PDF file"
	convert -colorspace "$colorspaceImg" "$tmp/$page.forocr.$ext" "$tmp/$page.forpdf.jpg"
	
	# embed text and image to new pdf file
	echo "Page $page: Embedding text in PDF"
	python hocrTransform.py -r $dpi -i "$tmp/$page.forpdf.jpg" "$tmp/$page.hocr" "$tmp/${page}-ocred.pdf"
	
	# go to next page of the pdf
	page=$(($page+1))
done


# concatenate all pages
pdftk ${tmp}/*-ocred.pdf cat output "${tmp}/ocred.pdf"

# insert metadata
# TODO

# validate generated pdf file (compliance to PDF/A) 
#java -jar jhove/bin/JhoveApp.jar -m PDF-hul "$1" |egrep "Status|Message"
