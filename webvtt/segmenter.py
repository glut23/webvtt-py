import os
from math import ceil

from .exceptions import InvalidCaptionsError
from .generic import Caption


class WebVTTSegmenter(object):
    DEFAULT_MPEGTS = 900000
    DEFAULT_SECONDS = 10  # default number of seconds per segment

    def __init__(self):
        self.total_segments = 0
        self._output_folder = ''
        self._seconds = 0

    @property
    def seconds(self):
        return self._seconds

    def _validate_captions(self, captions):
        """validates that the captions is a list and all the captions are instances of Caption"""
        if not isinstance(captions, list):
            return False
        for c in captions:
            if not isinstance(c, Caption):
                return False
        return True

    def _write_segments(self):
        for index in range(self.total_segments):
            current_second = index * self._seconds
            segment_file = os.path.join(self._output_folder, 'fileSequence{}.webvtt'.format(index))

            with open(segment_file, 'w', encoding='utf-8') as f:
                pass

    def _write_manifest(self):
        manifest_file = os.path.join(self._output_folder, 'prog_index.m3u8')
        with open(manifest_file, 'w', encoding='utf-8') as f:
            f.write('#EXTM3U\n')
            f.write('#EXT-X-TARGETDURATION:\n')

    def segment(self, captions, output='', seconds=DEFAULT_SECONDS):
        if not self._validate_captions(captions):
            raise InvalidCaptionsError('The captions provided are invalid')

        self.total_segments = int(ceil(captions[-1].end_in_seconds / seconds))
        self._output_folder = output
        self._seconds = seconds

        output_folder = os.path.join(os.getcwd(), output)
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        self._write_segments()
        self._write_manifest()

