#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 James R. Barlow
# SPDX-License-Identifier: MPL-2.0
#
# Install the snap we just packed and push one real PDF through it.
#
# The snap is strictly confined, so a failure here is as likely to be a snapd
# or confinement problem as an OCRmyPDF bug, and those kill the process before
# it can say anything. Send the OCR run's stderr to a file we cat back
# unconditionally, and dump snapd state when it fails, so the log explains
# itself either way.
#
# Usage: smoke-test-snap.sh [expected-version]

set -euxo pipefail

expected_version=${1:-}

sudo snap install --dangerous ocrmypdf.snap
snap list ocrmypdf
snap connections ocrmypdf
df -h .

# The snap's own version comes from git describe, so it only matches
# ocrmypdf --version on a tagged build; callers pass it only when it should.
if [ -n "$expected_version" ]; then
  ocrmypdf --version | grep -Fx "$expected_version"
else
  ocrmypdf --version
fi

rc=0
ocrmypdf --deskew --clean --optimize 2 -l eng+fra --sidecar skew.txt \
  - - <tests/resources/skew.pdf >skew-ocr.pdf 2>ocr-stderr.txt || rc=$?

echo "::group::ocrmypdf stderr (exit $rc)"
cat ocr-stderr.txt || true
echo "::endgroup::"

if [ "$rc" -ne 0 ]; then
  echo "::group::snapd diagnostics"
  ls -l skew-ocr.pdf skew.txt || true
  snap changes || true
  sudo journalctl -u snapd --no-pager -n 200 || true
  sudo dmesg | grep -iE 'apparmor|seccomp|audit' | tail -n 50 || true
  echo "::endgroup::"
  exit "$rc"
fi

grep -i 'the' skew.txt
