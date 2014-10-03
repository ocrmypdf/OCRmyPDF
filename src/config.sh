#####################################################################################
# The following parameters might be changed by the user
#####################################################################################

DEFAULT_LANGUAGES="eng"			# Default language(s) of the PDF file. The language should be set correctly in order to get good OCR results.
					# Any language supported by tesseract is supported (Tesseract uses 3-character ISO 639-2 language codes)
					# Multiple languages may be specified, separated by '+' characters.
					
DEFAULT_DPI=300				# dpi value used as fall back if the page dpi cannot be determined

#####################################################################################
# Do NOT change the following parameters
#####################################################################################

TOOLNAME="OCRmyPDF"
VERSION="v2.x"

# possible exit codes
EXIT_BAD_ARGS="1"
EXIT_BAD_INPUT_FILE="2"
EXIT_MISSING_DEPENDENCY="3"
EXIT_INVALID_OUTPUT_PDFA="4"
EXIT_FILE_ACCESS_ERROR="5"
EXIT_OTHER_ERROR="15"

# possible log levels
LOG_ERR="0"				# only error messages
LOG_WARN="1"				# error messages and warnings
LOG_INFO="2"				# error messages, warnings and some infos
LOG_DEBUG="3"				# debug level logging

# various paths
SRC="./src"				# location of the source folder (except source of external tools like jhove)
OCR_PAGE="$SRC/ocrPage.sh"		# path to the script aimed at OCRing one page
JHOVE="./jhove/bin/JhoveApp.jar"	# java SW for validating the final PDF/A
JHOVE_CFG="./jhove/conf/jhove.conf"	# location of the jhove config file
