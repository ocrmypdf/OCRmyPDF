from pathlib import Path
from argparse import ArgumentParser, Namespace
from typing import Set
import logging
import os
from PIL import Image
from dotenv import load_dotenv

from google.cloud import vision
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential

from ocrmypdf.pluginspec import OcrEngine, OrientationConfidence
from ocrmypdf.helpers import Resolution
from ocrmypdf import hookimpl

log = logging.getLogger(__name__)
load_dotenv()

def init_google_vision():
    return vision.ImageAnnotatorClient()

def init_azure_form_recognizer():
    endpoint = os.getenv("AZURE_FORM_ENDPOINT")
    key = os.getenv("AZURE_FORM_KEY")
    return DocumentAnalysisClient(endpoint, AzureKeyCredential(key))

@hookimpl
def add_options(parser: ArgumentParser):
    hwr = parser.add_argument_group("Handwriting Recognition")
    hwr.add_argument(
        '--enable-handwriting',
        action='store_true',
        help="Enable experimental handwriting recognition support"
    )
    hwr.add_argument(
        '--handwriting-model',
        choices=['google-vision', 'azure-form-recognizer'],
        default='google-vision',
        help="Select the handwriting recognition service to use"
    )

class HandwritingRecognitionEngine(OcrEngine):
    """Implements handwriting recognition using cloud services."""

    _google_client = None
    _azure_client = None

    @classmethod
    def get_google_client(cls):
        if cls._google_client is None:
            cls._google_client = init_google_vision()
        return cls._google_client

    @classmethod
    def get_azure_client(cls):
        if cls._azure_client is None:
            cls._azure_client = init_azure_form_recognizer()
        return cls._azure_client

    @staticmethod
    def version() -> str:
        return "1.0.0"

    @staticmethod
    def creator_tag(options: Namespace) -> str:
        return f"Handwriting-Recognition-{options.handwriting_model}"

    def __str__(self):
        return f"Handwriting Recognition Engine {self.version()}"

    @staticmethod
    def languages(options: Namespace) -> Set[str]:
        if options.handwriting_model == 'google-vision':
            return {'eng', 'fra', 'deu', 'spa', 'ita'}  # Google Vision supports multiple languages
        return {'eng'}  # Azure Form Recognizer initially supports English

    @staticmethod
    def get_orientation(input_file: Path, options: Namespace) -> OrientationConfidence:
        # Use the selected service to detect orientation
        try:
            if options.handwriting_model == 'google-vision':
                client = HandwritingRecognitionEngine.get_google_client()
                with open(input_file, 'rb') as image_file:
                    content = image_file.read()
                image = vision.Image(content=content)
                response = client.document_text_detection(image=image)
                # Google Vision doesn't directly provide orientation confidence
                return OrientationConfidence(
                    angle=response.text_annotations[0].rotation if response.text_annotations else 0,
                    confidence=0.9 if response.text_annotations else 0.0
                )
            else:
                # Azure Form Recognizer doesn't provide direct orientation detection
                return OrientationConfidence(angle=0, confidence=0.0)
        except Exception as e:
            log.error(f"Orientation detection failed: {str(e)}")
            return OrientationConfidence(angle=0, confidence=0.0)

    @staticmethod
    def generate_hocr(
        input_file: Path,
        output_hocr: Path,
        output_text: Path,
        options: Namespace
    ) -> None:
        if not options.enable_handwriting:
            return
        
        try:
            if options.handwriting_model == 'google-vision':
                client = HandwritingRecognitionEngine.get_google_client()
                with open(input_file, 'rb') as image_file:
                    content = image_file.read()
                image = vision.Image(content=content)
                response = client.document_text_detection(image=image)
                
                # Generate hOCR output
                with open(output_hocr, 'w', encoding='utf-8') as hocr_file:
                    hocr_file.write('<?xml version="1.0" encoding="UTF-8"?>\n')
                    hocr_file.write('<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en">\n')
                    hocr_file.write('<head>\n<title>OCR Results</title>\n</head>\n<body>\n')
                    
                    # Write text annotations
                    for page in response.full_text_annotation.pages:
                        for block in page.blocks:
                            for paragraph in block.paragraphs:
                                words = []
                                for word in paragraph.words:
                                    word_text = ''.join([
                                        symbol.text for symbol in word.symbols
                                    ])
                                    words.append(word_text)
                                    
                                    # Get bounding box coordinates
                                    vertices = word.bounding_box.vertices
                                    bbox = f"{vertices[0].x} {vertices[0].y} {vertices[2].x} {vertices[2].y}"
                                    
                                    hocr_file.write(
                                        f'<span class="ocrx_word" title="bbox {bbox}">'
                                        f'{word_text}</span> '
                                    )
                                hocr_file.write('\n')
                    
                    hocr_file.write('</body>\n</html>')
                
                # Generate plain text output
                with open(output_text, 'w', encoding='utf-8') as text_file:
                    text_file.write(response.text)
                    
            else:  # Azure Form Recognizer
                client = HandwritingRecognitionEngine.get_azure_client()
                with open(input_file, 'rb') as image_file:
                    poller = client.begin_analyze_document(
                        "prebuilt-document",
                        document=image_file
                    )
                result = poller.result()
                
                # Generate hOCR and text output similar to Google Vision
                # Implementation details similar to above
                
        except Exception as e:
            log.error(f"Handwriting recognition failed: {str(e)}")
            raise

    @staticmethod
    def generate_pdf(*args, **kwargs):
        # Implementation similar to generate_hocr but produces PDF output
        raise NotImplementedError("PDF generation not yet implemented")