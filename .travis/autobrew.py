#!/usr/bin/env python3
# © 2016 James R. Barlow: github.com/jbarlow83

from string import Template
from subprocess import run, PIPE
import re

recipe_template = Template("""
class Ocrmypdf < Formula
  include Language::Python::Virtualenv

  desc "Adds an OCR text layer to scanned PDF files"
  homepage "https://github.com/jbarlow83/OCRmyPDF"
  ${ocrmypdf_url}
  ${ocrmypdf_sha256}

  depends_on :python3
  depends_on :x11  # Pillow needs XQuartz
  depends_on "pkg-config" => :build
  depends_on "libffi"
  depends_on "tesseract"
  depends_on "ghostscript"
  depends_on "unpaper"
  depends_on "qpdf"

  # For Pillow source install
  depends_on "openjpeg"
  depends_on "freetype"
  depends_on "libpng"
  depends_on "libjpeg"
  depends_on "webp"
  depends_on "little-cms2"

${resources}
  def install
    ENV.append ["SETUPTOOLS_SCM_PRETEND_VERSION"], "v${ocrmypdf_version}"
    ENV.each do |key, value|
      puts "#{key}:#{value}"
    end
    virtualenv_install_with_resources
  end

  test do
    # `test do` will create, run in and delete a temporary directory.
    #
    # The installed folder is not in the path, so use the entire path to any
    # executables being tested: `system "#{bin}/program", "do", "something"`.
    system "#{bin}/ocrmypdf", "--version"
  end
end
""")

def main():
    p = run(['poet', '--single', 'ocrmypdf'],
            encoding='utf-8', stdout=PIPE, check=True)

    ocrmypdf_lines = p.stdout.splitlines()
    ocrmypdf_url = ocrmypdf_lines[1].strip()
    ocrmypdf_sha256 = ocrmypdf_lines[2].strip()

    ocrmypdf_version = re.search(
        r'ocrmypdf-(.+)\.tar.*', ocrmypdf_url).group(1)
    print(f"Autobrewing {ocrmypdf_version}")

    p = run(['poet', '--resources', 'ocrmypdf'],
            encoding='utf-8', stdout=PIPE, check=True)

    poet_resources = p.stdout

    # Remove the duplicate "ocrmypdf" resource block
    all_resources = poet_resources.split('resource')
    kept_resources = [block for block in all_resources if 'ocrmypdf' not in block]
    resources = 'resource'.join(kept_resources)

    with open('ocrmypdf.rb', 'w') as out:
        out.write(recipe_template.substitute(**locals()))


if __name__ == '__main__':
    main()
