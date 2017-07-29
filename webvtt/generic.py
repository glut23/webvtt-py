import re

from webvtt.exceptions import MalformedCaptionError

TIMESTAMP_PATTERN = re.compile('(\d+)?:?(\d{2}):(\d{2})[.,](\d{3})')


class Caption(object):
    """
    Represents a caption.
    """
    def __init__(self, start='00:00:00.000', end='00:00:00.000', text=None):
        self.start = start
        self.end = end

        # If lines is a string convert to a list
        if text and isinstance(text, str):
            text = text.splitlines()

        self._lines = text or []

    def add_line(self, line):
        self.lines.append(line)

    def _to_seconds(self, hours, minutes, seconds, milliseconds):
        return hours * 3600 + minutes * 60 + seconds + milliseconds / 1000

    def _parse_timestamp(self, timestamp):
        res = re.match(TIMESTAMP_PATTERN, timestamp)
        if not res:
            raise MalformedCaptionError('Invalid timestamp: {}'.format(timestamp))

        values = list(map(lambda x: int(x) if x else 0, res.groups()))
        return self._to_seconds(*values)

    def _to_timestamp(self, total_seconds):
        hours = int(total_seconds / 3600)
        minutes = int(total_seconds / 60 - hours * 60)
        seconds = total_seconds - hours * 3600 - minutes * 60
        return '{:02d}:{:02d}:{:06.3f}'.format(hours, minutes, seconds)

    @property
    def start_in_seconds(self):
        return self._start

    @property
    def end_in_seconds(self):
        return self._end

    @property
    def start(self):
        return self._to_timestamp(self._start)

    @start.setter
    def start(self, value):
        self._start = self._parse_timestamp(value)

    @property
    def end(self):
        return self._to_timestamp(self._end)

    @end.setter
    def end(self, value):
        self._end = self._parse_timestamp(value)

    @property
    def lines(self):
        return self._lines

    @property
    def text(self):
        """Returns the captions lines as a text"""
        return '\n'.join(self.lines)

    @text.setter
    def text(self, value):
        if not isinstance(value, str):
            raise AttributeError('String value expected but received {}.'.format(type(value)))

        self._lines = value.splitlines()


class GenericParser(object):
    """
    A generic parent class for all parsers.
    """
    def __init__(self):
        self._captions = []

    def _parse(self, content):
        # method to be overwritten by child classes
        pass

    def _read_content(self, file):
        # method to be overwritten by child classes
        return

    def _validate(self, content):
        # method to be overwritten by child classes
        pass

    def read(self, file):
        """Reads the captions file."""
        self._captions = []

        content = self._read_content(file)
        self._validate(content)
        self._parse(content)

        return self

    @property
    def captions(self):
        return self._captions