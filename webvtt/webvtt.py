from .parsers import WebVTTParser, SRTParser

SUPPORTED_FORMATS = (
    ('webvtt', WebVTTParser),  # default parser for WebVTT format
    ('srt',    SRTParser),     # parser for SRT format
)


class WebVTT:
    """
    Parse captions in WebVTT format and also from other formats like SRT.
    To read WebVTT:
        WebVTT().read('captions.vtt')
    For other formats like SRT, use from_[format in lower case]:
        WebVTT().from_srt('captions.srt')

    A list of all supported formats is available calling supported_formats().
    """
    def __init__(self):
        self.parser = None

        # create methods dynamically to read captions based on the supported types
        # read() is created for WebVTT and from_[FORMAT]() for the other formats.
        for format_, parser_class in SUPPORTED_FORMATS:
            method_name = 'read' if format_ == 'webvtt' else 'from_{}'.format(format_)

            setattr(self.__class__, method_name, self._set_reader(method_name, format_, parser_class))

    def _set_reader(self, name, format_, parser_class):
        def f(self, file):
            self.parser = parser_class()
            return self.parser.read(file)

        f.__name__ = name
        if format_ == 'webvtt':
            f.__doc__ = 'Reads a WebVTT captions file.'
        else:
            f.__doc__ = 'Reads captions from a file in {} format.'.format(format_.upper())
        return f

    @staticmethod
    def supported_formats():
        """Provides a list of supported formats that this class can read from."""
        return [f[0] for f in SUPPORTED_FORMATS]

    @property
    def captions(self):
        """Returns the list of parsed captions."""
        return [] if self.parser is None else self.parser.captions