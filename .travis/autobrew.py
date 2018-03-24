#!/usr/bin/env python3
# © 2017-18 James R. Barlow: github.com/jbarlow83

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

  depends_on "pkg-config" => :build
  depends_on "mupdf-tools" => :build  # statically links libmupdf.a
  depends_on "freetype"
  depends_on "ghostscript"
  depends_on "jpeg"
  depends_on "libpng"
  depends_on "python"
  depends_on "qpdf"
  depends_on "tesseract"
  depends_on "unpaper"

${resources}
  def install
    venv = virtualenv_create(libexec, "python3")

    resource("Pillow").stage do
      inreplace "setup.py" do |s|
        sdkprefix = MacOS::CLT.installed? ? "" : MacOS.sdk_path
        s.gsub! "openjpeg.h", "probably_not_a_header_called_this_eh.h"
        s.gsub! "ZLIB_ROOT = None", "ZLIB_ROOT = ('#{sdkprefix}/usr/lib', '#{sdkprefix}/usr/include')"
        s.gsub! "JPEG_ROOT = None", "JPEG_ROOT = ('#{Formula["jpeg"].opt_prefix}/lib', '#{Formula["jpeg"].opt_prefix}/include')"
        s.gsub! "FREETYPE_ROOT = None", "FREETYPE_ROOT = ('#{Formula["freetype"].opt_prefix}/lib', '#{Formula["freetype"].opt_prefix}/include')"
      end

      # avoid triggering "helpful" distutils code that doesn't recognize Xcode 7 .tbd stubs
      ENV.append "CFLAGS", "-I#{MacOS.sdk_path}/System/Library/Frameworks/Tk.framework/Versions/8.5/Headers" unless MacOS::CLT.installed?
      venv.pip_install Pathname.pwd
    end

    res = resources.map(&:name).to_set - ["Pillow"]

    res.each do |r|
      venv.pip_install resource(r)
    end

    venv.pip_install_and_link buildpath
  end

  test do
    # Since we use Python 3, we require a UTF-8 locale
    ENV["LC_ALL"] = "en_US.UTF-8"

    system "#{bin}/ocrmypdf", "-f", "-q", "--deskew",
                              test_fixtures("test.pdf"), "ocr.pdf"
    assert_predicate testpath/"ocr.pdf", :exist?
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
