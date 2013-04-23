#!/bin/sh

VERSION="alpha0"

usage() {
	cat << EOF
--------------------------------------------------------------------------------------
Script aimed at generating a searchable PDF file from a PDF file containing only images.
(The script performs optical character recognition of each respective page using the
tesseract engine)

Copyright: fritz from NAS4Free forum
Version: $VERSION

Usage: OCRmyPDF.sh  [-h] [-v] [-g] [-k] [-d] [-c] [-i] [-l language] [-C filename] inputfile outputfile

-h : Display this help message
-v : Increase the verbosity (this option can be used more than once)
-g : Activate debug mode:
     - Generates a PDF file containing each page twice (once with the image, once without the image
       but with the OCRed text as well as the detected bounding boxes detected during OCR)
     - Set the verbosity to the highest possible 
-k : Do not delete the temporary files
-d : Deskew each page before performing OCR
-c : Clean each page before performing OCR
-i : Incorporate the cleaned image in the final PDF file (by default the original image	
     image, or the deskewed image if the -d option is set, is incorporated)
-l : Set the language of the PDF file in order to improve OCR results (default "eng")
     Any language supported by tesseract is supported.
-C : Pass an additional configuration file to the tesseract OCR engine.
     (this option can be used more than once)
     Note: The configuration file must be available in the "tessdata/configs" folder
     of your tesseract installation
inputfile  : PDF file to be OCRed
outputfile : The PDF/A file to be generated 
--------------------------------------------------------------------------------------
EOF
}


#################################################
# Get an absolute path from a relative path to a file
#
# Param1 : Relative path
# Returns: 1 if the folder in which the file is located does not exist
#          0 otherwise
################################################# 
absolutePath() {
	local wdsave absolutepath 
	wdsave="`pwd`"
	! cd "`dirname "$1"`" 1> /dev/null 2> /dev/null && return 1
	absolutepath="`pwd`/`basename $1`"
	cd "$wdsave"
	echo "$absolutepath"
	return 0
}



# Initialization of constants
EXIT_BAD_ARGS="1"		# possible exit codes
EXIT_BAD_INPUT_FILE="2"
EXIT_MISSING_DEPENDENCY="3"
EXIT_INVALID_OUPUT_PDFA="4"
EXIT_OTHER_ERROR="5"
LOG_ERR="0"			# 0=only error messages
LOG_INFO="1"			# 1=error messages and some infos
LOG_DEBUG="2"			# 2=debug level logging

# Initialization the configuration parameters with default values
VERBOSITY="$LOG_ERR"		# default verbosity level
LAN="eng"			# default language of the PDF file (required to get good OCR results)
KEEP_TMP="0"			# do not delete the temporary files (default)
PREPROCESS_DESKEW="0"		# 0=no, 1=yes (deskew image)
PREPROCESS_CLEAN="0"		# 0=no, 1=yes (clean image to improve OCR)
PREPROCESS_CLEANTOPDF="0"	# 0=no, 1=yes (put cleaned image in final PDF)
DEBUG_MODE="0"			# 0=no, 1=yes (generates each PDF page twice, with and without image)
TESS_CFG_FILES=""		# list of additional configuration files to be used by tesseract

# Parse optional command line arguments
while getopts ":hvgkdcil:C:" opt; do
	case $opt in
		h) usage ; exit 0 ;;
		v) VERBOSITY=$(($VERBOSITY+1)) ;;
		g) VERBOSITY="10"; DEBUG_MODE="1" ;;
		k) KEEP_TMP="1" ;;
		d) PREPROCESS_DESKEW="1" ;;
		c) PREPROCESS_CLEAN="1" ;;
		i) PREPROCESS_CLEANTOPDF="1" ;;
		l) LAN="$OPTARG" ;;
		C) TESS_CFG_FILES="$OPTARG $TESS_CFG_FILES" ;;
		\?)
			echo "Invalid option: -$OPTARG"
			echo
			usage
			exit $EXIT_BAD_ARGS ;;
		:)
			echo "Option -$OPTARG requires an argument"
			echo
			usage
			exit $EXIT_BAD_ARGS ;;
	esac
done

# Remove the optional arguments parsed above.
shift $((OPTIND-1))

# Check if the number of mandatory parameters
# provided is as expected
if [ "$#" -ne "2" ]; then
	echo "Exactly one mandatory argument shall be provided"
	echo
	usage
	exit $EXIT_BAD_ARGS
