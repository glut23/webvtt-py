"""VTT format module."""

import re
import typing
from dataclasses import dataclass

from .errors import MalformedFileError, MalformedCaptionError
from .models import Caption, Style


@dataclass
class ParserOutput:
    """Output of parser."""

    styles: typing.List[Style]
    captions: typing.List[Caption]
    header_comments: typing.List[str]
    footer_comments: typing.List[str]

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
              len(lines) >= 1 and
              re.match(cls.CUE_TIMINGS_PATTERN, lines[0]) and
              (len(lines) < 2 or "-->" not in lines[1])
              ) or
            (
              len(lines) >= 2 and
              "-->" not in lines[0] and
              re.match(cls.CUE_TIMINGS_PATTERN, lines[1]) and
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

    return parse_items(lines, strict)


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
        if not line:
            if block:
                yield block
                block = []
                in_header = False
            continue

        if _starts_new_block(block, line, in_header):
            if strict and not in_header:
                raise MalformedCaptionError(
                    f'Invalid cue block {[*block, line]!r}'
                    )
            yield block
            block = []
            in_header = False

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
         'footer_comments': [comment.text for comment in comments]
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
        footer_comments: typing.Iterable[str]
        ):
    """
    Write captions to an output.

    :param f: file or file-like object
    :param captions: Iterable of `Caption` objects
    :param styles: Iterable of `Style` objects
    :param header_comments: the comments for the header
    :param footer_comments: the comments for the footer
    """
    f.write(
        to_str(captions,
               styles,
               header_comments,
               footer_comments
               )
        )


def to_str(
        captions: typing.Iterable[Caption],
        styles: typing.Iterable[Style],
        header_comments: typing.Iterable[str],
        footer_comments: typing.Iterable[str]
        ) -> str:
    """
    Convert captions to a string with webvtt format.

    :param captions: the iterable of `Caption` objects
    :param styles: the iterable of `Style` objects
    :param header_comments: the comments for the header
    :param footer_comments: the comments for the footer
    :returns: String of the content in WebVTT format.
    """
    output = ['WEBVTT']

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
