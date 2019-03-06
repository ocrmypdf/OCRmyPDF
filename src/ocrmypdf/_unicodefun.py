# Copyright (c) 2014, Armin Ronacher
#
# Copyright (c) 2017, James R Barlow
#
# Some rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#
#     * Redistributions in binary form must reproduce the above
#       copyright notice, this list of conditions and the following
#       disclaimer in the documentation and/or other materials provided
#       with the distribution.
#
#     * The names of the contributors may not be used to endorse or
#       promote products derived from this software without specific
#       prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


import codecs
import os
import sys


def verify_python3_env():  # pragma: no cover
    """Ensures that the environment is good for unicode on Python 3."""

    # PEP 538 changes in Python 3.7 should make this wrangling unnecessary
    if sys.version_info[0:3] >= (3, 7, 0):
        return

    try:
        import locale

        fs_enc = codecs.lookup(locale.getpreferredencoding()).name
    except Exception:
        fs_enc = 'ascii'
    if fs_enc != 'ascii':
        return

    extra = ''
    if os.name == 'posix':
        import subprocess

        rv = subprocess.run(
            ['locale', '-a'], stdout=subprocess.PIPE, stderr=subprocess.PIPE
        ).stdout
        good_locales = set()
        has_c_utf8 = False

        # Make sure we're operating on text here.
        if isinstance(rv, bytes):
            rv = rv.decode('ascii', 'replace')

        for line in rv.splitlines():
            locale = line.strip()
            if locale.lower().endswith(('.utf-8', '.utf8')):
                good_locales.add(locale)
                if locale.lower() in ('c.utf8', 'c.utf-8'):
                    has_c_utf8 = True

        extra += '\n\n'
        if not good_locales:
            extra += (
                'Additional information: on this system no suitable UTF-8\n'
                'locales were discovered.  This most likely requires resolving\n'
                'by reconfiguring the locale system.'
            )
        elif has_c_utf8:
            extra += (
                'This system supports the C.UTF-8 locale which is recommended.\n'
                'You might be able to resolve your issue by exporting the\n'
                'following environment variables:\n\n'
                '    export LC_ALL=C.UTF-8\n'
                '    export LANG=C.UTF-8'
            )
        else:
            extra += (
                'This system lists a couple of UTF-8 supporting locales that\n'
                'you can pick from.  The following suitable locales were\n'
                'discovered: %s'
            ) % ', '.join(sorted(good_locales))

        bad_locale = None
        for locale in os.environ.get('LC_ALL'), os.environ.get('LANG'):
            if locale and locale.lower().endswith(('.utf-8', '.utf8')):
                bad_locale = locale
            if locale is not None:
                break
        if bad_locale is not None:
            extra += (
                '\nocrmypdf discovered that you exported a UTF-8 locale\n'
                'but the locale system could not pick up from it because\n'
                'it does not exist.  The exported locale is "%s" but it\n'
                'is not supported'
            ) % bad_locale

    raise RuntimeError(
        'ocrmypdf will abort further execution because Python 3 '
        'was configured to use ASCII as encoding for the '
        'environment.' + extra
    )
