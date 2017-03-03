#!/bin/bash
set -euo pipefail
set -x

pip3 install homebrew-pypi-poet
python3 .travis/autobrew.py
brew audit ocrmypdf.rb
cat ocrmypdf.rb
