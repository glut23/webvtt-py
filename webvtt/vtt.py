"""VTT format module."""

import re
import typing
from dataclasses import dataclass, field

from .errors import MalformedFileError, MalformedCaptionError
from .models import Caption, Style

TIMESTAMP = r'(?:\d+:)?\d{1,2}:\d{1,2}\.\d{1,3}'
STRICT_TIMESTAMP = r'(?:\d{2,}:)?\d{2}:\d{2}\.\d{3}'


@dataclass
class ParserOutput:
    """Output of parser."""

    styles: typing.List[Style]
    captions: typing.List[Caption]
    header_comments: typing.List[str]
    footer_comments: typing.List[str]
    header_text: str = ''
    metadata: typing.List[str] = field(default_factory=list)

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
            footer_comments=data.get('footer_comments', [])
            )


class WebVTTCueBlock:
    """Representation of a cue timing block."""

    CUE_TIMINGS_PATTERN = re.compile(
        rf'\s*({TIMESTAMP})\s*-->\s*({TIMESTAMP})'
        )
    STRICT_CUE_TIMINGS_PATTERN = re.compile(
        rf'\s*({STRICT_TIMESTAMP})\s*-->\s*({STRICT_TIMESTAMP})(?=\s|$)'
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
            lines: typing.Sequence[str],
            strict: bool = False
            ) -> bool:
        """
        Validate the lines for a match of a cue time block.

        Timestamps with fields shorter than the WebVTT format requires, as
        in ``0:0:13.540``, are accepted unless strict.

        :param lines: the lines to be validated
        :param strict: only accept timestamps in the WebVTT format
        :returns: true for a matching cue time block
        """
        pattern = (
            cls.STRICT_CUE_TIMINGS_PATTERN if strict
            else cls.CUE_TIMINGS_PATTERN
            )
        return bool(
            (
              len(lines) >= 1 and
              re.match(pattern, lines[0]) and
              (len(lines) < 2 or "-->" not in lines[1])
              ) or
            (
              len(lines) >= 2 and
              "-->" not in lines[0] and
              re.match(pattern, lines[1]) and
              (len(lines) < 3 or "-->" not in lines[2])
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
                not any(not line or '-->' in line for line in lines)
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

    output = parse_items(lines, strict)
    output.header_text, output.metadata = parse_header(
        next(iter_blocks_of_lines(lines))
        )
    return output


def is_valid_content(lines: typing.Sequence[str]) -> bool:
    """
    Validate lines of text for valid VTT content.

    :param lines: lines of text
    :returns: true for a valid VTT content
    """
    return bool(lines and lines[0].startswith('WEBVTT'))


def iter_blocks_of_lines(
        lines: typing.Iterable[str],
        strict: bool = False
        ) -> typing.Generator[typing.List[str], None, None]:
    """
    Iterate blocks of text following the WebVTT parsing rules.

    A block ends at an empty line, so lines containing only whitespace are
    part of the block. A line containing "-->" that cannot be the cue
    timings line of the current block starts a new block.

    :param lines: lines of text
    :param strict: raise an error when a block is not ended by an empty line
        before a cue timings line

    :raises MalformedCaptionError: if strict and a cue timings line follows
        a block without an empty line in between
    """
    block: typing.List[str] = []
    in_header = True

    for line in lines:
        if not line or _starts_new_block(block, line, in_header):
            if strict and line and not in_header:
                raise MalformedCaptionError(
                    f'Invalid cue block {[*block, line]!r}'
                    )
            if block:
                yield block
                block = []
                in_header = False

        if line:
            block.append(line)

    if block:
        yield block


def _starts_new_block(
        block: typing.Sequence[str],
        line: str,
        in_header: bool
        ) -> bool:
    """
    Return whether a line containing "-->" starts a new block.

    The line can only be the cue timings line of the current block when it
    is the block's first line, or the second one following an identifier.

    :param block: lines of the current block
    :param line: the next line of text
    :param in_header: true if the current block is the file header
    :returns: true if the line starts a new block
    """
    return bool(
        block and
        '-->' in line and
        (in_header or len(block) > 1 or '-->' in block[0])
        )


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

    for block_lines in iter_blocks_of_lines(lines, strict):
        item = parse_item(block_lines, strict)
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
         'footer_comments': [comment.text for comment in comments]
         }
        )


