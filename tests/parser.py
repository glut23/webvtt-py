import os
import unittest

from webvtt import WebVTTParser
from webvtt.exceptions import MalformedFileError

SUBTITLES_DIR = os.path.dirname(os.path.dirname(__file__))
SUBTITLES_DIR = os.path.join(SUBTITLES_DIR, 'tests/subtitles')


class WebVTTParserTestCase(unittest.TestCase):

    def setUp(self):
        self.parser = WebVTTParser()

    def test_parser_valid_webvtt(self):
        self.assertTrue(self.parser.read(os.path.join(SUBTITLES_DIR, 'sample.vtt')).is_valid())

    def test_parser_invalid_webvtt(self):
        self.assertRaises(
            MalformedFileError,
            self.parser.read,
            os.path.join(SUBTITLES_DIR, 'invalid.vtt'))