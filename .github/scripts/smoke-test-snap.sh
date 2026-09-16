#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 James R. Barlow
# SPDX-License-Identifier: MPL-2.0
#
# Install the snap we just packed and push one real PDF through it.
#
# The snap is strictly confined, so a failure here is as likely to be a snapd
# or confinement problem as an OCRmyPDF bug, and those kill the process before
# it can say anything. Run each check for its exit code rather than letting
# errexit abort at the first one, so a single run reports every result, and
# dump snapd state at the end if anything failed.
#
# Usage: smoke-test-snap.sh [expected-version]

set -uxo pipefail

expected_version=${1:-}

set -e
sudo snap install --dangerous ocrmypdf.snap
snap list ocrmypdf
snap connections ocrmypdf
df -h .
set +e

# Run --version three ways: the exit code differed between a bare call and a
# piped one, which is what we are here to pin down.
ocrmypdf --version >version-tty.txt 2>version-tty-err.txt
version_rc=$?
ocrmypdf --version 2>version-pipe-err.txt | cat >version-pipe.txt
version_piped_rc=${PIPESTATUS[0]}

echo "::group::ocrmypdf --version"
echo "bare exit: $version_rc, stdout: $(cat version-tty.txt)"
cat version-tty-err.txt
echo "piped exit: $version_piped_rc, stdout: $(cat version-pipe.txt)"
cat version-pipe-err.txt
echo "::endgroup::"

ocrmypdf --deskew --clean --optimize 2 -l eng+fra --sidecar skew.txt \
  - - <tests/resources/skew.pdf >skew-ocr.pdf 2>ocr-stderr.txt
ocr_rc=$?

echo "::group::ocrmypdf OCR run (exit $ocr_rc)"
cat ocr-stderr.txt
ls -l skew-ocr.pdf skew.txt
echo "::endgroup::"

grep -i 'the' skew.txt
grep_rc=$?

version_matches=0
if [ -n "$expected_version" ]; then
  grep -Fx "$expected_version" version-tty.txt
  version_matches=$?
fi

if [ "$version_rc" -ne 0 ] || [ "$version_piped_rc" -ne 0 ] ||
   [ "$ocr_rc" -ne 0 ] || [ "$grep_rc" -ne 0 ] || [ "$version_matches" -ne 0 ]; then
  echo "::group::snapd diagnostics"
  snap changes
  sudo journalctl -u snapd --no-pager -n 200
  sudo dmesg | grep -iE 'apparmor|seccomp|audit' | tail -n 50
  echo "::endgroup::"
  echo "smoke test failed: version=$version_rc version_piped=$version_piped_rc" \
       "ocr=$ocr_rc sidecar_grep=$grep_rc version_match=$version_matches"
  exit 1
fi
