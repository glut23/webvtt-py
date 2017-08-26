import os
import unittest
from shutil import rmtree, copy

from webvtt import WebVTT
from webvtt.exceptions import MissingFilenameError, MalformedCaptionError
from webvtt.generic import Caption, Style

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
        self.assertEqual(caption.start, '00:00:00.500')
        self.assertEqual(caption.start_in_seconds, 0.5)
        self.assertEqual(caption.end, '00:00:07.000')
        self.assertEqual(caption.end_in_seconds, 7)
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

    def test_sbv_conversion(self):
        os.makedirs(OUTPUT_DIR)
        copy(self._get_file('two_captions.sbv'), OUTPUT_DIR)

        self.webvtt.from_sbv(os.path.join(OUTPUT_DIR, 'two_captions.sbv'))
        self.webvtt.save()

        self.assertTrue(os.path.exists(os.path.join(OUTPUT_DIR, 'two_captions.vtt')))

        with open(os.path.join(OUTPUT_DIR, 'two_captions.vtt'), 'r', encoding='utf-8') as f:
            lines = [line.rstrip() for line in f.readlines()]

        expected_lines = [
            'WEBVTT',
            '',
            '00:00:00.378 --> 00:00:11.378',
            'Caption text #1',
            '',
            '00:00:11.378 --> 00:00:12.305',
            'Caption text #2 (line 1)',
            'Caption text #2 (line 2)',
        ]

        self.assertListEqual(lines, expected_lines)

    def test_save_to_other_location(self):
        target_path = os.path.join(OUTPUT_DIR, 'test_folder')
        os.makedirs(target_path)

        self.webvtt.read(self._get_file('one_caption.vtt')).save(target_path)
        self.assertTrue(os.path.exists(os.path.join(target_path, 'one_caption.vtt')))

    def test_save_specific_filename(self):
        target_path = os.path.join(OUTPUT_DIR, 'test_folder')
        os.makedirs(target_path)
        output_file = os.path.join(target_path, 'custom_name.vtt')

        self.webvtt.read(self._get_file('one_caption.vtt')).save(output_file)
        self.assertTrue(os.path.exists(output_file))

    def test_save_specific_filename_no_extension(self):
        target_path = os.path.join(OUTPUT_DIR, 'test_folder')
        os.makedirs(target_path)
        output_file = os.path.join(target_path, 'custom_name')

        self.webvtt.read(self._get_file('one_caption.vtt')).save(output_file)
        self.assertTrue(os.path.exists(os.path.join(target_path, 'custom_name.vtt')))

    def test_caption_timestamp_update(self):
        c = Caption('00:00:00.500', '00:00:07.000')
        c.start = '00:00:01.750'
        c.end = '00:00:08.250'

        self.assertEqual(c.start, '00:00:01.750')
        self.assertEqual(c.end, '00:00:08.250')

    def test_caption_timestamp_format(self):
        c = Caption('01:02:03.400', '02:03:04.500')
        self.assertEqual(c.start, '01:02:03.400')
        self.assertEqual(c.end, '02:03:04.500')

        c = Caption('02:03.400', '03:04.500')
        self.assertEqual(c.start, '00:02:03.400')
        self.assertEqual(c.end, '00:03:04.500')

    def test_caption_text(self):
        c = Caption(text=['Caption line #1', 'Caption line #2'])
        self.assertEqual(
            c.text,
            'Caption line #1\nCaption line #2'
        )

    def test_caption_receive_text(self):
        c = Caption(text='Caption line #1\nCaption line #2')

        self.assertEqual(
            len(c.lines),
            2
        )
        self.assertEqual(
            c.text,
            'Caption line #1\nCaption line #2'
        )

    def test_update_text(self):
        c = Caption(text='Caption line #1')
        c.text = 'Caption line #1 updated'
        self.assertEqual(
            c.text,
            'Caption line #1 updated'
        )

    def test_update_text_multiline(self):
        c = Caption(text='Caption line #1')
        c.text = 'Caption line #1\nCaption line #2'

        self.assertEqual(
            len(c.lines),
            2
        )

        self.assertEqual(
            c.text,
            'Caption line #1\nCaption line #2'
        )

    def test_update_text_wrong_type(self):
        c = Caption(text='Caption line #1')

        self.assertRaises(
            AttributeError,
            setattr,
            c,
            'text',
            123
        )

    def test_manipulate_lines(self):
        c = Caption(text=['Caption line #1', 'Caption line #2'])
        c.lines[0] = 'Caption line #1 updated'
        self.assertEqual(
            c.lines[0],
            'Caption line #1 updated'
        )

    def test_captions(self):
        self.webvtt.read(self._get_file('sample.vtt'))
        self.assertIsInstance(self.webvtt.captions, list)

    def test_captions_prevent_write(self):
        self.webvtt.read(self._get_file('sample.vtt'))
        self.assertRaises(
            AttributeError,
            setattr,
            self.webvtt,
            'captions',
            []
        )

    def test_sequence_iteration(self):
        self.webvtt.read(self._get_file('sample.vtt'))
        self.assertIsInstance(self.webvtt[0], Caption)
        self.assertEqual(len(self.webvtt), len(self.webvtt.captions))

    def test_save_no_filename(self):
        webvtt = WebVTT()
        self.assertRaises(
            MissingFilenameError,
            webvtt.save
        )

    def test_malformed_start_timestamp(self):
        self.assertRaises(
            MalformedCaptionError,
            Caption,
            '01:00'
        )

    def test_set_styles_from_text(self):
        style = Style()
        style.text = '::cue(b) {\n  color: peachpuff;\n}'
        self.assertListEqual(
            style.lines,
            ['::cue(b) {', '  color: peachpuff;', '}']
        )

    def test_get_styles_as_text(self):
        style = Style()
        style.lines = ['::cue(b) {', '  color: peachpuff;', '}']
        self.assertEqual(
            style.text,
            '::cue(b) {color: peachpuff;}'
        )