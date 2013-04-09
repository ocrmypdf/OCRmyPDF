#!/bin/sh
echo "usage: ./scan-archive.sh filename.pdf"

infile="$1"
lan="deu"
dpi=300

tmp="./tmp"

# delete tmp files
rm -r -f "${tmp}"
mkdir -p "${tmp}"

# detect the number of page of the pdf file
numpages=`pdftk $infile "dump_data" | grep "NumberOfPages" | cut -f2 -d" "`
echo "PDF file has $numpages pages"

# Itterate the pages of the pdf file
page="1"
while [ $page -le $numpages ]; do

	# extract image from current pdf page
	echo "Page $page: Extracting image from PDF"
	pdftk "$infile" cat $page output "${tmp}/${page}.pdf" > /dev/null
	pdftoppm -r $dpi "${tmp}/${page}.pdf" > "${tmp}/${page}.ppm"

	# improve quality of the image to get better ocr results
	echo "Page $page: Preprocessing image with unpaper"
	unpaper --dpi $dpi --mask-scan-size 100 \
		--no-grayfilter --no-blackfilter --no-mask-center --no-border-align \
		--overwrite "$tmp/$page.ppm" "$tmp/$page.forocr.ppm" > /dev/null 

	# perform OCR
	echo "Page $page: Performing OCR"
	tesseract -l ${lan} "${tmp}/${page}.forocr.ppm" "${tmp}/${page}.hocr" hocr 1> /dev/null 2> /dev/null 
	cp "${tmp}/${page}.hocr.html" "${tmp}/${page}.hocr"

	# embed text and image to new pdf file
	echo "Page $page: Embedding text in PDF"
	python hocrTransform.py "${tmp}/${page}.hocr" "${tmp}/${page}.forocr.ppm" "${tmp}/${page}-ocred.pdf"

	# go to next page of the pdf
	page=$(($page+1))
done


# concatenate all pages
pdftk ${tmp}/*-ocred.pdf cat output "${tmp}/ocred.pdf"

# insert metadata

# validate generated pdf file (compliance to PDF/A) 
#java -jar jhove/bin/JhoveApp.jar -m PDF-hul "$1" |egrep "Status|Message"