fi

! absolutePath "$1" && echo "The folder in which the input file should be located does not exist. Exiting..." && exit $EXIT_BAD_ARGS
FILE_INPUT_PDF="`absolutePath "$1"`"
! absolutePath "$2" && echo "The folder in which the output file should be generated does not exist. Exiting..." && exit $EXIT_BAD_ARGS
FILE_OUTPUT_PDFA="`absolutePath "$2"`"




# set script path as working directory
cd "`dirname $0`"

# check if the required utilities are installed
[ $VERBOSITY -ge $LOG_DEBUG ] && echo "Checking if all dependencies are installed"
! command -v gs > /dev/null && echo "Please install ghostcript. Exiting..." && exit $EXIT_MISSING_DEPENDENCY
! command -v identify > /dev/null && echo "Please install ImageMagick. Exiting..." && exit $EXIT_MISSING_DEPENDENCY
! command -v pdfimages > /dev/null && echo "Please install xpdf. Exiting..." && exit $EXIT_MISSING_DEPENDENCY
! command -v pdftoppm > /dev/null && echo "Please install xpdf. Exiting..." && exit $EXIT_MISSING_DEPENDENCY
! command -v pdftk > /dev/null && echo "Please install pdftk. Exiting..." && exit $EXIT_MISSING_DEPENDENCY
! command -v unpaper > /dev/null && echo "Please install unpaper. Exiting..." && exit $EXIT_MISSING_DEPENDENCY
! command -v tesseract > /dev/null && echo "Please install tesseract and tesseract-data. Exiting..." && exit $EXIT_MISSING_DEPENDENCY
! command -v java > /dev/null && echo "Please install java. Exiting..." && exit $EXIT_MISSING_DEPENDENCY




# Initialize path to temporary files
TMP_FLD="./tmp/`date +"%Y%m%d_%H%M"`.filename.`basename "$FILE_INPUT_PDF" | sed s/[.][^.]*//`"
FILE_SIZE_PAGES="$TMP_FLD/page-sizes.txt"		# size in pt of the respective page of the input PDF file
FILES_OCRed_PDFS="${TMP_FLD}/*-ocred.pdf"		# string matching all 1 page PDF files that need to be merged
FILE_OUTPUT_PDF="${TMP_FLD}/ocred.pdf"			# name of the OCRed PDF file before conversion to PDF/A
FILE_VALIDATION_LOG="${TMP_FLD}/pdf_validation.log"	# log file containing the results of the validation of the PDF/A file

# Create tmp folder
[ $VERBOSITY -ge $LOG_DEBUG ] && echo "Creating temporary folder"
rm -r -f "${TMP_FLD}"
mkdir -p "${TMP_FLD}"




# get the size of each pdf page (width / height) in pt (inch*72)
[ $VERBOSITY -ge $LOG_DEBUG ] && echo "Input file: Extracting size of each page (in pt)"
! identify -format "%w %h\n" "$FILE_INPUT_PDF" > "$FILE_SIZE_PAGES" \
	&& echo "Could not get size of PDF pages. Exiting..." && exit $EXIT_BAD_INPUT_FILE
sed -I "" '/^$/d' "$FILE_SIZE_PAGES"	# removing empty lines (last one should be)
numpages=`cat "$FILE_SIZE_PAGES" | wc -l | sed 's/^ *//g'`
[ $VERBOSITY -ge $LOG_INFO ] && echo "Input file: The file has $numpages pages"