def parse_header(
        lines: typing.Sequence[str]
        ) -> typing.Tuple[str, typing.List[str]]:
    """
    Parse the header block of the file.

    :param lines: lines of the header block, the first one starting with
        "WEBVTT"
    :returns: the text following "WEBVTT" in the first line and the
        metadata lines that follow it
    """
    text = lines[0][len('WEBVTT'):]
    if text[:1] in (' ', '\t'):
        text = text[1:]
    return text, list(lines[1:])


def validate_header(header_text: str, metadata: typing.Iterable[str]):
    """
    Validate the header text and metadata lines before writing them.

    :param header_text: the text following "WEBVTT" in the first line
    :param metadata: the metadata lines of the header

    :raises ValueError: if the header text contains a line break, or a
        metadata line is empty, contains a line break or contains "-->"
    """
    if _has_line_break(header_text):
        raise ValueError(
            f'Header text must be a single line: {header_text!r}'
            )

    for line in metadata:
        if not line or _has_line_break(line) or '-->' in line:
            raise ValueError(
                'Metadata lines must be single non-empty lines without '
                f'"-->": {line!r}'
                )


def _has_line_break(text: str) -> bool:
    """
    Return whether the text contains a WebVTT line terminator.

    :param text: the text to check
    :returns: true if the text contains a carriage return or a line feed
    """
    return '\n' in text or '\r' in text


def parse_item(
        lines: typing.Sequence[str],
        strict: bool = False
        ) -> typing.Union[Caption, Style, None]:
    """
    Parse an item from lines of text.

    :param lines: lines of text
    :param strict: only accept cue timestamps in the WebVTT format and
        raise an error for cues with an invalid timestamp
    :returns: An item (Caption or Style) if found, otherwise None

    :raises MalformedCaptionError: if strict and a cue has an invalid
        timestamp
    """
    if WebVTTCueBlock.is_valid(lines, strict):
        cue_block = WebVTTCueBlock.from_lines(lines)
        try:
            return Caption(cue_block.start,
                           cue_block.end,
                           cue_block.payload,
                           cue_block.identifier
                           )
        except MalformedCaptionError:
            if strict:
                raise
            return None

    if WebVTTStyleBlock.is_valid(lines):
        return Style(WebVTTStyleBlock.from_lines(lines).text)

    return None


def write(
        f: typing.IO[str],
        captions: typing.Iterable[Caption],
        styles: typing.Iterable[Style],
        header_comments: typing.Iterable[str],
        footer_comments: typing.Iterable[str],
        header_text: str = '',
        metadata: typing.Iterable[str] = ()
        ):
    """
    Write captions to an output.

    :param f: file or file-like object
    :param captions: Iterable of `Caption` objects
    :param styles: Iterable of `Style` objects
    :param header_comments: the comments for the header
    :param footer_comments: the comments for the footer
    :param header_text: the text following "WEBVTT" in the first line
    :param metadata: the metadata lines of the header

    :raises ValueError: if the header text or metadata are not valid
    """
    f.write(
        to_str(captions,
               styles,
               header_comments,
               footer_comments,
               header_text,
               metadata
               )
        )


def to_str(
        captions: typing.Iterable[Caption],
        styles: typing.Iterable[Style],
        header_comments: typing.Iterable[str],
        footer_comments: typing.Iterable[str],
        header_text: str = '',
        metadata: typing.Iterable[str] = ()
        ) -> str:
    """
    Convert captions to a string with webvtt format.

    :param captions: the iterable of `Caption` objects
    :param styles: the iterable of `Style` objects
    :param header_comments: the comments for the header
    :param footer_comments: the comments for the footer
    :param header_text: the text following "WEBVTT" in the first line
    :param metadata: the metadata lines of the header
    :returns: String of the content in WebVTT format.

    :raises ValueError: if the header text or metadata are not valid
    """
    metadata = list(metadata)
    validate_header(header_text, metadata)

    output = [f'WEBVTT {header_text}' if header_text else 'WEBVTT',
              *metadata
              ]

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
