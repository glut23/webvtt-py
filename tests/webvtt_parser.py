from .generic import GenericParserTestCase

import webvtt
from webvtt.parsers import WebVTTParser
from webvtt.structures import Caption
from webvtt.errors import MalformedFileError, MalformedCaptionError


class WebVTTParserTestCase(GenericParserTestCase):

    def test_webvtt_parse_invalid_file(self):
        self.assertRaises(
            MalformedFileError,
            webvtt.read,
            self._get_file('invalid.vtt')
        )

    def test_webvtt_captions_not_found(self):
        self.assertRaises(
            FileNotFoundError,
            webvtt.read,
            'some_file'
        )

    def test_webvtt_total_length(self):
        self.assertEqual(
            webvtt.read(self._get_file('sample.vtt')).total_length,
            64
        )

    def test_webvtt_total_length_no_parser(self):
        self.assertEqual(
            webvtt.WebVTT().total_length,
            0
        )

    def test_webvtt__parse_captions(self):
        self.assertTrue(webvtt.read(self._get_file('sample.vtt')).captions)

    def test_webvtt_parse_empty_file(self):
        self.assertRaises(
            MalformedFileError,
            webvtt.read,
            self._get_file('empty.vtt')
        )

    def test_webvtt_parse_get_captions(self):
        self.assertEqual(
            len(webvtt.read(self._get_file('sample.vtt')).captions),
            16
        )

    def test_webvtt_parse_invalid_timeframe_line(self):
        self.assertRaises(
            MalformedCaptionError,
            webvtt.read,
            self._get_file('invalid_timeframe.vtt')
        )

    def test_webvtt_parse_invalid_timeframe_in_cue_text(self):
        self.assertRaises(
            MalformedCaptionError,
            webvtt.read,
            self._get_file('invalid_timeframe_in_cue_text.vtt')
        )

    def test_webvtt_parse_get_caption_data(self):
        vtt = webvtt.read(self._get_file('one_caption.vtt'))
        self.assertEqual(vtt.captions[0].start_in_seconds, 0.5)
        self.assertEqual(vtt.captions[0].start, '00:00:00.500')
        self.assertEqual(vtt.captions[0].end_in_seconds, 7)
        self.assertEqual(vtt.captions[0].end, '00:00:07.000')
        self.assertEqual(vtt.captions[0].lines[0], 'Caption text #1')
        self.assertEqual(len(vtt.captions[0].lines), 1)

    def test_webvtt_caption_without_timeframe(self):
        self.assertRaises(
            MalformedCaptionError,
            webvtt.read,
            self._get_file('missing_timeframe.vtt')
        )

    def test_webvtt_caption_without_cue_text(self):
        vtt = webvtt.read(self._get_file('missing_caption_text.vtt'))
        self.assertEqual(len(vtt.captions), 5)

    def test_webvtt_timestamps_format(self):
        vtt = webvtt.read(self._get_file('sample.vtt'))
        self.assertEqual(vtt.captions[2].start, '00:00:11.890')
        self.assertEqual(vtt.captions[2].end, '00:00:16.320')

    def test_parse_timestamp(self):
        caption = Caption(start='02:03:11.890')
        self.assertEqual(
            caption.start_in_seconds,
            7391.89
        )

    def test_captions_attribute(self):
        self.assertListEqual([], webvtt.WebVTT().captions)

    def test_webvtt_timestamp_format(self):
        self.assertTrue(WebVTTParser()._validate_timeframe_line('00:00:00.000 --> 00:00:00.000'))
        self.assertTrue(WebVTTParser()._validate_timeframe_line('00:00.000 --> 00:00.000'))

    def test_metadata_headers(self):
        vtt = webvtt.read(self._get_file('metadata_headers.vtt'))
        self.assertEqual(len(vtt.captions), 2)

    def test_metadata_headers_multiline(self):
        vtt = webvtt.read(self._get_file('metadata_headers_multiline.vtt'))
        self.assertEqual(len(vtt.captions), 2)

    def test_parse_identifiers(self):
        vtt = webvtt.read(self._get_file('using_identifiers.vtt'))
        self.assertEqual(len(vtt.captions), 6)

        self.assertEqual(vtt.captions[1].identifier, 'second caption')
        self.assertEqual(vtt.captions[2].identifier, None)
        self.assertEqual(vtt.captions[3].identifier, '4')

    def test_parse_with_comments(self):
        vtt = webvtt.read(self._get_file('comments.vtt'))
        self.assertEqual(len(vtt.captions), 3)
        self.assertListEqual(
            vtt.captions[0].lines,
            ['- Ta en kopp varmt te.',
             '- Det är inte varmt.']
        )
        self.assertEqual(
            vtt.captions[2].text,
            '- Ta en kopp'
        )

    def test_parse_styles(self):
        vtt = webvtt.read(self._get_file('styles.vtt'))
        self.assertEqual(len(vtt.captions), 1)
        self.assertEqual(
            vtt.styles[0].text,
            '::cue {background-image: linear-gradient(to bottom, dimgray, lightgray);color: papayawhip;}'
        )

    def test_clean_cue_tags(self):
        vtt = webvtt.read(self._get_file('cue_tags.vtt'))
        self.assertEqual(
            vtt.captions[1].text,
            'Like a big-a pizza pie'
        )
        self.assertEqual(
            vtt.captions[2].text,
            'That\'s amore'
        )

    def test_parse_captions_with_bom(self):
        vtt = webvtt.read(self._get_file('captions_with_bom.vtt'))
        self.assertEqual(len(vtt.captions), 4)

    def test_empty_lines_are_not_included_in_result(self):
        vtt = webvtt.read(self._get_file('netflix_chicas_del_cable.vtt'))
        self.assertEqual(vtt.captions[0].text, "[Alba] En 1928,")
        self.assertEqual(
            vtt.captions[-2].text,
            "Diez años no son suficientes\npara olvidarte..."
        )