# Itterate the pages of the input pdf file
cpt="1"
while read pageSize ; do

	# add leading zeros to the page number
	page=`printf "%04d" $cpt`
	[ $VERBOSITY -ge $LOG_INFO ] && echo "Processing page $page"
	
	# create the name of the required file
	curOrigImg="$TMP_FLD/${page}_Image"			# original image available in the current PDF page 
							# (the image file may have a different orientation than in the pdf file)
	curHocr="$TMP_FLD/$page.hocr"			# hocr file to be generated by the OCR SW for the current page
	curOCRedPDF="$TMP_FLD/${page}-ocred.pdf"		# PDF file containing the image + the OCRed text for the current page
	curOCRedPDFDebug="$TMP_FLD/${page}-debug-ocred.pdf"	# PDF file containing data required to find out if OCR worked correctly
	
	[ $VERBOSITY -ge $LOG_DEBUG ] && echo "Page $page: Computing embedded image resolution"
	# get width / height of PDF page
	heightPDF=`echo $pageSize | cut -f1 -d" "`
	widthPDF=`echo $pageSize | cut -f2 -d" "`
	# extract raw image from pdf file to compute resolution
	# unfortunatelly this image may not be rotated as in the pdf...
	# so we will have to extract it again later
	pdfimages -f $page -l $page -j "$FILE_INPUT_PDF" "$curOrigImg" 1>&2	
	# count number of extracted images
	nbImg=`ls -1 "$curOrigImg"* | wc -l`
	[ $nbImg -ne "1" ] && echo "Not exactly 1 image on page $page. Exiting..." && exit $EXIT_BAD_INPUT_FILE
	
	# Get characteristics of the extracted image
	curOrigImg01=`ls -1 "$curOrigImg"*`
	propCurOrigImg01=`identify -format "%w %h %[colorspace]" "$curOrigImg01"`
	heightCurOrigImg01=`echo "$propCurOrigImg01" | cut -f1 -d" "`
	widthICurOrigImg01=`echo "$propCurOrigImg01" | cut -f2 -d" "`
	colorspaceCurOrigImg01=`echo "$propCurOrigImg01" | cut -f3 -d" "`
	# compute the resolution of the whole page (taking into account all images)
	dpi_x=$(($widthICurOrigImg01*72/$widthPDF))
	dpi_y=$(($heightCurOrigImg01*72/$heightPDF))
	[ "$dpi_x" -ne "$dpi_y" ] && echo "X/Y Resolutions not equal (Not supported currently). Exiting..." && exit $EXIT_BAD_INPUT_FILE
	dpi="$dpi_x"

	# Identify if page image should be saved as ppm (color) or pgm (gray)
	ext="ppm"
	opt=""		
	if [ $colorspaceCurOrigImg01 == "Gray" ]; then
		ext="pgm"
		opt="-gray"
	fi
	curImgPixmap="$TMP_FLD/$page.$ext"
	curImgPixmapDeskewed="$TMP_FLD/$page.deskewed.$ext"
	curImgPixmapClean="$TMP_FLD/$page.cleaned.$ext"
	
	# extract current page as image with right orientation and resoltution
	[ $VERBOSITY -ge $LOG_DEBUG ] && echo "Page $page: Extracting image as $ext file (${dpi} dpi)"
	! pdftoppm -f $page -l $page -r $dpi $opt "$FILE_INPUT_PDF" > "$curImgPixmap" \
		&& echo "Could not extract page $page as $ext from $FILE_INPUT_PDF. Exiting..." && exit $EXIT_OTHER_ERROR

	# if requested deskew image (without changing its size in pixel)
	if [ "$PREPROCESS_DESKEW" -eq "1" ]; then
		[ $VERBOSITY -ge $LOG_DEBUG ] && echo "Page $page: Deskewing image"
		! convert "$curImgPixmap" -deskew 40% -gravity center -extent ${heightCurOrigImg01}x${widthICurOrigImg01} "$curImgPixmapDeskewed" \
			&& echo "Could not deskew \"$curImgPixmap\". Exiting..." && exit $EXIT_OTHER_ERROR
	else
		cp "$curImgPixmap" "$curImgPixmapDeskewed"
	fi

	# if requested clean image with unpaper to get better OCR results
	if [ "$PREPROCESS_CLEAN" -eq "1" ]; then
		[ $VERBOSITY -ge $LOG_DEBUG ] && echo "Page $page: Cleaning image with unpaper"
		! unpaper --dpi $dpi --mask-scan-size 100 \
			--no-deskew --no-grayfilter --no-blackfilter --no-mask-center --no-border-align \
			"$curImgPixmapDeskewed" "$curImgPixmapClean" 1> /dev/null \
			&& echo "Could not clean \"$curImgPixmapDeskewed\". Exiting..." && exit $EXIT_OTHER_ERROR
	else
		cp "$curImgPixmapDeskewed" "$curImgPixmapClean"
	fi

	# perform OCR
	[ $VERBOSITY -ge $LOG_DEBUG ] && echo "Page $page: Performing OCR"
	! tesseract -l "$LAN" "$curImgPixmapClean" "$curHocr" hocr $TESS_CFG_FILES 1> /dev/null 2> /dev/null \
		&& echo "Could not OCR file \"$curImgPixmapClean\". Exiting..." && exit $EXIT_OTHER_ERROR
	mv "$curHocr.html" "$curHocr"

	# embed text and image to new pdf file
	if [ "$PREPROCESS_CLEANTOPDF" -eq "1" ]; then
		image4finalPDF="$curImgPixmapClean"
	else
		image4finalPDF="$curImgPixmapDeskewed"	
	fi
	[ $VERBOSITY -ge $LOG_DEBUG ] && echo "Page $page: Embedding text in PDF"
	! python hocrTransform.py -r $dpi -i "$image4finalPDF" "$curHocr" "$curOCRedPDF" \
		&& echo "Could not create PDF file from \"$curHocr\". Exiting..." && exit $EXIT_OTHER_ERROR
	
	# if requested generate special debug PDF page with visible OCR text
	if [ $DEBUG_MODE -eq "1" ] ; then
		[ $VERBOSITY -ge $LOG_DEBUG ] && echo "Page $page: Embedding text in PDF (debug page)"
		! python hocrTransform.py -b -r $dpi "$curHocr" "$curOCRedPDFDebug" \
			&& echo "Could not create PDF file from \"$curHocr\". Exiting..." && exit $EXIT_OTHER_ERROR	
	fi
	
	# delete temporary files created for the current page
	# to avoid using to much disk space in case of PDF files having many pages
	if [ $KEEP_TMP -eq 0 ]; then
		rm "$curOrigImg"*.*
		rm "$curHocr"
		rm "$curImgPixmap"
		rm "$curImgPixmapDeskewed"
		rm "$curImgPixmapClean"
	fi

	# go to next page of the pdf
	cpt=$(($cpt+1))
	
