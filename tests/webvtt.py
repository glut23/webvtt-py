import os
import unittest
from shutil import rmtree, copy

from webvtt import WebVTT
from webvtt.generic import Caption

BASE_DIR = os.path.dirname(__file__)
SUBTITLES_DIR = os.path.join(BASE_DIR, 'subtitles')
OUTPUT_DIR = os.path.join(BASE_DIR, 'output')


class WebVTTTestCase(unittest.TestCase):

    def setUp(self):
        self.webvtt = WebVTT()

    def _get_file(self, filename):
        return os.path.join(SUBTITLES_DIR, filename)

    def tearDown(self):
        if os.path.exists(OUTPUT_DIR):
            rmtree(OUTPUT_DIR)

    def test_create_caption(self):
        caption = Caption('00:00:00.500', '00:00:07.000', ['Caption test line 1', 'Caption test line 2'])
        self.assertEqual(caption.start_as_timestamp, '00:00:00.500')
        self.assertEqual(caption.start, 0.5)
        self.assertEqual(caption.end_as_timestamp, '00:00:07.000')
        self.assertEqual(caption.end, 7)
        self.assertEqual(caption.lines, ['Caption test line 1', 'Caption test line 2'])

    def test_save_captions(self):
        os.makedirs(OUTPUT_DIR)
        copy(self._get_file('one_caption.vtt'), OUTPUT_DIR)

        self.webvtt.read(os.path.join(OUTPUT_DIR, 'one_caption.vtt'))
        new_caption = Caption('00:00:07.000', '00:00:11.890', ['New caption text line1', 'New caption text line2'])
        self.webvtt.captions.append(new_caption)
        self.webvtt.save()

        with open(os.path.join(OUTPUT_DIR, 'one_caption.vtt'), 'r', encoding='utf-8') as f:
            lines = [line.rstrip() for line in f.readlines()]

        expected_lines = [
            'WEBVTT',
            '',
            '00:00:00.500 --> 00:00:07.000',
            'Caption text #1',
            '',
            '00:00:07.000 --> 00:00:11.890',
            'New caption text line1',
            'New caption text line2'
        ]

        self.assertListEqual(lines, expected_lines)

    def test_srt_conversion(self):
        os.makedirs(OUTPUT_DIR)
        copy(self._get_file('one_caption.srt'), OUTPUT_DIR)

        self.webvtt.from_srt(os.path.join(OUTPUT_DIR, 'one_caption.srt'))
        self.webvtt.save()

        self.assertTrue(os.path.exists(os.path.join(OUTPUT_DIR, 'one_caption.vtt')))

        with open(os.path.join(OUTPUT_DIR, 'one_caption.vtt'), 'r', encoding='utf-8') as f:
            lines = [line.rstrip() for line in f.readlines()]

        expected_lines = [
            'WEBVTT',
            '',
            '00:00:00.500 --> 00:00:07.000',
            'Caption text #1',
        ]

        self.assertListEqual(lines, expected_lines)