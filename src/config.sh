TOOLNAME="OCRmyPDF"
VERSION="v2.x"

EXIT_BAD_ARGS="1"			# possible exit codes
EXIT_BAD_INPUT_FILE="2"
EXIT_MISSING_DEPENDENCY="3"
EXIT_INVALID_OUPUT_PDFA="4"
EXIT_OTHER_ERROR="5"
LOG_ERR="0"				# 0=only error messages
LOG_INFO="1"				# 1=error messages and some infos
LOG_DEBUG="2"				# 2=debug level logging
SRC="./src"				# location of the source folder (except source of external tools like jhove)
OCR_PAGE="$SRC/ocrPage.sh"		# path to the script aimed at OCRing one page
JHOVE="./jhove/bin/JhoveApp.jar"	# java SW for validating the final PDF/A
JHOVE_CFG="./jhove/conf/jhove.conf"	# location of the jhove config file
