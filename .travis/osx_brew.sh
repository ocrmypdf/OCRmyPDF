#!/bin/bash
# © 2017 James R. Barlow: github.com/jbarlow83
set -euo pipefail
set -x

pip3 install homebrew-pypi-poet
python3 .travis/autobrew.py
cat ocrmypdf.rb

# brew audit crashes Travis
#brew audit ocrmypdf.rb

# Important: disable debug output so token is hidden
set +x
git clone https://$HOMEBREW_OCRMYPDF_TOKEN@github.com/jbarlow83/homebrew-ocrmypdf.git
set -x

pushd homebrew-ocrmypdf
cp ../ocrmypdf.rb Formula/ocrmypdf.rb
git add Formula/ocrmypdf.rb
git commit -m "homebrew-ocrmypdf: automatic release $TRAVIS_BUILD_NUMBER $TRAVIS_TAG"
git push origin master
popd
