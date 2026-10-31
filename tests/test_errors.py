import io
import unittest

import webvtt
from webvtt.errors import (
    WebVTTError,
    MalformedFileError,
    MalformedCaptionError,
    MissingFilenameError
    )


class TestErrors(unittest.TestCase):

    def test_errors_are_webvtt_errors(self):
        for error in (
                MalformedFileError,
                MalformedCaptionError,
                MissingFilenameError
                ):
            with self.subTest(error=error):
                self.assertTrue(issubclass(error, WebVTTError))

    def test_malformed_errors_are_value_errors(self):
        for error in (MalformedFileError, MalformedCaptionError):
            with self.subTest(error=error):
                self.assertTrue(issubclass(error, ValueError))

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
