import re

from .generic import Caption
from .exceptions import MalformedFileError, MalformedCaptionError

TIMEFRAME_LINE_PATTERN = re.compile('\s*(\d+:\d{2}:\d{2}.\d{3})\s*-->\s*(\d+:\d{2}:\d{2}.\d{3})')
TIMESTAMP_PATTERN = re.compile('(\d+):(\d{2}):(\d{2}).(\d{3})')


class WebVTT:

    def __init__(self):
        self.captions = []

    def _to_seconds(self, hours, minutes, seconds, milliseconds):
        return hours * 3600 + minutes * 60 + seconds + milliseconds / 1000

    def _parse_timeframe_line(self, line, line_number):
        """Parse timeframe line and return start and end timestamps"""
        res = re.match(TIMEFRAME_LINE_PATTERN, line)
        if not res:
            raise MalformedCaptionError('Invalid time format in line {}'.format(line_number))

        start = self._parse_timestamp(res.group(1))
        end = self._parse_timestamp(res.group(2))

        return start, end

    def _parse_timestamp(self, timestamp):
        res = re.match(TIMESTAMP_PATTERN, timestamp)
        return self._to_seconds(
            int(res.group(1)),  # hours
            int(res.group(2)),  # minutes
            int(res.group(3)),  # seconds
            int(res.group(4))  # miliseconds
        )

    def _parse(self, lines):
        c = None
        for index, line in enumerate(lines):
            if '-->' in line:
                start, end = self._parse_timeframe_line(line, index)
                c = Caption(start, end)
            elif len(line) > 0:
                if c is None:
                    raise MalformedCaptionError('Caption missing timeframe in line {}'.format(index + 1))
                else:
                    c.add_line(line)
            else:
                if c is None:
                    continue
                if not c.lines:
                    raise MalformedCaptionError('Caption missing text in line {}'.format(index + 1))

                self.captions.append(c)
                c = None

        if c is not None and c.lines:
            self.captions.append(c)

    def read(self, file):
        self.captions = []

        with open(file, encoding='utf-8') as f:
            lines = [line.rstrip() for line in f.readlines()]

        if len(lines) == 0:
            raise MalformedFileError('The file is empty')
        if 'WEBVTT' not in lines[0]:
            raise MalformedFileError('The file does not have a valid format')

        self._parse(lines[1:])

        return self

    @property
    def total_length(self):
        return int(self.captions[-1].end) - int(self.captions[0].start)