import os
from .parsers import WebVTTParser, SRTParser

SUPPORTED_FORMATS = (
    ('webvtt', WebVTTParser),  # default parser for WebVTT format
    ('srt',    SRTParser),     # parser for SRT format
)


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
        self.captions = []
        self.file = ''

        # create methods dynamically to read captions based on the supported types
        # read() is created for WebVTT and from_[FORMAT]() for the other formats.
        for format_, parser_class in SUPPORTED_FORMATS:
            method_name = 'read' if format_ == 'webvtt' else 'from_{}'.format(format_)

            setattr(self.__class__, method_name, self._set_reader(method_name, format_, parser_class))

    def _set_reader(self, name, format_, parser_class):
        def f(self, file):
            self.file = file
            self.captions = parser_class().read(file).captions
            return self

        f.__name__ = name
        if format_ == 'webvtt':
            f.__doc__ = 'Reads a WebVTT captions file.'
        else:
            f.__doc__ = 'Reads captions from a file in {} format.'.format(format_.upper())
        return f

    def save(self, output=''):
        if not output:
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
            for c in self.captions:
                f.write('\n{} --> {}\n'.format(c.start, c.end))
                f.writelines(['{}\n'.format(l) for l in c.lines])

    @staticmethod
    def supported_formats():
        """Provides a list of supported formats that this class can read from."""
        return [f[0] for f in SUPPORTED_FORMATS]

    @property
    def total_length(self):
        """Returns the total length of the captions."""
        if not self.captions:
            return 0
        return int(self.captions[-1].end_in_seconds) - int(self.captions[0].start_in_seconds)