from .generic import GenericParserTestCase

from webvtt import WebVTT
from webvtt.parsers import WebVTTParser
from webvtt.generic import Caption
from webvtt.exceptions import MalformedFileError, MalformedCaptionError


class WebVTTParserTestCase(GenericParserTestCase):

    def test_webvtt_parse_invalid_file(self):
        self.assertRaises(
            MalformedFileError,
            self.webvtt.read,
            self._get_file('invalid.vtt')
        )

    def test_webvtt_captions_not_found(self):
        self.assertRaises(
            FileNotFoundError,
            self.webvtt.read,
            'some_file'
        )

    def test_webvtt_total_length(self):
        self.assertEqual(
            self.webvtt.read(self._get_file('sample.vtt')).total_length,
            64
        )

    def test_webvtt_allows_identifiers(self):
        # Allowed by standard https://www.w3.org/TR/webvtt1/#introduction-other-features

        self.assertTrue(self.webvtt.read(self._get_file('optional_identifiers.vtt')).captions)

    def test_webvtt_total_length_no_parser(self):
        self.assertEqual(
            self.webvtt.total_length,
            0
        )

    def test_webvtt__parse_captions(self):
        self.assertTrue(self.webvtt.read(self._get_file('sample.vtt')).captions)

    def test_webvtt_parse_empty_file(self):
        self.assertRaises(
            MalformedFileError,
            self.webvtt.read,
            self._get_file('empty.vtt')
        )

    def test_webvtt_parse_get_captions(self):
        self.assertEqual(
            len(self.webvtt.read(self._get_file('sample.vtt')).captions),
            16
        )

    def test_webvtt_parse_invalid_timeframe_line(self):
        self.assertRaises(
            MalformedCaptionError,
            self.webvtt.read,
            self._get_file('invalid_timeframe.vtt')
        )

    def test_webvtt_parse_get_caption_data(self):
        self.webvtt.read(self._get_file('one_caption.vtt'))
        self.assertEqual(self.webvtt.captions[0].start_in_seconds, 0.5)
        self.assertEqual(self.webvtt.captions[0].start, '00:00:00.500')
        self.assertEqual(self.webvtt.captions[0].end_in_seconds, 7)
        self.assertEqual(self.webvtt.captions[0].end, '00:00:07.000')
        self.assertEqual(self.webvtt.captions[0].lines[0], 'Caption text #1')
        self.assertEqual(len(self.webvtt.captions[0].lines), 1)

    def test_webvtt_caption_without_timeframe(self):
        self.assertRaises(
            MalformedCaptionError,
            self.webvtt.read,
            self._get_file('missing_timeframe.vtt')
        )

    def test_webvtt_timestamps_format(self):
        self.webvtt.read(self._get_file('sample.vtt'))
        self.assertEqual(self.webvtt.captions[2].start, '00:00:11.890')
        self.assertEqual(self.webvtt.captions[2].end, '00:00:16.320')

    def test_parse_timestamp(self):
        caption = Caption(start='02:03:11.890')
        self.assertEqual(
            caption.start_in_seconds,
            7391.89
        )

    def test_captions_attribute(self):
        self.assertListEqual([], WebVTT().captions)

    def test_webvtt_timestamp_format(self):
        self.assertTrue(WebVTTParser()._validate_timeframe_line('00:00:00.000 --> 00:00:00.000'))
        self.assertTrue(WebVTTParser()._validate_timeframe_line('00:00.000 --> 00:00.000'))

    def test_metadata_headers(self):
        self.webvtt.read(self._get_file('metadata_headers.vtt'))
        self.assertEqual(len(self.webvtt.captions), 2)

    def test_metadata_headers_multiline(self):
        self.webvtt.read(self._get_file('metadata_headers_multiline.vtt'))
        self.assertEqual(len(self.webvtt.captions), 2)

    def test_clean_cue_tags(self):
        self.webvtt.read(self._get_file('cue_tags.vtt'))
        self.assertEqual(
            self.webvtt.captions[1].text,
            'Like a big-a pizza pie'
        )
        self.assertEqual(
            self.webvtt.captions[2].text,
            'That\'s amore'
        )
