"""VTT format module."""

import re
import typing
from dataclasses import dataclass

from .errors import MalformedFileError, MalformedCaptionError
from .models import Caption, Style, TimestampMap
from . import utils


TIMESTAMP_MAP_HEADER = 'X-TIMESTAMP-MAP='


@dataclass
class ParserOutput:
    """Output of parser."""

    styles: typing.List[Style]
    captions: typing.List[Caption]
    header_comments: typing.List[str]
    footer_comments: typing.List[str]
    timestamp_map: typing.Optional[TimestampMap] = None

    @classmethod
    def from_data(
            cls,
            data: typing.Mapping[str, typing.Any]
            ) -> 'ParserOutput':
        """
        Return a `ParserOutput` instance from the provided data.

        :param data: data from the parser
        :returns: an instance of `ParserOutput`
        """
        items = data.get('items', [])
        return cls(
            captions=[it for it in items if isinstance(it, Caption)],
            styles=[it for it in items if isinstance(it, Style)],
            header_comments=data.get('header_comments', []),
            footer_comments=data.get('footer_comments', []),
            timestamp_map=data.get('timestamp_map')
            )


class WebVTTCueBlock:
    """Representation of a cue timing block."""

    CUE_TIMINGS_PATTERN = re.compile(
        r'\s*((?:\d+:)?\d{2}:\d{2}\.\d{3})'
        r'\s*-->\s*'
        r'((?:\d+:)?\d{2}:\d{2}\.\d{3})'
        )

    def __init__(
            self,
            identifier,
            start,
            end,
            payload
            ):
        """
        Initialize.

        :param start: start time
        :param end: end time
        :param payload: caption text
        """
        self.identifier = identifier
        self.start = start
        self.end = end
        self.payload = payload

    @classmethod
    def is_valid(
            cls,
            lines: typing.Sequence[str]
            ) -> bool:
        """
        Validate the lines for a match of a cue time block.

        :param lines: the lines to be validated
        :returns: true for a matching cue time block
        """
        return bool(
            (
              len(lines) >= 2 and
              re.match(cls.CUE_TIMINGS_PATTERN, lines[0]) and
              "-->" not in lines[1]
              ) or
            (
              len(lines) >= 3 and
              "-->" not in lines[0] and
              re.match(cls.CUE_TIMINGS_PATTERN, lines[1]) and
              "-->" not in lines[2]
              )
        )

    @classmethod
    def from_lines(
            cls,
            lines: typing.Iterable[str]
            ) -> 'WebVTTCueBlock':
        """
        Create a `WebVTTCueBlock` from lines of text.

        :param lines: the lines of text
        :returns: `WebVTTCueBlock` instance
        """
        identifier = None
        start = None
        end = None
        payload = []

        for line in lines:
            timing_match = re.match(cls.CUE_TIMINGS_PATTERN, line)
            if timing_match:
                start = timing_match.group(1)
                end = timing_match.group(2)
            elif not start:
                identifier = line
            else:
                payload.append(line)

        return cls(identifier, start, end, payload)

    @staticmethod
    def format_lines(caption: Caption) -> typing.List[str]:
        """
        Return the lines for a cue block.

        :param caption: the `Caption` instance
        :returns: list of lines for a cue block
        """
        return [
            '',
            *(identifier for identifier in {caption.identifier} if identifier),
            f'{caption.start} --> {caption.end}',
            *caption.lines
        ]


