

class Caption(object):
    def __init__(self, start, end, lines=None):
        self.start = start
        self.end = end
        self.lines = lines or []

    def add_line(self, line):
        self.lines.append(line)