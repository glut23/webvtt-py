import re

from webvtt.exceptions import MalformedFileError, MalformedCaptionError
from webvtt.generic import GenericParser, Caption


class TextBasedParser(GenericParser):
    """
    Parser for plain text caption files.
    This is a generic class, do not use directly.
    """

    TIMEFRAME_LINE_PATTERN = ''

    def _read_content(self, file):
        with open(file, encoding='utf-8') as f:
            lines = [line.rstrip() for line in f.readlines()]

        if not lines:
            raise MalformedFileError('The file is empty.')

        return lines

    def _parse_timeframe_line(self, line):
        """Parse timeframe line and return start and end timestamps."""
        tf = self._validate_timeframe_line(line)
        if not tf:
            raise MalformedCaptionError('Invalid time format')

        return tf.group(1), tf.group(2)

    def _validate_timeframe_line(self, line):
        return re.match(self.TIMEFRAME_LINE_PATTERN, line)

    def _is_timeframe_line(self, line):
        """
        This method returns True if the line contains the timeframes.
        To be implemented by child classes.
        """
        return False

    def _should_skip_line(self, line, index, caption):
        """
        This method returns True for a line that should be skipped.
        To be implemented by child classes.
        """
        return False

    def _parse(self, lines):
        c = None

        for index, line in enumerate(lines):
            if self._is_timeframe_line(line):
                try:
                    start, end = self._parse_timeframe_line(line)
                except MalformedCaptionError as e:
                    raise MalformedCaptionError('{} in line! {}'.format(e, index + 1))
                c = Caption(start, end)
            elif self._should_skip_line(line, index, c):  # allow child classes to skip lines based on the content
                continue
            elif line:
                if c is None:
                    raise MalformedCaptionError('Caption missing timeframe in line {}.'.format(index + 1))
                else:
                    c.add_line(line)
            else:
                if c is None:
                    continue
                if not c.lines:
                    raise MalformedCaptionError('Caption missing text in line {}.'.format(index + 1))

                self.captions.append(c)
                c = None

        if c is not None and c.lines:
            self.captions.append(c)


class SRTParser(TextBasedParser):
    """
    SRT parser.
    """

    TIMEFRAME_LINE_PATTERN = re.compile('\s*(\d+:\d{2}:\d{2},\d{3})\s*-->\s*(\d+:\d{2}:\d{2},\d{3})')

    def _validate(self, lines):
        if len(lines) < 2 or lines[0] != '1' or not self._validate_timeframe_line(lines[1]):
            raise MalformedFileError('The file does not have a valid format.')

    def _is_timeframe_line(self, line):
        return '-->' in line

    def _should_skip_line(self, line, index, caption):
        return caption is None and line.isdigit()


class WebVTTParser(SRTParser):
    """
    WebVTT parser.
    """

    TIMEFRAME_LINE_PATTERN = re.compile('\s*((?:\d+:)?\d{2}:\d{2}.\d{3})\s*-->\s*((?:\d+:)?\d{2}:\d{2}.\d{3})')
    METADATA_HEADER = re.compile('\w+:\s*\w+')

    def _validate(self, lines):
        if 'WEBVTT' not in lines[0]:
            raise MalformedFileError('The file does not have a valid format')

    def _should_skip_line(self, line, index, caption):
        is_header_title = index == 0 and line == 'WEBVTT'
        is_metadata_header = len(self.captions) == 0 and re.match(self.METADATA_HEADER, line)
        return is_header_title or is_metadata_header


class SBVParser(TextBasedParser):
    """
    YouTube SBV parser.
    """

    TIMEFRAME_LINE_PATTERN = re.compile('\s*(\d+:\d{2}:\d{2}.\d{3}),(\d+:\d{2}:\d{2}.\d{3})')

    def _validate(self, lines):
        if not self._validate_timeframe_line(lines[0]):
            raise MalformedFileError('The file does not have a valid format')

    def _is_timeframe_line(self, line):
        return self._validate_timeframe_line(line)