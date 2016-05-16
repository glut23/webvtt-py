

class Caption(object):
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