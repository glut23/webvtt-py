from datetime import time


class Caption(object):
    def __init__(self, start=time(0, 0, 0), end=time(0, 0, 0), lines=None):
        self.start = start
        self.end = end
        self.lines = lines or []

    def add_line(self, line):
        self.lines.append(line)

    def _time_in_seconds(self, time):
        return time.second + time.minute * 60 + time.hour * 60 * 60

    @property
    def start_in_seconds(self):
        return self._time_in_seconds(self.start)

    @property
    def end_in_seconds(self):
        return self._time_in_seconds(self.end)