class WebVTTCommentBlock:
    """Representation of a comment block."""

    COMMENT_PATTERN = re.compile(r'NOTE\s(.*?)\Z', re.DOTALL)

    def __init__(self, text: str):
        """
        Initialize.

        :param text: comment text
        """
        self.text = text

    @classmethod
    def is_valid(
            cls,
            lines: typing.Sequence[str]
            ) -> bool:
        """
        Validate the lines for a match of a comment block.

        :param lines: the lines to be validated
        :returns: true for a matching comment block
        """
        return bool(lines and lines[0].startswith('NOTE'))

    @classmethod
    def from_lines(
            cls,
            lines: typing.Iterable[str]
            ) -> 'WebVTTCommentBlock':
        """
        Create a `WebVTTCommentBlock` from lines of text.

        :param lines: the lines of text
        :returns: `WebVTTCommentBlock` instance
        """
        match = cls.COMMENT_PATTERN.match('\n'.join(lines))
        return cls(text=match.group(1).strip() if match else '')

    @staticmethod
    def format_lines(lines: str) -> typing.List[str]:
        """
        Return the lines for a comment block.

        :param lines: comment lines
        :returns: list of lines for a comment block
        """
        list_of_lines = lines.split('\n')

        if len(list_of_lines) == 1:
            return [f'NOTE {lines}']

        return ['NOTE', *list_of_lines]


class WebVTTStyleBlock:
    """Representation of a style block."""

    STYLE_PATTERN = re.compile(r'STYLE\s(.*?)\Z', re.DOTALL)

    def __init__(self, text: str):
        """
        Initialize.

        :param text: style text
        """
        self.text = text

    @classmethod
    def is_valid(
            cls,
            lines: typing.Sequence[str]
            ) -> bool:
        """
        Validate the lines for a match of a style block.

        :param lines: the lines to be validated
        :returns: true for a matching style block
        """
        return (len(lines) >= 2 and
                lines[0] == 'STYLE' and
                not any(line.strip() == '' or '-->' in line for line in lines)
                )

    @classmethod
    def from_lines(
            cls,
            lines: typing.Iterable[str]
            ) -> 'WebVTTStyleBlock':
        """
        Create a `WebVTTStyleBlock` from lines of text.

        :param lines: the lines of text
        :returns: `WebVTTStyleBlock` instance
        """
        match = cls.STYLE_PATTERN.match('\n'.join(lines))
        return cls(text=match.group(1).strip() if match else '')

    @staticmethod
    def format_lines(lines: typing.List[str]) -> typing.List[str]:
        """
        Return the lines for a style block.

        :param lines: style lines
        :returns: list of lines for a style block
        """
        return ['STYLE', *lines]


def parse(
        lines: typing.Sequence[str],
        strict: bool = False
        ) -> ParserOutput:
    """
    Parse VTT captions from lines of text.

    :param lines: lines of text
    :param strict: raise an error on malformed cue blocks instead of
        ignoring them
    :returns: object `ParserOutput` with all parsed items

    :raises MalformedFileError: if the content is not in WebVTT format
    :raises MalformedCaptionError: if strict and a cue block is malformed
    """
    if not is_valid_content(lines):
        raise MalformedFileError('Invalid format')

    return parse_items(lines, strict)


def is_valid_content(lines: typing.Sequence[str]) -> bool:
    """
    Validate lines of text for valid VTT content.

    :param lines: lines of text
    :returns: true for a valid VTT content
    """
    return bool(lines and lines[0].startswith('WEBVTT'))


def _parse_timestamp_map(
        lines: typing.Sequence[str]
        ) -> typing.Optional[TimestampMap]:
    """
    Return a `TimestampMap` parsed from a header line, or None.

    :param lines: lines of text
    :returns: a `TimestampMap` instance if a header line is found, else None
    """
    for line in lines:
        if line.startswith(TIMESTAMP_MAP_HEADER):
            return TimestampMap.from_string(
                line[len(TIMESTAMP_MAP_HEADER):]
                )
    return None


