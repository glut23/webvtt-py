import os
import unittest
from shutil import rmtree, copy

from webvtt import WebVTT
from webvtt.srt import SRTCaptions

BASE_DIR = os.path.dirname(__file__)
SUBTITLES_DIR = os.path.join(BASE_DIR, 'subtitles')
OUTPUT_DIR = os.path.join(BASE_DIR, 'output')

class SRTCaptionsTestCase(unittest.TestCase):

    def setUp(self):
        self.webvtt = WebVTT()
        self.srtcaptions = SRTCaptions()

        os.makedirs(OUTPUT_DIR)

    def _get_file(self, filename):
        return os.path.join(SUBTITLES_DIR, filename)

    def tearDown(self):
        if os.path.exists(OUTPUT_DIR):
            rmtree(OUTPUT_DIR)

    def test_convert_from_srt_to_vtt_and_back_gives_same_file(self):
        copy(self._get_file('sample.srt'), OUTPUT_DIR)

        self.webvtt.from_srt(os.path.join(OUTPUT_DIR, 'sample.srt'))
        self.webvtt.save()

        self.srtcaptions.from_vtt(os.path.join(OUTPUT_DIR, 'sample.vtt'))
        self.srtcaptions.save(os.path.join(OUTPUT_DIR, 'sample_converted.srt'))

        with open(os.path.join(OUTPUT_DIR, 'sample.srt'), 'r', encoding='utf-8') as f:
            original = f.read()

        with open(os.path.join(OUTPUT_DIR, 'sample_converted.srt'), 'r', encoding='utf-8') as f:
            converted = f.read()

        self.assertEqual(original.strip(), converted.strip())


