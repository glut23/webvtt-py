import os
from unittest import TestCase
from subprocess import Popen, PIPE
from shutil import rmtree

from webvtt import __version__

BASE_DIR = os.path.dirname(__file__)
OUTPUT_DIR = os.path.join(BASE_DIR, 'output')


class TestCLI(TestCase):

    def tearDown(self):
        if os.path.exists(OUTPUT_DIR):
            rmtree(OUTPUT_DIR)

    def test_help_is_displayed(self):
        output = Popen(['webvtt', '-h'], stdout=PIPE).communicate()[0].decode('utf-8')
        self.assertTrue('Usage' in output)

    def test_version_is_displayed(self):
        output = Popen(['webvtt', '--version'], stdout=PIPE).communicate()[0].decode('utf-8')
        self.assertEqual(output.rstrip(), __version__)

    def test_segmentation_with_defaults(self):
        args = [
            'webvtt',
            'segment',
            'tests/subtitles/sample.vtt',
            '--output',
            OUTPUT_DIR,
        ]
        Popen(args, stdout=PIPE).communicate()
        self.assertTrue(os.path.exists(os.path.join(OUTPUT_DIR, 'prog_index.m3u8')))

        # verify the expected segments are generated
        for i in range(7):
            self.assertTrue(os.path.exists(os.path.join(OUTPUT_DIR, 'fileSequence{}.webvtt'.format(i))))

        # verify there are no unexpected segments
        self.assertFalse(os.path.exists(os.path.join(OUTPUT_DIR, 'fileSequence8.webvtt')))

        # verify MPEGTS value
        with open(os.path.join(OUTPUT_DIR, 'fileSequence0.webvtt'), 'r', encoding='utf-8') as f:
            lines = f.readlines()
            self.assertIn('MPEGTS:900000', lines[1])

    def test_segmentation_with_custom_values(self):
        args = [
            'webvtt',
            'segment',
            'tests/subtitles/sample.vtt',
            '--output',
            OUTPUT_DIR,
            '--target-duration',
            '30',
            '--mpegts',
            '0',
        ]
        Popen(args, stdout=PIPE).communicate()

        # verify the expected segments are generated
        for i in range(3):
            self.assertTrue(os.path.exists(os.path.join(OUTPUT_DIR, 'fileSequence{}.webvtt'.format(i))))

        # verify there are no unexpected segments
        self.assertFalse(os.path.exists(os.path.join(OUTPUT_DIR, 'fileSequence3.webvtt')))

        # verify MPEGTS value
        with open(os.path.join(OUTPUT_DIR, 'fileSequence0.webvtt'), 'r', encoding='utf-8') as f:
            lines = f.readlines()
            self.assertIn('MPEGTS:0', lines[1])

    def test_segmentation_wrong_target_duration(self):
        args = [
            'webvtt',
            'segment',
            'tests/subtitles/sample.vtt',
            '--output',
            OUTPUT_DIR,
            '--target-duration',
            'text'
        ]
        output = Popen(args, stderr=PIPE).communicate()[1].decode('utf-8')
        self.assertIn('Invalid target duration.', output)

    def test_segmentation_invalid_mpegts(self):
        args = [
            'webvtt',
            'segment',
            'tests/subtitles/sample.vtt',
            '--output',
            OUTPUT_DIR,
            '--mpegts',
            'text'
        ]
        output = Popen(args, stderr=PIPE).communicate()[1].decode('utf-8')
        self.assertIn('Invalid MPEGTS value.', output)