import pkg_resources

PROGRAM_NAME = 'ocrmypdf'

VERSION = pkg_resources.get_distribution('ocrmypdf').version


# These imports are for v4.x backward compatibility for consumers of ocrmypdf
# (if any). They are deprecated and will be removed in v5.x.
from .exec import ghostscript, qpdf, tesseract, unpaper, get_program
from .exceptions import ExitCode
from .helpers import page_number, is_iterable_notstr



