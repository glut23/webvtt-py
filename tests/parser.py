import os
import unittest

from webvtt import WebVTTParser
from webvtt.exceptions import MalformedFileError, MalformedCaptionError

SUBTITLES_DIR = os.path.dirname(os.path.dirname(__file__))
SUBTITLES_DIR = os.path.join(SUBTITLES_DIR, 'tests/subtitles')


class WebVTTParserTestCase(unittest.TestCase):

    def setUp(self):
        self.parser = WebVTTParser()

    def test_parser_valid_webvtt(self):
        self.assertTrue(self.parser.read(os.path.join(SUBTITLES_DIR, 'sample.vtt')).captions)

    def test_parser_invalid_webvtt(self):
        self.assertRaises(
            MalformedFileError,
            self.parser.read,
            os.path.join(SUBTITLES_DIR, 'invalid.vtt'))

    def test_parser_empty_file(self):
        self.assertRaises(
            MalformedFileError,
            self.parser.read,
            os.path.join(SUBTITLES_DIR, 'empty.vtt'))

    def test_parser_get_captions(self):
        self.assertEqual(
            len(self.parser.read(os.path.join(SUBTITLES_DIR, 'sample.vtt')).captions), 7)

    def test_parser_invalid_timeframe_line(self):
        self.assertRaises(
            MalformedCaptionError,
            self.parser.read,
            os.path.join(SUBTITLES_DIR, 'invalid_timeframe.vtt'))

    def test_parser_get_caption_data(self):
        self.parser.read(os.path.join(SUBTITLES_DIR, 'one_caption.vtt'))
        self.assertEqual(self.parser.captions[0].start, '00:00:00.500')
        self.assertEqual(self.parser.captions[0].end, '00:00:07.000')
        self.assertEqual(self.parser.captions[0].lines[0], 'Caption text #1')
        self.assertEqual(len(self.parser.captions[0].lines), 1)

    def test_caption_without_timeframe(self):
        self.assertRaises(
            MalformedCaptionError,
            self.parser.read,
            os.path.join(SUBTITLES_DIR, 'missing_timeframe.vtt'))
