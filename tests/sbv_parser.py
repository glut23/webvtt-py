from __future__ import absolute_import, unicode_literals

import webvtt

from .generic import GenericParserTestCase


class SBVParserTestCase(GenericParserTestCase):

    def test_sbv_parse_empty_file(self):
        self.assertRaises(
            webvtt.errors.MalformedFileError,
            webvtt.from_sbv,
            self._get_file('empty.vtt')  # We reuse this file as it is empty and serves the purpose.
        )

    def test_sbv_invalid_format(self):
        self.assertRaises(
            webvtt.errors.MalformedFileError,
            webvtt.from_sbv,
            self._get_file('invalid_format.sbv')
        )

    def test_sbv_total_length(self):
        self.assertEqual(
            webvtt.from_sbv(self._get_file('sample.sbv')).total_length,
            16
        )

    def test_sbv_parse_captions(self):
        self.assertEqual(
            len(webvtt.from_srt(self._get_file('sample.srt')).captions),
            5
        )

    def test_sbv_missing_timeframe_line(self):
        self.assertRaises(
            webvtt.errors.MalformedCaptionError,
            webvtt.from_sbv,
            self._get_file('missing_timeframe.sbv')
        )

    def test_sbv_missing_caption_text(self):
        self.assertRaises(
            webvtt.errors.MalformedCaptionError,
            webvtt.from_sbv,
            self._get_file('missing_caption_text.sbv')
        )

    def test_sbv_invalid_timestamp(self):
        self.assertRaises(
            webvtt.errors.MalformedCaptionError,
            webvtt.from_sbv,
            self._get_file('invalid_timeframe.sbv')
        )

    def test_sbv_timestamps_format(self):
        vtt = webvtt.from_sbv(self._get_file('sample.sbv'))
        self.assertEqual(vtt.captions[1].start, '00:00:11.378')
        self.assertEqual(vtt.captions[1].end, '00:00:12.305')

    def test_sbv_timestamps_in_seconds(self):
        vtt = webvtt.from_sbv(self._get_file('sample.sbv'))
        self.assertEqual(vtt.captions[1].start_in_seconds, 11.378)
        self.assertEqual(vtt.captions[1].end_in_seconds, 12.305)

    def test_sbv_get_caption_text(self):
        vtt = webvtt.from_sbv(self._get_file('sample.sbv'))
        self.assertEqual(vtt.captions[1].text, 'Caption text #2')

    def test_sbv_get_caption_text_multiline(self):
        vtt = webvtt.from_sbv(self._get_file('sample.sbv'))
        self.assertEqual(
            vtt.captions[2].text,
            'Caption text #3 (line 1)\nCaption text #3 (line 2)'
        )
        self.assertListEqual(
            vtt.captions[2].lines,
            ['Caption text #3 (line 1)', 'Caption text #3 (line 2)']
        )
