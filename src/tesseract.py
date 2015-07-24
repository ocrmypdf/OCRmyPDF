#!/usr/bin/env python3

from cffi import FFI
from ctypes.util import find_library
import sys

ffi = FFI()
try:
    libtess = ffi.dlopen(find_library('libtesseract'))
except Exception:
    print("Could not find Tesseract 3.02.02", file=sys.stderr)
    sys.exit(1)

ffi.cdef('''
    const char* TessVersion();
''')

cstr_version = libtess.TessVersion()
TESS_VERSION = ffi.string(cstr_version).decode('ascii')

__all__ = ['TESS_VERSION']
