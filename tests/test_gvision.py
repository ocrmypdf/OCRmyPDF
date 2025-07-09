import unittest
from ocrmypdf.builtin_plugins.gvision import GVisionOcrEngine
from argparse import Namespace
import pathlib

class TestGVisionOcrEngine(unittest.TestCase):
    def setUp(self):
        self.options = Namespace(gcv_keyfile=None)
        self.engine = GVisionOcrEngine(self.options)

    def test_initialization(self):
        self.assertIsNotNone(self.engine)
        self.assertIsNone(self.engine.gcv_client)


    def test_generate_hocr(self):
        input_file = pathlib.Path('tests/resources/crom.png')
        output_hocr = pathlib.Path('output.hocr')
        output_text = pathlib.Path('output.txt')
        
        try:
            self.engine.generate_hocr(input_file, output_hocr, output_text, self.options)
            self.assertTrue(output_hocr.exists())
            self.assertTrue(output_text.exists())
        except Exception as e:
            self.fail(f"generate_hocr raised an exception: {e}")

if __name__ == '__main__':
    unittest.main()