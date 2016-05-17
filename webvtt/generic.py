import re

TIMESTAMP_PATTERN = re.compile('(\d+):(\d{2}):(\d{2}).(\d{3})')


class Caption(object):
    """
    Represents a caption
    """
    def __init__(self, start=0, end=0, lines=None):
        self.start = start
        self.end = end
        self.lines = lines or []

    def add_line(self, line):
        self.lines.append(line)

    def _to_timestamp(self, total_seconds):
        hours = int(total_seconds / 3600)
        minutes = int(total_seconds / 60 - hours * 60)
        seconds = total_seconds - hours * 3600 - minutes * 60
        return '{:02d}:{:02d}:{:06.3f}'.format(int(hours), int(minutes), seconds)

    @property
    def start_as_timestamp(self):
        return self._to_timestamp(self.start)

    @property
    def end_as_timestamp(self):
        return self._to_timestamp(self.end)


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