def parse_items(
        lines: typing.Sequence[str],
        strict: bool = False
        ) -> ParserOutput:
    """
    Parse items from the text.

    :param lines: lines of text
    :param strict: raise an error on malformed cue blocks instead of
        ignoring them
    :returns: an object `ParserOutput` with all parsed items

    :raises MalformedCaptionError: if strict and a cue block is malformed
    """
    header_comments: typing.List[str] = []
    items: typing.List[typing.Union[Caption, Style]] = []
    comments: typing.List[WebVTTCommentBlock] = []
    timestamp_map: typing.Optional[TimestampMap] = None

    for block_lines in utils.iter_blocks_of_lines(lines):
        if not items and timestamp_map is None:
            timestamp_map = _parse_timestamp_map(block_lines)

        item = parse_item(block_lines)
        if item:
            item.comments = [comment.text for comment in comments]
            comments = []
            items.append(item)
        elif WebVTTCommentBlock.is_valid(block_lines):
            comments.append(WebVTTCommentBlock.from_lines(block_lines))
        elif strict and any('-->' in line for line in block_lines):
            raise MalformedCaptionError(
                f'Invalid cue block {block_lines!r}'
                )

    if items:
        header_comments, items[0].comments = items[0].comments, header_comments

    return ParserOutput.from_data(
        {'items': items,
         'header_comments': header_comments,
         'footer_comments': [comment.text for comment in comments],
         'timestamp_map': timestamp_map
         }
        )


def parse_item(
        lines: typing.Sequence[str]
        ) -> typing.Union[Caption, Style, None]:
    """
    Parse an item from lines of text.

    :param lines: lines of text
    :returns: An item (Caption or Style) if found, otherwise None
    """
    if WebVTTCueBlock.is_valid(lines):
        cue_block = WebVTTCueBlock.from_lines(lines)
        return Caption(cue_block.start,
                       cue_block.end,
                       cue_block.payload,
                       cue_block.identifier
                       )

    if WebVTTStyleBlock.is_valid(lines):
        return Style(WebVTTStyleBlock.from_lines(lines).text)

    return None


def write(
        f: typing.IO[str],
        captions: typing.Iterable[Caption],
        styles: typing.Iterable[Style],
        header_comments: typing.Iterable[str],
        footer_comments: typing.Iterable[str],
        timestamp_map: typing.Optional[TimestampMap] = None
        ):
    """
    Write captions to an output.

    :param f: file or file-like object
    :param captions: Iterable of `Caption` objects
    :param styles: Iterable of `Style` objects
    :param header_comments: the comments for the header
    :param footer_comments: the comments for the footer
    :param timestamp_map: optional `TimestampMap` written right after the
        ``WEBVTT`` line
    """
    f.write(
        to_str(captions,
               styles,
               header_comments,
               footer_comments,
               timestamp_map
               )
        )


def to_str(
        captions: typing.Iterable[Caption],
        styles: typing.Iterable[Style],
        header_comments: typing.Iterable[str],
        footer_comments: typing.Iterable[str],
        timestamp_map: typing.Optional[TimestampMap] = None
        ) -> str:
    """
    Convert captions to a string with webvtt format.

    :param captions: the iterable of `Caption` objects
    :param styles: the iterable of `Style` objects
    :param header_comments: the comments for the header
    :param footer_comments: the comments for the footer
    :param timestamp_map: optional `TimestampMap` written right after the
        ``WEBVTT`` line
    :returns: String of the content in WebVTT format.
    """
    output = ['WEBVTT']

    if timestamp_map is not None:
        output.append(str(timestamp_map))

    for comment in header_comments:
        output.extend([
            '',
            *WebVTTCommentBlock.format_lines(comment)
        ])

    for style in styles:
        for comment in style.comments:
            output.extend([
                '',
                *WebVTTCommentBlock.format_lines(comment)
            ])
        output.extend([
            '',
            *WebVTTStyleBlock.format_lines(style.lines)
            ])

    for caption in captions:
        for comment in caption.comments:
            output.extend([
                '',
                *WebVTTCommentBlock.format_lines(comment)
            ])
        output.extend(WebVTTCueBlock.format_lines(caption))

    if not footer_comments:
        output.append('')

    for comment in footer_comments:
        output.extend([
            '',
            *WebVTTCommentBlock.format_lines(comment)
        ])

    return '\n'.join(output)
