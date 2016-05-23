import re

from webvtt.exceptions import MalformedFileError, MalformedCaptionError
from webvtt.generic import Caption
from .srt import SRTParser


class WebVTTParser(SRTParser):
    """
    WebVTT parser.
    """

    TIMEFRAME_LINE_PATTERN = re.compile('\s*(\d+:\d{2}:\d{2}.\d{3})\s*-->\s*(\d+:\d{2}:\d{2}.\d{3})')

    def _parse(self, file):
        c = None

        lines = self._read_lines(file)

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