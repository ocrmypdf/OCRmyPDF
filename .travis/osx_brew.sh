#!/bin/bash
set -euo pipefail
set -x

pip3 install homebrew-pypi-poet
python3 .travis/autobrew.py
cat ocrmypdf.rb
brew audit ocrmypdf.rb
