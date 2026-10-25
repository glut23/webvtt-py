"""WebVTT module."""

import datetime
import os
import io
import typing
import warnings

from . import vtt, utils
from . import srt
from . import sbv
from .models import (
    Caption,
    Region,
    Style,
    Timestamp,
    _FrameRate,
    _Position,
    _offset_in_milliseconds,
    _retime_captions,
    _sync_mapping,
    _framerate_mapping
    )
from .errors import MissingFilenameError

DEFAULT_ENCODING = 'utf-8'


class WebVTT:
    """
    Parse captions in WebVTT format and also from other formats like SRT.

    To read WebVTT:

        WebVTT.read('captions.vtt')

    For other formats:

        WebVTT.from_srt('captions.srt')
        WebVTT.from_sbv('captions.sbv')
    """

    def __init__(
            self,
            # NoReturn, so type checkers report positional arguments too
            *args: typing.NoReturn,
            file: typing.Optional[str] = None,
            captions: typing.Optional[typing.List[Caption]] = None,
            styles: typing.Optional[typing.List[Style]] = None,
            header_comments: typing.Optional[typing.List[str]] = None,
            footer_comments: typing.Optional[typing.List[str]] = None,
            header_text: typing.Optional[str] = None,
            metadata: typing.Optional[typing.List[str]] = None,
            regions: typing.Optional[typing.List[Region]] = None
            ):
        """
        Initialize.

        The arguments are keyword only, and no file is read: use `read`,
        `from_srt`, `from_sbv`, `from_buffer` or `from_string` to read
        captions. The ``file`` attribute is the path the captions were read
        from or last saved to, which `save` uses when no output is given,
        and can be set to choose where they are saved.

        :param file: DEPRECATED, set the ``file`` attribute instead
        :param captions: the list of captions
        :param styles: the list of styles
        :param header_comments: list of comments for the start of the file
        :param footer_comments: list of comments for the bottom of the file
        :param header_text: the text following "WEBVTT" in the first line
        :param metadata: list of metadata lines following the "WEBVTT"
            line, e.g. ``X-TIMESTAMP-MAP=LOCAL:00:00:00.000,MPEGTS:0``
        :param regions: the list of regions

        :raises TypeError: if an argument is passed by position
        """
        if args:
            # WebVTT('captions.vtt') looks like it reads the file, but it
            # only set the path where save() writes, so saving it replaced
            # the file with no captions
            raise TypeError(
                f'{self.__class__.__name__}() takes keyword arguments only '
                'and does not read files, use webvtt.read() to read '
                'captions from a file'
                )

        if file is not None:
            warnings.warn(
                f'The file argument of {self.__class__.__name__}() is '
                'deprecated, use webvtt.read() to read captions from a file '
                'and set the file attribute, or pass the output to save(), '
                'to choose where they are saved',
                DeprecationWarning,
                stacklevel=2
                )

        self.file = file
        self.captions = captions or []
        self.styles = styles or []
        self.header_comments = header_comments or []
        self.footer_comments = footer_comments or []
        self.header_text = header_text or ''
        self.metadata = metadata or []
        self.regions = regions or []
        self._has_bom = False
        self.encoding = DEFAULT_ENCODING

    def __len__(self):
        """Return the number of captions."""
        return len(self.captions)

    def __getitem__(self, index):
        """Return a caption by index."""
        return self.captions[index]

    def __repr__(self):
        """Return the string representation of the WebVTT file."""
        return (f'<{self.__class__.__name__} file={self.file!r} '
                f'encoding={self.encoding!r}>'
                )

    def __str__(self):
        """Return a readable representation of the WebVTT content."""
        return '\n'.join(str(c) for c in self.captions)

    @classmethod
    def read(
            cls,
            file: str,
            encoding: typing.Optional[str] = None,
            strict: bool = False
            ) -> 'WebVTT':
        """
        Read a WebVTT captions file.

        :param file: the file path
        :param encoding: encoding of the file
        :param strict: raise an error on malformed cue blocks instead of
            ignoring them
        :returns: a `WebVTT` instance

        :raises MalformedFileError: if the file is not in the right format
        :raises MalformedCaptionError: if a caption has an invalid timestamp,
            or if strict and a cue block is malformed
        """
        with utils.FileWrapper.open(file, encoding=encoding) as fw:
            instance = cls.from_buffer(fw.file, strict=strict)
            if fw.bom_encoding:
                instance.encoding = fw.bom_encoding
                instance._has_bom = True
            return instance

    @classmethod
    def read_buffer(
            cls,
            buffer: typing.Iterator[str]
            ) -> 'WebVTT':
        """
        Read WebVTT captions from a file-like object.

        This method is DEPRECATED. Use from_buffer instead.

        Such file-like object may be the return of an io.open call,
        io.StringIO object, tempfile.TemporaryFile object, etc.

        :param buffer: the file-like object to read captions from
        :returns: a `WebVTT` instance
        """
        warnings.warn(
            'Deprecated: use from_buffer instead.',
            DeprecationWarning
            )
        return cls.from_buffer(buffer)

    @classmethod
    def from_buffer(
            cls,
            buffer: typing.Union[typing.Iterable[str], io.BytesIO],
            format: str = 'vtt',
            strict: bool = False
            ) -> 'WebVTT':
        """
        Read WebVTT captions from a file-like object.

        Such file-like object may be the return of an io.open call,
        io.StringIO object, tempfile.TemporaryFile object, etc.

        :param buffer: the file-like object to read captions from
        :param format: the format of the data (vtt, srt or sbv)
        :param strict: raise an error on malformed cue blocks instead of
            ignoring them, only for the vtt format
        :returns: a `WebVTT` instance

        :raises MalformedFileError: if the data is not in the right format
        :raises MalformedCaptionError: if a caption has an invalid timestamp,
            or if strict and a cue block is malformed
        :raises ValueError: if the format is not supported
        """
        file = getattr(buffer, 'name', None)

        if isinstance(buffer, io.BytesIO):
            buffer = (line.decode('utf-8') for line in buffer)

        if format == 'vtt':
            output = vtt.parse(cls._get_lines(buffer), strict)
            instance = cls(
                captions=output.captions,
                styles=output.styles,
                header_comments=output.header_comments,
                footer_comments=output.footer_comments,
                header_text=output.header_text,
                metadata=output.metadata,
                regions=output.regions
                )
        elif format == 'srt':
            instance = cls(captions=srt.parse(cls._get_lines(buffer)))
        elif format == 'sbv':
            instance = cls(captions=sbv.parse(cls._get_lines(buffer)))
        else:
            raise ValueError(f'Format {format} is not supported.')

        instance.file = file
        return instance

    @classmethod
    def from_srt(
            cls,
            file: str,
            encoding: typing.Optional[str] = None
            ) -> 'WebVTT':
        """
        Read captions from a file in SubRip format.

        :param file: the file path
        :param encoding: encoding of the file
        :returns: a `WebVTT` instance

        :raises MalformedFileError: if the file is not in the right format
        :raises MalformedCaptionError: if a caption has an invalid timestamp
        """
        with utils.FileWrapper.open(file, encoding=encoding) as fw:
            return cls.from_buffer(fw.file, format='srt')

    @classmethod
    def from_sbv(
            cls,
            file: str,
            encoding: typing.Optional[str] = None
            ) -> 'WebVTT':
        """
        Read captions from a file in YouTube SBV format.

        :param file: the file path
        :param encoding: encoding of the file
        :returns: a `WebVTT` instance

        :raises MalformedFileError: if the file is not in the right format
        :raises MalformedCaptionError: if a caption has an invalid timestamp
        """
        with utils.FileWrapper.open(file, encoding=encoding) as fw:
            return cls.from_buffer(fw.file, format='sbv')

    @classmethod
    def from_string(cls, string: str, strict: bool = False) -> 'WebVTT':
        """
        Read captions from a string.

        :param string: the captions in a string
        :param strict: raise an error on malformed cue blocks instead of
            ignoring them
        :returns: a `WebVTT` instance

        :raises MalformedFileError: if the string is not in the right format
        :raises MalformedCaptionError: if a caption has an invalid timestamp,
            or if strict and a cue block is malformed
        """
        output = vtt.parse(cls._get_lines([string]), strict)
        return cls(
            captions=output.captions,
            styles=output.styles,
            header_comments=output.header_comments,
            footer_comments=output.footer_comments,
            header_text=output.header_text,
            metadata=output.metadata,
            regions=output.regions
        )

    @staticmethod
    def _get_lines(lines: typing.Iterable[str]) -> typing.List[str]:
        """
        Return cleaned lines from an iterable of lines.

        Each item is split on CR, LF and CRLF, so an item holding several
        lines, like CR terminated lines read from a buffer that only splits
        on LF, is also handled.

        :param lines: iterable of lines
        :returns: a list of cleaned lines
        """
        cleaned_lines: typing.List[str] = []
        for item in lines:
            # an empty item is an empty line
            cleaned_lines.extend(utils._split_lines(item) or [''])
        if cleaned_lines and cleaned_lines[0].startswith('\ufeff'):
            cleaned_lines[0] = cleaned_lines[0][1:]
        return cleaned_lines

    def _get_destination_file(
            self,
            destination_path: typing.Optional[str] = None,
            extension: str = 'vtt'
            ) -> str:
        """
        Return the destination file based on the provided params.

        :param destination_path: optional destination path
        :param extension: the extension of the file
        :returns: the destination file

        :raises MissingFilenameError: if destination path cannot be determined
        """
        if not destination_path and not self.file:
            raise MissingFilenameError

        if not destination_path and self.file:
            destination_path = (
                f'{os.path.splitext(self.file)[0]}.{extension}'
                )

        assert destination_path is not None

        target = os.path.join(os.getcwd(), destination_path)
        if os.path.isdir(target):
            if not self.file:
                raise MissingFilenameError

            # store the file in specified directory
            base_name = os.path.splitext(os.path.basename(self.file))[0]
            new_filename = f'{base_name}.{extension}'
            return os.path.join(target, new_filename)

        if target[-4:].lower() != f'.{extension}':
            target = f'{target}.{extension}'

        # store the file in the specified full path
        return target

    def save(
            self,
            output: typing.Optional[str] = None,
            encoding: typing.Optional[str] = None,
            add_bom: typing.Optional[bool] = None
            ):
        """
        Save the WebVTT captions to a file.

        The content is encoded before the file is opened, so an error while
        encoding, such as a character the encoding cannot write, leaves an
        existing file unchanged.

        :param output: destination path of the file
        :param encoding: encoding of the file
        :param add_bom: save the file with Byte Order Mark

        :raises MissingFilenameError: if output cannot be determined
        :raises ValueError: if the header text or metadata are not valid,
            or the text of a caption, style or comment could not be read
            back, leaving an existing file unchanged
        """
        destination = self._get_destination_file(output)
        # build the content first so an invalid header leaves no file behind
        content = self.content
        encoding = encoding or self.encoding

        if add_bom is None and self._has_bom:
            add_bom = True

        if add_bom and encoding in utils.CODEC_BOMS:
            content = utils.CODEC_BOMS[encoding].decode(encoding) + content

        utils._write_text_file(destination, content, encoding)
        self.file = destination

    def save_as_srt(
            self,
            output: typing.Optional[str] = None,
            encoding: typing.Optional[str] = DEFAULT_ENCODING,
            keep_formatting: bool = False
            ):
        """
        Save the WebVTT captions to a file in SubRip format.

        The content is encoded before the file is opened, so an error while
        encoding, such as a character the encoding cannot write, leaves an
        existing file unchanged.

        :param output: destination path of the file
        :param encoding: encoding of the file
        :param keep_formatting: keep bold, italic, underline and the colours
            of the cue classes in the styles, instead of removing the cue tags

        :raises MissingFilenameError: if output cannot be determined
        """
        destination = self._get_destination_file(output, extension='srt')
        content = io.StringIO()
        srt.write(content,
                  self.captions,
                  self.styles if keep_formatting else None
                  )

        utils._write_text_file(destination, content.getvalue(), encoding)
        self.file = destination

    def write(
            self,
            f: typing.IO[str],
            format: str = 'vtt',
            keep_formatting: bool = False
            ):
        """
        Save the WebVTT captions to a file-like object.

        :param f: destination file-like object
        :param format: the format to use (`vtt` or `srt`)
        :param keep_formatting: when writing SRT, keep bold, italic,
            underline and the colours of the cue classes in the styles,
            instead of removing the cue tags

        :raises ValueError: if the format is not supported, or when
            writing WebVTT, the header text or metadata are not valid or the
            text of a caption, style or comment could not be read back
        """
        if format == 'vtt':
            return vtt.write(f,
                             self.captions,
                             self.styles,
                             self.header_comments,
                             self.footer_comments,
                             self.header_text,
                             self.metadata,
                             self.regions
                             )
        if format == 'srt':
            return srt.write(f,
                             self.captions,
                             self.styles if keep_formatting else None
                             )

        raise ValueError(f'Format {format} is not supported.')

    def iter_slice(
            self,
            start: typing.Optional[str] = None,
            end: typing.Optional[str] = None
            ) -> typing.Generator[Caption, None, None]:
        """
        Iterate a slice of the captions based on a time range.

        Only the captions within the range are returned: a caption that
        starts before ``start`` or ends after ``end`` is left out.

        :param start: start timestamp of the range
        :param end: end timestamp of the range
        :returns: generator of Captions
        """
        start_time = Timestamp.from_string(start) if start else None
        end_time = Timestamp.from_string(end) if end else None

        for caption in self.captions:
            if (
                    (not start_time or caption.start_time >= start_time) and
                    (not end_time or caption.end_time <= end_time)
                    ):
                yield caption

    def shift(
            self,
            offset: typing.Union[float, datetime.timedelta],
            start: typing.Optional[str] = None
            ):
        """
        Shift the start and end time of the captions.

        The offset is rounded to the nearest millisecond, halves away from
        zero, and a timestamp that would fall before zero is set to
        ``00:00:00.000``.

        :param offset: a number of seconds or a ``timedelta``, negative
            values move the captions earlier
        :param start: only shift the captions starting at or after this
            timestamp

        :raises TypeError: if the offset is not a number or a ``timedelta``
        :raises ValueError: if the offset is not finite, or would move a
            time after the largest timestamp, leaving the captions unchanged
        :raises MalformedCaptionError: if the start timestamp is not valid
        """
        offset_ms = _offset_in_milliseconds(offset)

        def mapping(milliseconds: int) -> int:
            return milliseconds + offset_ms

        _retime_captions(self.iter_slice(start=start), mapping)

    def sync(self, *points: typing.Sequence[_Position]):
        """
        Synchronize the captions to two or more points.

        Each point is a ``(from, to)`` pair: the time ``from`` in the
        captions is moved to ``to``. Times between two points are moved
        along the line between them, which fixes captions that drift out of
        sync, and times before the first or after the last point along the
        line of the outermost points. Start and end times are rounded to the
        nearest millisecond, halves away from zero, and a time that would
        fall before zero is set to ``00:00:00.000``.

        :param points: ``(from, to)`` pairs, each time a timestamp string, a
            `Timestamp`, a number of seconds or a ``timedelta``

        :raises MalformedCaptionError: if a timestamp string is not valid
        :raises TypeError: if a point is not a pair of supported values
        :raises ValueError: if there are fewer than two points, two points
            have the same ``from`` time, the ``to`` times are not in the
            same order as the ``from`` times, a time is not finite, is
            before zero or is after the largest timestamp, or a caption
            would be moved after the largest timestamp, leaving the captions
            unchanged
        """
        mapping = _sync_mapping(points)

        _retime_captions(self.captions, mapping)

    def change_framerate(self, from_fps: _FrameRate, to_fps: _FrameRate):
        """
        Change the timing of the captions from one frame rate to another.

        Useful when the captions were timed for a video with a different
        frame rate, e.g. ``change_framerate(25, 23.976)`` for captions of a
        25 fps video played with a 23.976 fps one. Times are multiplied by
        ``from_fps / to_fps`` and rounded to the nearest millisecond, halves
        away from zero. Frame rates are read as written, and exact rates
        such as ``Fraction(24000, 1001)`` for NTSC can be given as a
        ``fractions.Fraction``.

        :param from_fps: the frame rate the captions are timed for, a number
            or a ``fractions.Fraction``
        :param to_fps: the frame rate of the video, a number or a
            ``fractions.Fraction``

        :raises TypeError: if a frame rate is not a number
        :raises ValueError: if a frame rate is not finite or not above zero,
            or a caption would be moved after the largest timestamp, leaving
            the captions unchanged
        """
        mapping = _framerate_mapping(from_fps, to_fps)

        _retime_captions(self.captions, mapping)

    @property
    def total_length(self):
        """
        Return the total length of the captions in seconds.

        It is the time from the start of the first caption to the end of
        the last one, in whole seconds as the milliseconds of both are left
        out, so the captions are expected in order of time.
        """
        if not self.captions:
            return 0
        return (
                self.captions[-1].end_in_seconds -
                self.captions[0].start_in_seconds
                )

    @property
    def content(self) -> str:
        """
        Return the webvtt captions as string.

        This property is useful in cases where the webvtt content is needed
        but no file-like destination is required. Storage in DB for instance.

        :raises ValueError: if the header text or metadata are not valid,
            or the text of a caption, style or comment could not be read
            back
        """
        return vtt.to_str(
            self.captions,
            self.styles,
            self.header_comments,
            self.footer_comments,
            self.header_text,
            self.metadata,
            self.regions
            )
