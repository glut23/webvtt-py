import re

from .generic import Caption
from .exceptions import MalformedFileError, MalformedCaptionError

TIMEFRAME_LINE_PATTERN = re.compile('\s*(\d+:\d{2}:\d{2}.\d{3})\s*-->\s*(\d+:\d{2}:\d{2}.\d{3})')


class WebVTTParser:

    def _parse_timeframe_line(self, line, line_number):
        """Parse timeframe line and return start and end timestamps"""
        res = re.match(TIMEFRAME_LINE_PATTERN, line)
        if not res:
            raise MalformedCaptionError('Invalid time format in line {}'.format(line_number))

        return res.group(1), res.group(2)

    def _parse(self):
        c = None
        for index, line in enumerate(self.lines[1:]):
            line = line.strip()
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
            self.lines = f.readlines()

        if len(self.lines) == 0:
            raise MalformedFileError('The file is empty')
        if 'WEBVTT' not in self.lines[0]:
            raise MalformedFileError('The file does not have a valid format')

        self._parse()

        return self