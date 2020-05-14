# © 2020 James R. Barlow: github.com/jbarlow83
#
# This file is part of OCRmyPDF.
#
# OCRmyPDF is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OCRmyPDF is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with OCRmyPDF.  If not, see <http://www.gnu.org/licenses/>.

from ocrmypdf import hookimpl
from ocrmypdf.exec import tesseract
from ocrmypdf.pluginspec import OcrEngine


class TesseractOcrEngine(OcrEngine):
    @staticmethod
    def version():
        return tesseract.version()

    @staticmethod
    def creator_tag(options):
        tag = '-PDF' if options.pdf_renderer == 'sandwich' else ''
        return f"Tesseract OCR{tag} {TesseractOcrEngine.version()}"

    @staticmethod
    def languages():
        return tesseract.get_languages()

    @staticmethod
    def get_orientation(input_file, options):
        return tesseract.get_orientation(
            input_file,
            engine_mode=options.tesseract_oem,
            timeout=options.tesseract_timeout,
            tesseract_env=options.tesseract_env,
        )

    @staticmethod
    def generate_hocr(input_file, output_hocr, output_text, options):
        tesseract.generate_hocr(
            input_file=input_file,
            output_hocr=output_hocr,
            output_text=output_text,
            languages=options.language,
            engine_mode=options.tesseract_oem,
            tessconfig=options.tesseract_config,
            timeout=options.tesseract_timeout,
            pagesegmode=options.tesseract_pagesegmode,
            user_words=options.user_words,
            user_patterns=options.user_patterns,
            tesseract_env=options.tesseract_env,
        )

    @staticmethod
    def generate_pdf(input_file, output_pdf, output_text, options):
        tesseract.generate_pdf(
            input_file=input_file,
            output_pdf=output_pdf,
            output_text=output_text,
            languages=options.language,
            engine_mode=options.tesseract_oem,
            tessconfig=options.tesseract_config,
            timeout=options.tesseract_timeout,
            pagesegmode=options.tesseract_pagesegmode,
            user_words=options.user_words,
            user_patterns=options.user_patterns,
            tesseract_env=options.tesseract_env,
        )


@hookimpl
def get_ocr_engine():
    return TesseractOcrEngine()
