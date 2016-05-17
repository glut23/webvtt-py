import re

from webvtt.exceptions import MalformedFileError, MalformedCaptionError
from webvtt.generic import GenericParser, Caption

TIMEFRAME_LINE_PATTERN = re.compile('\s*(\d+:\d{2}:\d{2}.\d{3})\s*-->\s*(\d+:\d{2}:\d{2}.\d{3})')


class WebVTTParser(GenericParser):

    def _parse_timeframe_line(self, line, line_number):
        """Parse timeframe line and return start and end timestamps"""
        res = re.match(TIMEFRAME_LINE_PATTERN, line)
        if not res:
            raise MalformedCaptionError('Invalid time format in line {}'.format(line_number))

        start = self._parse_timestamp(res.group(1))
        end = self._parse_timestamp(res.group(2))

        return start, end

    def _parse(self, file):
        c = None

        with open(file, encoding='utf-8') as f:
            lines = [line.rstrip() for line in f.readlines()]

        if len(lines) == 0:
            raise MalformedFileError('The file is empty')
        if 'WEBVTT' not in lines[0]:
            raise MalformedFileError('The file does not have a valid format')

        for index, line in enumerate(lines[1:]):
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

    @property
    def total_length(self):
        return int(self.captions[-1].end) - int(self.captions[0].start)