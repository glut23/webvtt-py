import re

TIMESTAMP_PATTERN = re.compile('(\d+):(\d{2}):(\d{2})[.,](\d{3})')


class Caption(object):
    """
    Represents a caption.
    """
    def __init__(self, start='00:00:00.000', end='00:00:00.000', lines=None):
        self._start = self._parse_timestamp(start)
        self._end = self._parse_timestamp(end)

        # If lines is a string convert to a list
        if lines and isinstance(lines, str):
            lines = lines.splitlines()

        self.lines = lines or []

    def add_line(self, line):
        self.lines.append(line)

    def _to_seconds(self, hours, minutes, seconds, milliseconds):
        return hours * 3600 + minutes * 60 + seconds + milliseconds / 1000

    def _parse_timestamp(self, timestamp):
        res = re.match(TIMESTAMP_PATTERN, timestamp)
        return self._to_seconds(
            int(res.group(1)),  # hours
            int(res.group(2)),  # minutes
            int(res.group(3)),  # seconds
            int(res.group(4))  # milliseconds
        )

    def _to_timestamp(self, total_seconds):
        hours = int(total_seconds / 3600)
        minutes = int(total_seconds / 60 - hours * 60)
        seconds = total_seconds - hours * 3600 - minutes * 60
        return '{:02d}:{:02d}:{:06.3f}'.format(int(hours), int(minutes), seconds)

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
    def text(self):
        """Returns the captions lines as a text"""
        return '\n'.join(self.lines)


class GenericParser(object):
    """
    A generic parent class for all parsers.
    """
    def __init__(self):
        self.captions = []

    def _parse(self, file):
        # method to be overwritten  by child classes
        pass

    def read(self, file):
        self.captions = []
        self._parse(file)

        return self