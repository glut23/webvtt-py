"""WebVTT module."""

import codecs
import copy
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
    ParseIssue,
    Region,
    Style,
    Timestamp,
    ValidationIssue,
    _FrameRate,
    _Position,
    _offset_in_milliseconds,
    _optional_timestamp,
    _retime_captions,
    _sync_mapping,
    _framerate_mapping
    )
from .errors import MissingFilenameError

DEFAULT_ENCODING = 'utf-8'

_T = typing.TypeVar('_T')

# the extensions of each format, kept when saving a file to the same format
_FORMAT_EXTENSIONS = {
    'vtt': ('.vtt', '.webvtt'), 'srt': ('.srt',), 'sbv': ('.sbv',)
    }

_FORMATS = tuple(_FORMAT_EXTENSIONS)


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
        and can be set to choose where they are saved. The ``parse_issues``
        attribute is the list of `ParseIssue` of the blocks that were skipped
        when reading the captions, empty when they were not read.

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
        self.parse_issues: typing.List[ParseIssue] = []
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

    def __eq__(self, other):
        """
        Compare equality with another object.

        Instances are equal when they have the same captions, styles,
        regions, header text and metadata, so they write the same content
        except for the comments. The comments are not compared, as for
        captions, styles and regions, nor where the captions are saved,
        their encoding or the issues found when reading them.
        """
        if not isinstance(other, WebVTT):
            return NotImplemented

        return (self.captions == other.captions and
                self.styles == other.styles and
                self.regions == other.regions and
                self.header_text == other.header_text and
                self.metadata == other.metadata
                )

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
            errors: typing.Optional[str] = 'strict'
            ) -> 'WebVTT':
        """
        Read a WebVTT captions file.

        :param file: the file path
        :param encoding: encoding of a file without a Byte Order Mark, UTF-8
            by default. It is only used for reading, as WebVTT files are
            saved in UTF-8 unless another encoding is given
        :param strict: raise an error on blocks that are not valid WebVTT
            instead of skipping them, which keeps them in ``parse_issues``
        :param errors: how bytes that are not valid in the encoding are
            handled, as in ``bytes.decode``: ``'strict'`` (the default)
            raises ``UnicodeDecodeError``, ``'replace'`` reads them as
            U+FFFD and ``'ignore'`` drops them
        :returns: a `WebVTT` instance

        :raises MalformedFileError: if the file is not in the right format
        :raises MalformedCaptionError: if a caption has an invalid timestamp,
            or if strict and a block is not valid WebVTT
        :raises UnicodeDecodeError: if the file cannot be decoded and errors
            is ``'strict'``
        :raises LookupError: if the errors handler is not known
        """
        return cls._from_file(file, 'vtt', encoding, errors, strict)

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
            errors: typing.Optional[str] = 'strict'
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
            instead of skipping them, which keeps them in ``parse_issues``,
            only for the vtt format, as SRT and SBV have no strict parsing
        :param encoding: encoding of binary data without a Byte Order Mark,
            UTF-8 by default. For the srt format, `save_as_srt` saves in the
            same encoding
        :param errors: how bytes of binary data that are not valid in the
            encoding are handled, as in ``bytes.decode``: ``'strict'`` (the
            default) raises ``UnicodeDecodeError``, ``'replace'`` reads them
            as U+FFFD and ``'ignore'`` drops them. It has no effect on text,
            as a file opened in text mode decodes its own data
        :returns: a `WebVTT` instance

        :raises MalformedFileError: if the data is not in the right format
        :raises MalformedCaptionError: if a caption has an invalid timestamp,
            or if strict and a block is not valid WebVTT
        :raises ValueError: if the format is not supported, or strict is
            given for the srt or sbv format
        :raises UnicodeDecodeError: if binary data cannot be decoded and
            errors is ``'strict'``
        :raises LookupError: if the errors handler is not known
        :raises TypeError: if the buffer is a string or bytes, use
            from_string to read a string or io.BytesIO to read bytes
        """
        _check_format(format)
        if strict and format != 'vtt':
            raise ValueError(
                f'Strict parsing is not supported for the {format} format'
                )
        utils._check_errors(errors)

        file = _buffer_file(buffer)
        lines, bom_encoding, binary = cls._read_buffer(
            buffer, encoding, errors
            )

        issues: typing.List[ParseIssue] = []
        if format == 'vtt':
            output = vtt.parse(cls._get_lines(lines), strict)
            issues = output.issues
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
            instance = cls(captions=srt.parse(cls._get_lines(lines), issues))
        else:
            instance = cls(captions=sbv.parse(cls._get_lines(lines), issues))

        instance.parse_issues = issues
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
            errors: typing.Optional[str]
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
            [data.decode(
                bom_encoding or encoding or 'utf-8',
                errors or 'strict'
                )],
            bom_encoding,
            True
            )

    @classmethod
    def from_srt(
            cls,
            file: str,
            encoding: typing.Optional[str] = None,
            errors: typing.Optional[str] = 'strict'
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
        :raises UnicodeDecodeError: if the file cannot be decoded and errors
            is ``'strict'``
        :raises LookupError: if the errors handler is not known
        """
        return cls._from_file(file, 'srt', encoding, errors)

    @classmethod
    def from_sbv(
            cls,
            file: str,
            encoding: typing.Optional[str] = None,
            errors: typing.Optional[str] = 'strict'
            ) -> 'WebVTT':
        """
        Read captions from a file in YouTube SBV format.

        :param file: the file path
        :param encoding: encoding of a file without a Byte Order Mark, UTF-8
            by default. It is only used for reading, as WebVTT and SBV
            files are saved in UTF-8 unless another encoding is given
        :param errors: how bytes that are not valid in the encoding are
            handled, as in ``bytes.decode``: ``'strict'`` (the default)
            raises ``UnicodeDecodeError``, ``'replace'`` reads them as
            U+FFFD and ``'ignore'`` drops them
        :returns: a `WebVTT` instance

        :raises MalformedFileError: if the file is not in the right format
        :raises MalformedCaptionError: if a caption has an invalid timestamp
        :raises UnicodeDecodeError: if the file cannot be decoded and errors
            is ``'strict'``
        :raises LookupError: if the errors handler is not known
        """
        return cls._from_file(file, 'sbv', encoding, errors)

    @classmethod
    def _from_file(
            cls,
            file: str,
            format: str,
            encoding: typing.Optional[str],
            errors: typing.Optional[str],
            strict: bool = False
            ) -> 'WebVTT':
        """
        Read captions from a file, keeping its Byte Order Mark.

        :param file: the file path
        :param format: the format of the file (vtt, srt or sbv)
        :param encoding: encoding of a file without a Byte Order Mark
        :param errors: how decoding errors are handled
        :param strict: raise an error on blocks that are not valid WebVTT
        :returns: a `WebVTT` instance
        """
        with utils.FileWrapper.open(
                file, encoding=encoding, errors=errors
                ) as fw:
            instance = cls.from_buffer(fw.file, format=format, strict=strict)
            if fw.bom_encoding:
                instance.encoding = fw.bom_encoding
                instance._has_bom = True
            elif format == 'srt':
                instance._srt_encoding = encoding
            return instance

    @classmethod
    def from_string(
            cls,
            string: str,
            strict: bool = False,
            format: str = 'vtt'
            ) -> 'WebVTT':
        """
        Read captions from a string.

        :param string: the captions in a string
        :param strict: raise an error on blocks that are not valid WebVTT
            instead of skipping them, which keeps them in ``parse_issues``,
            only for the vtt format, as SRT and SBV have no strict parsing
        :param format: the format of the string (vtt, srt or sbv)
        :returns: a `WebVTT` instance

        :raises MalformedFileError: if the string is not in the right format
        :raises MalformedCaptionError: if a caption has an invalid timestamp,
            or if strict and a block is not valid WebVTT
        :raises ValueError: if the format is not supported, or strict is
            given for the srt or sbv format
        """
        return cls.from_buffer([string], format=format, strict=strict)

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
        self._save(output, 'vtt', encoding or self.encoding, add_bom)

    def save_as_srt(
            self,
            output: typing.Optional[str] = None,
            encoding: typing.Optional[str] = None,
            keep_formatting: bool = False,
            add_bom: typing.Optional[bool] = None
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
            given to read the captions from SRT, or else the encoding of the
            Byte Order Mark of the file that was read, or UTF-8
        :param keep_formatting: keep bold, italic, underline and the colours
            of the cue classes in the styles, instead of removing the cue tags
        :param add_bom: save the file with Byte Order Mark, or without it
            if false. By default, the Byte Order Mark of the file that was
            read is kept

        :raises MissingFilenameError: if output cannot be determined
        :raises LookupError: if the encoding is not known
        :raises ValueError: if add_bom is true and the encoding has no Byte
            Order Mark, or false and the encoding always writes one, such as
            ``utf-16``, leaving an existing file unchanged
        """
        self._save(output,
                   'srt',
                   encoding or self._srt_encoding or self.encoding,
                   add_bom,
                   keep_formatting
                   )

    def save_as_sbv(
            self,
            output: typing.Optional[str] = None,
            encoding: typing.Optional[str] = None,
            add_bom: typing.Optional[bool] = None
            ):
        """
        Save the WebVTT captions to a file in YouTube SBV format.

        The cue tags are removed, as SBV has no formatting. The content is
        encoded before the file is opened, so an error while encoding, such
        as a character the encoding cannot write, leaves an existing file
        unchanged.

        :param output: destination path of the file, with ``.sbv`` added
            when it has no extension, or a folder to save the file there
            with the name of the file that was read. Without it, the file
            is saved to the ``file`` attribute, with its extension replaced
            by ``.sbv`` unless it is ``.sbv``
        :param encoding: encoding of the file, by default the encoding of
            the Byte Order Mark of the file that was read, or UTF-8
        :param add_bom: save the file with Byte Order Mark, or without it
            if false. By default, the Byte Order Mark of the file that was
            read is kept

        :raises MissingFilenameError: if output cannot be determined
        :raises LookupError: if the encoding is not known
        :raises ValueError: if add_bom is true and the encoding has no Byte
            Order Mark, or false and the encoding always writes one, such as
            ``utf-16``, leaving an existing file unchanged
        """
        self._save(output, 'sbv', encoding or self.encoding, add_bom)

    def _save(
            self,
            output: typing.Optional[str],
            format: str,
            encoding: str,
            add_bom: typing.Optional[bool],
            keep_formatting: bool = False
            ):
        """
        Save the captions to a file in a format.

        :param output: destination path of the file, or a folder
        :param format: the format to save in, also the extension of the file
        :param encoding: encoding of the file
        :param add_bom: save the file with Byte Order Mark, without it if
            false, or keep the Byte Order Mark of the file that was read
        :param keep_formatting: when saving SRT, keep the formatting
        """
        destination = self._get_destination_file(output, extension=format)
        # build the content first so an invalid header leaves no file behind
        content = self.to_string(format, keep_formatting)
        content = _byte_order_mark(encoding, add_bom, self._has_bom) + content

        utils._write_text_file(destination, content, encoding)
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
        :param format: the format to use (`vtt`, `srt` or `sbv`)
        :param keep_formatting: when writing SRT, keep bold, italic,
            underline and the colours of the cue classes in the styles,
            instead of removing the cue tags

        :raises ValueError: if the format is not supported, or when
            writing WebVTT, the header text or metadata are not valid or the
            text of a caption, style or comment could not be read back
        """
        f.write(self.to_string(format, keep_formatting))

    def to_string(
            self,
            format: str = 'vtt',
            keep_formatting: bool = False
            ) -> str:
        """
        Return the captions as a string in a format.

        :param format: the format to use (`vtt`, `srt` or `sbv`)
        :param keep_formatting: when writing SRT, keep bold, italic,
            underline and the colours of the cue classes in the styles,
            instead of removing the cue tags
        :returns: the captions in the format

        :raises ValueError: if the format is not supported, or when
            writing WebVTT, the header text or metadata are not valid or the
            text of a caption, style or comment could not be read back
        """
        _check_format(format)
        if format == 'vtt':
            return self.content

        output = io.StringIO()
        if format == 'srt':
            srt.write(output,
                      self.captions,
                      self.styles if keep_formatting else None
                      )
        else:
            sbv.write(output, self.captions)
        return output.getvalue()

    def copy(self) -> 'WebVTT':
        """
        Return a copy of the captions that shares nothing with them.

        The copy has its own lists of captions, styles, regions, comments,
        metadata and parse issues, and copies of each item, so changing it
        leaves the original unchanged. It keeps where the captions are saved
        and their encoding.
        """
        return copy.deepcopy(self)

    def iter_slice(
            self,
            start: typing.Optional[_Position] = None,
            end: typing.Optional[_Position] = None,
            *,
            overlapping: bool = False,
            clip: bool = False
            ) -> typing.Generator[Caption, None, None]:
        """
        Iterate a slice of the captions based on a time range.

        By default only the captions within the range are returned: a
        caption that starts before ``start`` or ends after ``end`` is left
        out.

        :param start: start of the range, a timestamp string, a
            `Timestamp`, a number of seconds or a ``timedelta``, rounded to
            the nearest millisecond. Default: no start
        :param end: end of the range, as the start. Default: no end
        :param overlapping: also return the captions with part of them in
            the range. A caption that only touches the range, ending at
            ``start`` or starting at ``end``, is not in it, and a range with
            ``end`` not after ``start`` overlaps no caption
        :param clip: return copies of the captions trimmed to the range,
            leaving the captions unchanged. It needs ``overlapping``, as
            only those captions have a part out of the range. The text is
            kept as it is, including any timestamp tags
        :returns: generator of Captions

        :raises ValueError: when the iteration starts, if clip is given
            without overlapping
        :raises MalformedCaptionError: when the iteration starts, if start or
            end are not valid
        """
        if clip and not overlapping:
            raise ValueError('clip needs overlapping')

        start_time = _optional_timestamp(start)
        end_time = _optional_timestamp(end)
        in_range = _overlaps_range if overlapping else _within_range

        for caption in self.captions:
            if in_range(caption, start_time, end_time):
                yield (_clipped(caption, start_time, end_time) if clip
                       else caption)

    def shift(
            self,
            offset: typing.Union[float, datetime.timedelta],
            start: typing.Optional[_Position] = None,
            *,
            drop_before_zero: bool = False
            ):
        """
        Shift the start and end time of the captions.

        The offset is rounded to the nearest millisecond, halves away from
        zero, and a timestamp that would fall before zero is set to
        ``00:00:00.000``, so a caption that ends at or before zero after
        the shift is kept at ``00:00:00.000 --> 00:00:00.000``, where it is
        never shown, unless ``drop_before_zero`` is given.

        :param offset: a number of seconds or a ``timedelta``, negative
            values move the captions earlier
        :param start: only shift the captions starting at or after this
            time, a timestamp string, a `Timestamp`, a number of seconds or
            a ``timedelta``
        :param drop_before_zero: remove from ``captions`` the shifted
            captions that end at or before zero. A caption that starts
            before zero but ends after it is kept, starting at zero

        :raises TypeError: if the offset is not a number or a ``timedelta``
        :raises ValueError: if the offset is not finite, or would move a
            time after the largest timestamp, leaving the captions unchanged
        :raises MalformedCaptionError: if the start time is not valid
        """
        offset_ms = _offset_in_milliseconds(offset)

        def mapping(milliseconds: int) -> int:
            return milliseconds + offset_ms

        captions = list(self.iter_slice(start=start))
        _retime_captions(captions, mapping)

        if drop_before_zero:
            # by identity, as other captions can be equal to a dropped one
            dropped = {
                id(caption)
                for caption in captions
                if caption.end_in_milliseconds == 0
                }
            if dropped:
                self.captions[:] = [
                    caption
                    for caption in self.captions
                    if id(caption) not in dropped
                    ]

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

    def sort(self):
        """
        Sort the captions by start time, as WebVTT requires.

        Captions that start at the same time keep their order. The list of
        captions is sorted in place, so it stays the same list.
        """
        self.captions.sort(key=lambda caption: caption.start_in_milliseconds)

    def validate(self) -> typing.List[ValidationIssue]:
        """
        Return the problems found in the captions, in the order of captions.

        Errors are for captions that are not valid WebVTT: an end time that
        is not after the start time, a start time before that of the previous
        caption, which `sort` fixes, or a ``region`` cue setting of a region
        that is not defined. Warnings are for captions that are valid but
        likely have a mistake: a caption that overlaps an earlier one in
        time, or a caption without text.

        The blocks skipped when reading the captions are in
        ``parse_issues`` instead.

        :returns: a list of `ValidationIssue`, empty when there is no
            problem
        """
        issues = []
        region_ids = {region.id for region in self.regions if region.id}
        previous: typing.Optional[Caption] = None

        for index, caption in enumerate(self.captions):
            if caption.end_in_milliseconds <= caption.start_in_milliseconds:
                issues.append(ValidationIssue(
                    index, 'timing', 'error',
                    f'ends at {caption.end}, not after its start at '
                    f'{caption.start}'
                    ))

            # compared with the previous caption only, so a caption out of
            # place is reported once and not every caption after it
            if (previous is not None and
                    caption.start_in_milliseconds <
                    previous.start_in_milliseconds):
                issues.append(ValidationIssue(
                    index, 'order', 'error',
                    f'starts at {caption.start}, before caption {index}, '
                    f'which starts at {previous.start}'
                    ))
            previous = caption

            region = caption.settings.region
            if region is not None and region not in region_ids:
                issues.append(ValidationIssue(
                    index, 'region', 'error',
                    f'is in the region {region!r}, which is not defined'
                    ))

            if not caption.text.strip():
                issues.append(ValidationIssue(
                    index, 'empty', 'warning', 'has no text'
                    ))

        issues.extend(_overlaps(self.captions))
        # stable, so the issues of a caption keep the order above
        issues.sort(key=lambda issue: issue.index)
        return issues

    @property
    def total_length(self) -> float:
        """
        Return the total length of the captions in seconds.

        It is the time from the earliest start to the latest end of the
        captions, so the order of the captions does not matter, and it is
        never negative, even for a caption that ends before it starts.
        """
        if not self.captions:
            return 0.0
        start = self.captions[0].start_in_milliseconds
        end = self.captions[0].end_in_milliseconds
        for caption in self.captions[1:]:
            start = min(start, caption.start_in_milliseconds)
            end = max(end, caption.end_in_milliseconds)
        return max(end - start, 0) / 1000

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


def _overlaps(captions: typing.List[Caption]) -> typing.List[ValidationIssue]:
    """
    Return a warning for each caption that overlaps an earlier one in time.

    The captions are taken in order of start time, whatever their order in
    the list, and each is compared with the earlier one that ends last, so
    a caption is reported once even if it overlaps several. Captions whose
    end is not after their start have no time to overlap and are left out.

    :param captions: the captions
    :returns: a list of `ValidationIssue` with the ``overlap`` code
    """
    issues = []
    timed = sorted(
        (index for index, caption in enumerate(captions)
         if caption.end_in_milliseconds > caption.start_in_milliseconds),
        key=lambda index: captions[index].start_in_milliseconds
        )
    last_ending: typing.Optional[int] = None

    for index in timed:
        caption = captions[index]
        if last_ending is not None:
            other = captions[last_ending]
            if caption.start_in_milliseconds < other.end_in_milliseconds:
                issues.append(ValidationIssue(
                    index, 'overlap', 'warning',
                    f'starts at {caption.start}, before caption '
                    f'{last_ending + 1} ends at {other.end}'
                    ))
            if caption.end_in_milliseconds <= other.end_in_milliseconds:
                continue
        last_ending = index

    return issues


def _within_range(
        caption: Caption,
        start: typing.Optional[Timestamp],
        end: typing.Optional[Timestamp]
        ) -> bool:
    """
    Return whether a caption is within a time range.

    :param caption: the caption
    :param start: the start of the range, or None if it has no start
    :param end: the end of the range, or None if it has no end
    :returns: true if the caption does not start before the range or end
        after it
    """
    return (
        (not start or caption.start_time >= start) and
        (not end or caption.end_time <= end)
        )


def _overlaps_range(
        caption: Caption,
        start: typing.Optional[Timestamp],
        end: typing.Optional[Timestamp]
        ) -> bool:
    """
    Return whether a caption has any part in a time range.

    A caption within the range is always in it, also one without duration
    on its limits. Others must share some time with the range, so a caption
    only touching the range is not in it, and a range without duration
    overlaps nothing.

    :param caption: the caption
    :param start: the start of the range, or None if it has no start
    :param end: the end of the range, or None if it has no end
    :returns: true if the caption is within or overlaps the range
    """
    if _within_range(caption, start, end):
        return True
    if start and end and start >= end:
        return False
    return (
        (not start or caption.end_time > start) and
        (not end or caption.start_time < end)
        )


def _clipped(
        caption: Caption,
        start: typing.Optional[Timestamp],
        end: typing.Optional[Timestamp]
        ) -> Caption:
    """
    Return a copy of a caption trimmed to a time range.

    :param caption: the caption, which is left unchanged
    :param start: the start of the range, or None if it has no start
    :param end: the end of the range, or None if it has no end
    :returns: a copy sharing nothing with the caption, nor its times with
        other copies
    """
    clipped = caption.copy()
    if start and clipped.start_time < start:
        clipped.start = start
    if end and clipped.end_time > end:
        clipped.end = end
    return clipped


def _check_format(format: str):
    """
    Check that a format is supported.

    :param format: the format, such as ``vtt``

    :raises ValueError: if the format is not supported
    """
    if format not in _FORMATS:
        raise ValueError(f'Format {format} is not supported.')
