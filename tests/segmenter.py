import os
import unittest
from shutil import rmtree

from webvtt import WebVTTSegmenter, Caption
from webvtt.exceptions import InvalidCaptionsError
from webvtt.parser import WebVTTParser

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
SUBTITLES_DIR = os.path.join(BASE_DIR, 'tests/subtitles')
OUTPUT_DIR = os.path.join(BASE_DIR, 'tests/output')


class WebVTTSegmenterTestCase(unittest.TestCase):

    def setUp(self):
        self.segmenter = WebVTTSegmenter()

    def tearDown(self):
        if os.path.exists(OUTPUT_DIR):
            rmtree(OUTPUT_DIR)

    def _parse_captions(self, filename):
        self.parser = WebVTTParser().read(os.path.join(SUBTITLES_DIR, filename))

    def test_invalid_captions(self):
        self.assertRaises(
            InvalidCaptionsError,
            self.segmenter.segment,
            'text'
        )

    def test_single_invalid_caption(self):
        self.assertRaises(
            InvalidCaptionsError,
            self.segmenter.segment,
            [Caption(), Caption(), 'text', Caption()]
        )

    def test_total_segments(self):
        # segment with default 10 seconds
        self._parse_captions('sample.vtt')
        self.segmenter.segment(self.parser.captions, OUTPUT_DIR)
        self.assertEqual(self.segmenter.total_segments, 7)

        # segment with custom 30 seconds
        self._parse_captions('sample.vtt')
        self.segmenter.segment(self.parser.captions, OUTPUT_DIR, 30)
        self.assertEqual(self.segmenter.total_segments, 3)

    def test_output_folder_is_created(self):
        self.assertFalse(os.path.exists(OUTPUT_DIR))
        self._parse_captions('sample.vtt')
        self.segmenter.segment(self.parser.captions, OUTPUT_DIR)
        self.assertTrue(os.path.exists(OUTPUT_DIR))

    def test_segmentation_files_exist(self):
        self._parse_captions('sample.vtt')
        self.segmenter.segment(self.parser.captions, OUTPUT_DIR)
        for i in range(7):
            self.assertTrue(
                os.path.exists(os.path.join(OUTPUT_DIR, 'fileSequence{}.webvtt'.format(i)))
            )
        self.assertTrue(os.path.exists(os.path.join(OUTPUT_DIR, 'prog_index.m3u8')))

    def test_manifest_content(self):
        self._parse_captions('sample.vtt')
        self.segmenter.segment(self.parser.captions, OUTPUT_DIR, 10)

        with open(os.path.join(OUTPUT_DIR, 'prog_index.m3u8'), 'r', encoding='utf-8') as f:
            lines = [line.rstrip() for line in f.readlines()]

            expected_lines = [
                '#EXTM3U',
                '#EXT-X-TARGETDURATION:{}'.format(self.segmenter.seconds),
                '#EXT-X-VERSION:3',
                '#EXT-X-PLAYLIST-TYPE:VOD',
            ]

            for i in range(7):
                expected_lines.extend([
                    '#EXTINF:30.00000',
                    'fileSequence{}.webvtt'.format(i)
                ])

            expected_lines.append('#EXT-X-ENDLIST')

            for index, line in enumerate(expected_lines):
                self.assertEqual(lines[index], line)