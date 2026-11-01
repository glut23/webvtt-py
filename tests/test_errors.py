import io
import unittest

import webvtt
from webvtt.errors import (
    WebVTTError,
    MalformedFileError,
    MalformedCaptionError,
    MalformedRegionError,
    MissingFilenameError
    )


class TestErrors(unittest.TestCase):

    def test_errors_are_webvtt_errors(self):
        for error in (
                MalformedFileError,
                MalformedCaptionError,
                MalformedRegionError,
                MissingFilenameError
                ):
            with self.subTest(error=error):
                self.assertTrue(issubclass(error, WebVTTError))

    def test_malformed_errors_are_value_errors(self):
        for error in (MalformedFileError, MalformedCaptionError,
                      MalformedRegionError):
            with self.subTest(error=error):
                self.assertTrue(issubclass(error, ValueError))

    def test_region_error_is_a_caption_error(self):
        self.assertTrue(
            issubclass(MalformedRegionError, MalformedCaptionError)
            )

    def test_catch_region_error_as_caption_error(self):
        for call in (
                lambda: webvtt.from_string(
                    'WEBVTT\n\nREGION\nwidth:abc\n', strict=True
                    ),
                lambda: webvtt.Region(width='abc'),
                lambda: webvtt.Region.from_string('id:fred --> x')):
            with self.assertRaises(MalformedRegionError) as cm:
                call()
            self.assertIsInstance(cm.exception, MalformedCaptionError)

    def test_cue_setting_error_is_not_a_region_error(self):
        with self.assertRaises(MalformedCaptionError) as cm:
            webvtt.CueSettings(region='not valid')
        self.assertNotIsInstance(cm.exception, MalformedRegionError)

    def test_missing_filename_is_not_a_value_error(self):
        self.assertFalse(issubclass(MissingFilenameError, ValueError))

    def test_catch_webvtt_error(self):
        with self.assertRaises(WebVTTError):
            webvtt.from_buffer(io.StringIO('not WebVTT'))

        with self.assertRaises(WebVTTError):
            webvtt.Caption('invalid', '00:00:01.000')

        with self.assertRaises(WebVTTError):
            webvtt.WebVTT().save()

    def test_catch_value_error(self):
        with self.assertRaises(ValueError):
            webvtt.from_buffer(io.StringIO('not WebVTT'))

        with self.assertRaises(ValueError):
            webvtt.Caption('invalid', '00:00:01.000')
