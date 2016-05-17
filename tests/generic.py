import os
import unittest

from webvtt import WebVTT


class GenericParserTestCase(unittest.TestCase):

    SUBTITLES_DIR = os.path.join(os.path.dirname(__file__), 'subtitles')

    def setUp(self):
        self.webvtt = WebVTT()

    def _get_file(self, filename):
        return os.path.join(self.SUBTITLES_DIR, filename)

