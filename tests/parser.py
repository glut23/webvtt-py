import os
import unittest
from datetime import time

from webvtt import WebVTTParser
from webvtt.exceptions import MalformedFileError, MalformedCaptionError
from webvtt.generic import Caption

SUBTITLES_DIR = os.path.dirname(os.path.dirname(__file__))
SUBTITLES_DIR = os.path.join(SUBTITLES_DIR, 'tests/subtitles')


class WebVTTParserTestCase(unittest.TestCase):

    def setUp(self):
        self.parser = WebVTTParser()

    def _get_file(self, filename):
        return os.path.join(SUBTITLES_DIR, filename)

    def test_parser_valid_webvtt(self):
        self.assertTrue(self.parser.read(self._get_file('sample.vtt')).captions)

    def test_parser_invalid_webvtt(self):
        self.assertRaises(
            MalformedFileError,
            self.parser.read,
            self._get_file('invalid.vtt')
        )

    def test_total_length(self):
        self.assertEqual(
            self.parser.read(self._get_file('sample.vtt')).total_length,
            64
        )

    def test_parser_empty_file(self):
        self.assertRaises(
            MalformedFileError,
            self.parser.read,
            self._get_file('empty.vtt')
        )

    def test_parser_get_captions(self):
        self.assertEqual(
            len(self.parser.read(self._get_file('sample.vtt')).captions),
            16
        )

    def test_parser_invalid_timeframe_line(self):
        self.assertRaises(
            MalformedCaptionError,
            self.parser.read,
            self._get_file('invalid_timeframe.vtt')
        )

    def test_parser_get_caption_data(self):
        self.parser.read(self._get_file('one_caption.vtt'))
        self.assertEqual(self.parser.captions[0].start, 0.5)
        self.assertEqual(self.parser.captions[0].start_as_timestamp, '00:00:00.500')
        self.assertEqual(self.parser.captions[0].end, 7)
        self.assertEqual(self.parser.captions[0].end_as_timestamp, '00:00:07.000')
        self.assertEqual(self.parser.captions[0].lines[0], 'Caption text #1')
        self.assertEqual(len(self.parser.captions[0].lines), 1)

    def test_caption_without_timeframe(self):
        self.assertRaises(
            MalformedCaptionError,
            self.parser.read,
            self._get_file('missing_timeframe.vtt')
        )

    def test_timestamps_format(self):
        self.parser.read(self._get_file('sample.vtt'))
        self.assertEqual(self.parser.captions[2].start_as_timestamp, '00:00:11.890')
        self.assertEqual(self.parser.captions[2].end_as_timestamp, '00:00:16.320')

    def test_parse_timestamp(self):
        self.assertEqual(
            self.parser._parse_timestamp('02:03:11.890'),
            7391.89
        )

    def test_seconds_conversion(self):
        self.assertEqual(
            self.parser._to_seconds(2, 3, 11, 890),
            7391.89
        )