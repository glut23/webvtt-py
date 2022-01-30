import os
import unittest
from shutil import rmtree, copy

import webvtt

from .generic import GenericParserTestCase


BASE_DIR = os.path.dirname(__file__)
OUTPUT_DIR = os.path.join(BASE_DIR, 'output')


class SRTCaptionsTestCase(GenericParserTestCase):

    def setUp(self):
        os.makedirs(OUTPUT_DIR)

    def tearDown(self):
        if os.path.exists(OUTPUT_DIR):
            rmtree(OUTPUT_DIR)

    def test_convert_from_srt_to_vtt_and_back_gives_same_file(self):
        copy(self._get_file('sample.srt'), OUTPUT_DIR)

        vtt = webvtt.from_srt(os.path.join(OUTPUT_DIR, 'sample.srt'))
        vtt.save_as_srt(os.path.join(OUTPUT_DIR, 'sample_converted.srt'))

        with open(os.path.join(OUTPUT_DIR, 'sample.srt'), 'r', encoding='utf-8') as f:
            original = f.read()

        with open(os.path.join(OUTPUT_DIR, 'sample_converted.srt'), 'r', encoding='utf-8') as f:
            converted = f.read()

        self.assertEqual(original.strip(), converted.strip())

    def test_convert_to_srt_with_styles(self):
        copy(self._get_file('styles2.vtt'), OUTPUT_DIR)
        copy(self._get_file('styles2.srt'), OUTPUT_DIR)

        vtt = webvtt.read(os.path.join(OUTPUT_DIR, 'styles2.vtt'))
        vtt.save_as_srt(os.path.join(OUTPUT_DIR, 'styles2_converted.srt'))

        with open(os.path.join(OUTPUT_DIR, 'styles2.srt'), 'r', encoding='utf-8') as f:
            original = f.read()

        with open(os.path.join(OUTPUT_DIR, 'styles2_converted.srt'), 'r', encoding='utf-8') as f:
            converted = f.read()

        self.assertEqual(original.strip(), converted.strip())