done < "$FILE_SIZE_PAGES"




# concatenate all pages
[ $VERBOSITY -ge $LOG_DEBUG ] && echo "Output file: Concatenating all pages"
! pdftk $FILES_OCRed_PDFS cat output "$FILE_OUTPUT_PDF" \
	&& echo "Could not concatenate individual PDF pages (\"$FILES_OCRed_PDFS\") to one file. Exiting..." && exit $EXIT_OTHER_ERROR

# insert metadata (copy metadata from input file)
#echo "Output file: Inserting metadata"
# TODO (may work with pdftk update_info)
# the name of the file may be used as title

# convert the pdf file to match PDF/A format
[ $VERBOSITY -ge $LOG_DEBUG ] && echo "Output file: Converting to PDF/A" 
! gs -dQUIET -dPDFA -dBATCH -dNOPAUSE -dUseCIEColor \
	-sProcessColorModel=DeviceCMYK -sDEVICE=pdfwrite -sPDFACompatibilityPolicy=2 \
	-sOutputFile=$FILE_OUTPUT_PDFA "$FILE_OUTPUT_PDF" 1> /dev/null 2> /dev/null \
	&& echo "Could not convert PDF file \"$FILE_OUTPUT_PDF\" to PDF/A. Exiting..." && exit $EXIT_OTHER_ERROR

# validate generated pdf file (compliance to PDF/A)
[ $VERBOSITY -ge $LOG_DEBUG ] && echo "Output file: Checking compliance to PDF/A standard" 
java -jar /root/jhove-1_9/jhove/bin/JhoveApp.jar -m PDF-hul "$FILE_OUTPUT_PDFA" > "$FILE_VALIDATION_LOG"
grep -i "Status|Message" "$FILE_VALIDATION_LOG" # summary of the validation
# check if the validation was successful
pdf_valid=1
grep -i "ErrorMessage" "$FILE_VALIDATION_LOG" && pdf_valid=0
grep -i "Status.*not valid" "$FILE_VALIDATION_LOG" && pdf_valid=0
grep -i "Status.*Not well-formed" "$FILE_VALIDATION_LOG" && pdf_valid=0
[ $VERBOSITY -ge $LOG_INFO ] && [ $pdf_valid -eq 1 ] && echo "Output file: The generated PDF/A file is VALID"
[ $pdf_valid -ne 1 ] && echo "Output file: The generated PDF/A file is INVALID"
[ $VERBOSITY -ge $LOG_DEBUG ] && cat "$FILE_VALIDATION_LOG"



# delete temporary files
if [ $KEEP_TMP -eq 0 ]; then
	rm -r -f "${TMP_FLD}"
fi

exit 0
