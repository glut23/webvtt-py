"""WebVTT module."""

import codecs
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

_T = typing.TypeVar('_T')

# the extensions of each format, kept when saving a file to the same format
_FORMAT_EXTENSIONS = {'vtt': ('.vtt', '.webvtt'), 'srt': ('.srt',)}


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

        The lists are kept as the attributes, not copied, so changes to a
        list after creating the instance show in it.

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
        self.captions = _list_or_new(captions)
        self.styles = _list_or_new(styles)
        self.header_comments = _list_or_new(header_comments)
        self.footer_comments = _list_or_new(footer_comments)
        self.header_text = header_text or ''
        self.metadata = _list_or_new(metadata)
        self.regions = _list_or_new(regions)
        self._has_bom = False
        self.encoding = DEFAULT_ENCODING
        # the encoding given to read SRT, which save_as_srt keeps
        self._srt_encoding: typing.Optional[str] = None

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
            strict: bool = False,
            errors: str = 'strict'
            ) -> 'WebVTT':
        """
        Read a WebVTT captions file.

        :param file: the file path
        :param encoding: encoding of a file without a Byte Order Mark, UTF-8
            by default. It is only used for reading, as WebVTT files are
            saved in UTF-8 unless another encoding is given
        :param strict: raise an error on blocks that are not valid WebVTT
            instead of ignoring them
        :param errors: how bytes that are not valid in the encoding are
            handled, as in ``bytes.decode``: ``'strict'`` (the default)
            raises ``UnicodeDecodeError``, ``'replace'`` reads them as
            U+FFFD and ``'ignore'`` drops them
        :returns: a `WebVTT` instance

        :raises MalformedFileError: if the file is not in the right format
        :raises MalformedCaptionError: if a caption has an invalid timestamp,
            or if strict and a block is not valid WebVTT
        """
        with utils.FileWrapper.open(
                file, encoding=encoding, errors=errors
                ) as fw:
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
            DeprecationWarning,
            stacklevel=2
            )
        return cls.from_buffer(buffer)

    @classmethod
    def from_buffer(
            cls,
            buffer: typing.Union[typing.Iterable[str], typing.BinaryIO],
            format: str = 'vtt',
            strict: bool = False,
            encoding: typing.Optional[str] = None,
            errors: str = 'strict'
            ) -> 'WebVTT':
        """
        Read WebVTT captions from a file-like object.

        Such file-like object may be the return of an io.open call, in text
        or binary mode, io.StringIO or io.BytesIO object,
        tempfile.TemporaryFile object, etc. Binary data is decoded with the
        encoding of its Byte Order Mark, if any, or else with ``encoding``.

        The ``name`` of the file-like object is kept as the ``file`` to save
        to when it is a path, so a file-like object without one, such as
        standard input, a file opened from a file descriptor or an
        io.BytesIO object, gives captions without a file, as when they are
        not read from a file.

        :param buffer: the file-like object to read captions from, or an
            iterable of lines
        :param format: the format of the data (vtt, srt or sbv)
        :param strict: raise an error on blocks that are not valid WebVTT
            instead of ignoring them, only for the vtt format, as SRT and
            SBV have no strict parsing
        :param encoding: encoding of binary data without a Byte Order Mark,
            UTF-8 by default. For the srt format, `save_as_srt` saves in the
            same encoding
        :param errors: how bytes of binary data that are not valid in the
            encoding are handled, as in ``bytes.decode``: ``'strict'`` (the
            default) raises ``UnicodeDecodeError``, ``'replace'`` reads them
            as U+FFFD and ``'ignore'`` drops them
        :returns: a `WebVTT` instance

        :raises MalformedFileError: if the data is not in the right format
        :raises MalformedCaptionError: if a caption has an invalid timestamp,
            or if strict and a block is not valid WebVTT
        :raises ValueError: if the format is not supported, or strict is
            given for the srt or sbv format
        :raises UnicodeDecodeError: if binary data cannot be decoded
        :raises TypeError: if the buffer is a string or bytes, use
            from_string to read a string or io.BytesIO to read bytes
        """
        if format not in ('vtt', 'srt', 'sbv'):
            raise ValueError(f'Format {format} is not supported.')
        if strict and format != 'vtt':
            raise ValueError(
                f'Strict parsing is not supported for the {format} format'
                )

        file = _buffer_file(buffer)
        lines, bom_encoding, binary = cls._read_buffer(
            buffer, encoding, errors
            )

        if format == 'vtt':
            output = vtt.parse(cls._get_lines(lines), strict)
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
            instance = cls(captions=srt.parse(cls._get_lines(lines)))
        else:
            instance = cls(captions=sbv.parse(cls._get_lines(lines)))

        instance.file = file
        if bom_encoding:
            instance.encoding = bom_encoding
            instance._has_bom = True
        elif format == 'srt' and binary:
            instance._srt_encoding = encoding
        return instance

    @staticmethod
    def _read_buffer(
            buffer: typing.Union[typing.Iterable[str], typing.BinaryIO],
            encoding: typing.Optional[str],
            errors: str = 'strict'
            ) -> typing.Tuple[
                typing.Iterable[str], typing.Optional[str], bool
                ]:
        """
        Return the lines of a buffer and the encoding of its BOM.

        A file-like object is read whole, and binary data is decoded with
        the encoding of its BOM, if any, or else with ``encoding``.

        :param buffer: the file-like object, or an iterable of lines
        :param encoding: encoding of binary data without a BOM
        :param errors: how decoding errors are handled
        :returns: the lines, the encoding of the BOM of binary data or
            None, and whether the data was binary

        :raises TypeError: if the buffer is a string or bytes
        """
        if isinstance(buffer, str):
            raise TypeError(
                'from_buffer reads a file-like object, not a string: '
                'use from_string to read a string'
                )

        if isinstance(buffer, (bytes, bytearray)):
            raise TypeError(
                'from_buffer reads a file-like object, not bytes: '
                'use io.BytesIO to read bytes'
                )

        read = getattr(buffer, 'read', None)
        if read is None:
            return typing.cast(typing.Iterable[str], buffer), None, False

        data = read()
        if isinstance(data, str):
            return [data], None, False

        bom_encoding = utils._bom_encoding(data)
        if bom_encoding:
            data = data[len(utils.CODEC_BOMS[bom_encoding]):]
        return (
            [data.decode(bom_encoding or encoding or 'utf-8', errors)],
            bom_encoding,
            True
            )

    @classmethod
    def from_srt(
            cls,
            file: str,
            encoding: typing.Optional[str] = None,
            errors: str = 'strict'
            ) -> 'WebVTT':
        """
        Read captions from a file in SubRip format.

        :param file: the file path
        :param encoding: encoding of a file without a Byte Order Mark, UTF-8
            by default. `save_as_srt` saves in the same encoding, while
            `save` saves WebVTT in UTF-8 unless another encoding is given
        :param errors: how bytes that are not valid in the encoding are
            handled, as in ``bytes.decode``: ``'strict'`` (the default)
            raises ``UnicodeDecodeError``, ``'replace'`` reads them as
            U+FFFD and ``'ignore'`` drops them
        :returns: a `WebVTT` instance

        :raises MalformedFileError: if the file is not in the right format
        :raises MalformedCaptionError: if a caption has an invalid timestamp
        """
        with utils.FileWrapper.open(
                file, encoding=encoding, errors=errors
                ) as fw:
            instance = cls.from_buffer(fw.file, format='srt')
            if not fw.bom_encoding:
                instance._srt_encoding = encoding
            return instance

    @classmethod
    def from_sbv(
            cls,
            file: str,
            encoding: typing.Optional[str] = None,
            errors: str = 'strict'
            ) -> 'WebVTT':
        """
        Read captions from a file in YouTube SBV format.

        :param file: the file path
        :param encoding: encoding of a file without a Byte Order Mark, UTF-8
            by default. It is only used for reading, as WebVTT files are
            saved in UTF-8 unless another encoding is given
        :param errors: how bytes that are not valid in the encoding are
            handled, as in ``bytes.decode``: ``'strict'`` (the default)
            raises ``UnicodeDecodeError``, ``'replace'`` reads them as
            U+FFFD and ``'ignore'`` drops them
        :returns: a `WebVTT` instance

        :raises MalformedFileError: if the file is not in the right format
        :raises MalformedCaptionError: if a caption has an invalid timestamp
        """
        with utils.FileWrapper.open(
                file, encoding=encoding, errors=errors
                ) as fw:
            return cls.from_buffer(fw.file, format='sbv')

    @classmethod
    def from_string(cls, string: str, strict: bool = False) -> 'WebVTT':
        """
        Read captions from a string.

        :param string: the captions in a string
        :param strict: raise an error on blocks that are not valid WebVTT
            instead of ignoring them
        :returns: a `WebVTT` instance

        :raises MalformedFileError: if the string is not in the right format
        :raises MalformedCaptionError: if a caption has an invalid timestamp,
            or if strict and a block is not valid WebVTT
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
            destination_path = _with_extension(self.file, extension)

        assert destination_path is not None

        target = os.path.join(os.getcwd(), destination_path)
        if os.path.isdir(target):
            if not self.file:
                raise MissingFilenameError

            # store the file in specified directory
            new_filename = os.path.basename(
                _with_extension(self.file, extension)
                )
            return os.path.join(target, new_filename)

        # a path with an extension is written as given, e.g. .webvtt
        if not os.path.splitext(target)[1]:
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

        :param output: destination path of the file, with ``.vtt`` added
            when it has no extension, or a folder to save the file there
            with the name of the file that was read. Without it, the file
            is saved to the ``file`` attribute, with its extension replaced
            by ``.vtt`` unless it is ``.vtt`` or ``.webvtt``
        :param encoding: encoding of the file, by default the ``encoding``
            attribute: the encoding of the Byte Order Mark of the file that
            was read, or UTF-8
        :param add_bom: save the file with Byte Order Mark, or without it
            if false. By default, the Byte Order Mark of the file that was
            read is kept

        :raises MissingFilenameError: if output cannot be determined
        :raises LookupError: if the encoding is not known
        :raises ValueError: if the header text or metadata are not valid,
            or the text of a caption, style or comment could not be read
            back, or add_bom is true and the encoding has no Byte Order
            Mark, or false and the encoding always writes one, such as
            ``utf-16``, leaving an existing file unchanged
        """
        destination = self._get_destination_file(output)
        # build the content first so an invalid header leaves no file behind
        content = self.content
        encoding = encoding or self.encoding
        content = _byte_order_mark(encoding, add_bom, self._has_bom) + content

        utils._write_text_file(destination, content, encoding)
        self.file = destination

    def save_as_srt(
            self,
            output: typing.Optional[str] = None,
            encoding: typing.Optional[str] = None,
            keep_formatting: bool = False
            ):
        """
        Save the WebVTT captions to a file in SubRip format.

        The content is encoded before the file is opened, so an error while
        encoding, such as a character the encoding cannot write, leaves an
        existing file unchanged.

        :param output: destination path of the file, with ``.srt`` added
            when it has no extension, or a folder to save the file there
            with the name of the file that was read. Without it, the file
            is saved to the ``file`` attribute, with its extension replaced
            by ``.srt`` unless it is ``.srt``
        :param encoding: encoding of the file, by default the encoding
            given to read the captions from SRT, or UTF-8
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

        utils._write_text_file(
            destination,
            content.getvalue(),
            encoding or self._srt_encoding or DEFAULT_ENCODING
            )
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


def _buffer_file(buffer: typing.Any) -> typing.Optional[str]:
    """
    Return the path of the file of a file-like object, if it has one.

    A name that is not a path is not kept, such as the file descriptor of
    a file opened from one or a name in angle brackets like ``<stdin>``
    that is not a file.

    :param buffer: the file-like object
    :returns: the path, or None
    """
    name = getattr(buffer, 'name', None)
    if isinstance(name, (str, bytes, os.PathLike)):
        name = os.fsdecode(name)
    if (not isinstance(name, str) or not name or
            (name.startswith('<') and name.endswith('>') and
             not os.path.exists(name))):
        return None
    return name


def _with_extension(file: str, extension: str) -> str:
    """
    Return the path of a file with the extension of a format.

    :param file: the path of the file
    :param extension: the extension of the format, such as ``vtt``
    :returns: the path as it is if its extension is one of the format, as
        ``.webvtt`` for ``vtt``, or else with the extension replaced
    """
    name, current = os.path.splitext(file)
    if current.lower() in _FORMAT_EXTENSIONS[extension]:
        return file
    return f'{name}.{extension}'


def _byte_order_mark(
        encoding: str,
        add_bom: typing.Optional[bool],
        has_bom: bool
        ) -> str:
    """
    Return the Byte Order Mark to write before the content.

    :param encoding: the encoding, under any of its names
    :param add_bom: true to add a Byte Order Mark, false to leave it out,
        or None to keep the Byte Order Mark of the file that was read
    :param has_bom: true if the file that was read has a Byte Order Mark
    :returns: the Byte Order Mark as text, empty if there is none or the
        codec of the encoding writes it

    :raises LookupError: if the encoding is not known
    :raises ValueError: if add_bom is true and the encoding has no Byte
        Order Mark, or false and the codec of the encoding always writes one
    """
    # equivalent names such as UTF-8 and utf8 become utf-8
    name = codecs.lookup(encoding).name

    if name in utils._BOM_WRITING_CODECS:
        if add_bom is False:
            raise ValueError(
                f'The {encoding} encoding always writes a Byte Order Mark'
                )
        return ''

    if name not in utils.CODEC_BOMS:
        if add_bom:
            raise ValueError(f'The {encoding} encoding has no Byte Order Mark')
        return ''

    if add_bom or (add_bom is None and has_bom):
        return utils.CODEC_BOMS[name].decode(name)
    return ''


def _list_or_new(items: typing.Optional[typing.List[_T]]) -> typing.List[_T]:
    """
    Return the list given, even if empty, or a new list for None.

    :param items: the list, kept so that changes to it show
    :returns: the list, or a new empty list
    """
    return [] if items is None else items
