import os

from .parsers import WebVTTParser, SRTParser, SBVParser
from webvtt.exceptions import MissingFilenameError


class WebVTT(object):
    """
    Parse captions in WebVTT format and also from other formats like SRT.

    To read WebVTT:

        WebVTT().read('captions.vtt')

    For other formats like SRT, use from_[format in lower case]:

        WebVTT().from_srt('captions.srt')

    A list of all supported formats is available calling supported_formats().
    """

    def __init__(self):
        self._captions = []
        self._styles = []
        self.file = ''

    def __len__(self):
        return len(self._captions)

    def __getitem__(self, index):
        return self._captions[index]

    def from_srt(self, file):
        """Reads captions from a file in SubRip format."""
        self.file = file
        self._captions = SRTParser().read(file).captions
        return self

    def from_sbv(self, file):
        """Reads captions from a file in YouTube SBV format."""
        self.file = file
        self._captions = SBVParser().read(file).captions
        return self

    def read(self, file):
        """Reads a WebVTT captions file."""
        parser = WebVTTParser().read(file)
        self.file = file
        self._captions = parser.captions
        self._styles = parser.styles
        return self

    def save(self, output=''):
        """Save the document.
        If no output is provided the file will be saved in the same location. Otherwise output
        can determine a target directory or file.
        """
        if not output:
            if not self.file:
                raise MissingFilenameError
            # saving an original vtt file will overwrite the file
            # and for files read from other formats will save as vtt
            # with the same name and location
            self.file = os.path.splitext(self.file)[0] + '.vtt'
        else:
            target = os.path.join(os.getcwd(), output)
            if os.path.isdir(target):
                # if an output is provided and it is a directory
                # the file will be saved in that location with the same name
                filename = os.path.splitext(os.path.basename(self.file))[0]
                self.file = os.path.join(target, '{}.vtt'.format(filename))
            else:
                if target[-3:].lower() != 'vtt':
                    target += '.vtt'
                # otherwise the file will be written in the specified location
                self.file = target

        with open(self.file, 'w', encoding='utf-8') as f:
            f.write('WEBVTT\n')
            for c in self._captions:
                f.write('\n{} --> {}\n'.format(c.start, c.end))
                f.writelines(['{}\n'.format(l) for l in c.lines])

    @staticmethod
    def supported_formats():
        """Provides a list of supported formats that this class can read from."""
        return ['WebVTT (.vtt)', 'SubRip (.srt)', 'YouTube SBV (.sbv)']

    @property
    def captions(self):
        """Returns the list of captions."""
        return self._captions

    @property
    def total_length(self):
        """Returns the total length of the captions."""
        if not self._captions:
            return 0
        return int(self._captions[-1].end_in_seconds) - int(self._captions[0].start_in_seconds)

    @property
    def styles(self):
        return self._styles
