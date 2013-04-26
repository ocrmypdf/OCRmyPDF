#!/bin/sh
#
# Perform OCR several times in order to find how quicly the quality decreases

cpt=1

while [ $cpt -le 10 ] ; do

	echo "------- Itteration $cpt ---------"

	! ../../OCRmyPDF.sh -vv -l deu -k ../../tmp/ocred-$(($cpt-1)).pdf ../../tmp/ocred-$cpt.pdf && exit 1
	
	cpt=$(($cpt+1))
	
done