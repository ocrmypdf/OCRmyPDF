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
	pdftk "$infile" cat $page output "${tmp}/${page}.pdf" > /dev/null

	# get the size of the pdf (width / height) page in pt (inch*72)
	# identify -format "return %w, %h\n" "${tmp}/${page}.pdf"
	
	# extract image from pdf file (keeping the resolution as available in the pdf file)
	# pdfimages -f 1 -l 1 "${tmp}/${page}.pdf" ${page} 1>&2

	# itterate the extracted images (there can be more than 1 image on the page)
	# and get there respective number of x/y pixel 
	# identify -format "return %w, %h\n" img1-xxx.ppm
	
	# compute the resolution of the whole page (taking into account all images)
	
	
	# extract the image with the right resolution
	echo "Page $page: Extracting image from PDF"	
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

	# compress image to be put inside the pdf file
	echo "Page $page: Compress image for final PDF file"
	convert "${tmp}/${page}.forocr.ppm" "${tmp}/${page}.forpdf.jpg"
	
	# embed text and image to new pdf file
	echo "Page $page: Embedding text in PDF"
	python hocrTransform.py -r $dpi -i "${tmp}/${page}.forpdf.jpg" "${tmp}/${page}.hocr" "${tmp}/${page}-ocred.pdf"
	
	# go to next page of the pdf
	page=$(($page+1))
done


# concatenate all pages
pdftk ${tmp}/*-ocred.pdf cat output "${tmp}/ocred.pdf"

# insert metadata
# TODO

# validate generated pdf file (compliance to PDF/A) 
#java -jar jhove/bin/JhoveApp.jar -m PDF-hul "$1" |egrep "Status|Message"
