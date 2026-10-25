"""SRT format module."""

import typing
import re

from .models import (
    Caption, Style, _caption_from_timings, _iter_cue_text_tokens
    )
from .errors import MalformedFileError
from . import utils


_TIMESTAMP = r'\d+:\d{1,2}:\d{1,2}[,.]\d+'

_CUE_CLASS_SELECTOR = re.compile(r'::cue\(\s*\.([\w-]+)\s*\)')

# the cue tags that SRT players support
_SRT_TAGS = {'b', 'i', 'u'}


class SRTCueBlock:
    """Representation of a cue timing block."""

    CUE_TIMINGS_PATTERN = re.compile(
        rf'\s*({_TIMESTAMP})\s*-->\s*({_TIMESTAMP})'
        )

    def __init__(
            self,
            index: str,
            start: str,
            end: str,
            payload: typing.Sequence[str]
            ):
        """
        Initialize.

        :param start: start time
        :param end: end time
        :param payload: caption text
        """
        self.index = index
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
          len(lines) >= 2 and
          lines[0].strip().isdigit() and
          re.match(cls.CUE_TIMINGS_PATTERN, lines[1])
          )

    @classmethod
    def from_lines(
            cls,
            lines: typing.Sequence[str]
            ) -> 'SRTCueBlock':
        """
        Create a `SRTCueBlock` from lines of text.

        :param lines: the lines of text
        :returns: `SRTCueBlock` instance
        """
        index = lines[0]

        match = re.match(cls.CUE_TIMINGS_PATTERN, lines[1])
        assert match is not None

        payload = lines[2:]

        return cls(index, match.group(1), match.group(2), payload)


def parse(lines: typing.Sequence[str]) -> typing.List[Caption]:
    """
    Parse SRT captions from lines of text.

    :param lines: lines of text
    :returns: list of `Caption` objects

    :raises MalformedFileError: if the content is not in SRT format
    """
    if not is_valid_content(lines):
        raise MalformedFileError('Invalid format')

    return parse_captions(lines)


def is_valid_content(lines: typing.Sequence[str]) -> bool:
    """
    Validate lines of text for valid SRT content.

    :param lines: lines of text
    :returns: true for a valid SRT content
    """
    return bool(
        len(lines) >= 3 and
        lines[0].isdigit() and
        '-->' in lines[1]
    )


def _is_cue_start(lines: typing.Sequence[str]) -> bool:
    """
    Validate if the lines start with cue timings or a cue index and timings.

    A line with only digits followed by caption text is not a cue start,
    as caption text can have such a line, e.g. a year.

    :param lines: the lines to be validated
    :returns: true if the lines start a cue
    """
    return '-->' in lines[0] or (
        len(lines) > 1 and _is_index_and_timings(lines[0], lines[1])
        )


def _is_index(line: str) -> bool:
    """Return whether a line can be a cue index, a line with only digits."""
    return line.strip().isdigit()


def _is_index_and_timings(line: str, next_line: str) -> bool:
    """Return whether a line is a cue index followed by the cue timings."""
    return _is_index(line) and '-->' in next_line


def _iter_cue_blocks(
        lines: typing.Sequence[str]
        ) -> typing.Generator[typing.List[str], None, None]:
    """
    Iterate blocks of text, also splitting a block where a cue starts.

    A cue starts at a cue index followed by the cue timings, even without
    an empty line before it. A block with only a cue index followed by a
    block starting with the cue timings is joined with it, as the index of
    that cue.

    :param lines: lines of text
    """
    index_block: typing.Optional[typing.List[str]] = None

    for block_lines in _iter_split_blocks(lines):
        if index_block is not None:
            if '-->' in block_lines[0]:
                block_lines = index_block + block_lines
            else:
                yield index_block
            index_block = None

        if len(block_lines) == 1 and _is_index(block_lines[0]):
            index_block = block_lines
        else:
            yield block_lines

    if index_block is not None:
        yield index_block


def _iter_split_blocks(
        lines: typing.Sequence[str]
        ) -> typing.Generator[typing.List[str], None, None]:
    """
    Iterate blocks of text, splitting a block where a cue index follows.

    :param lines: lines of text
    """
    for block_lines in utils.iter_blocks_of_lines(lines):
        start = 0
        for i in range(1, len(block_lines) - 1):
            if _is_index_and_timings(block_lines[i], block_lines[i + 1]):
                yield block_lines[start:i]
                start = i
        yield block_lines[start:]


def parse_captions(lines: typing.Sequence[str]) -> typing.List[Caption]:
    """
    Parse captions from the text.

    Blocks of text that do not start a cue are taken as part of the text
    of the previous cue, as some files have empty lines in the caption
    text.

    :param lines: lines of text
    :returns: list of `Caption` objects
    """
    captions: typing.List[Caption] = []
    caption: typing.Optional[Caption] = None

    for block_lines in _iter_cue_blocks(lines):
        if _is_cue_start(block_lines):
            caption = None
            if SRTCueBlock.is_valid(block_lines):
                cue_block = SRTCueBlock.from_lines(block_lines)
                caption = _caption_from_timings(cue_block.start,
                                                cue_block.end,
                                                cue_block.payload
                                                )
                if caption is not None:
                    captions.append(caption)
        elif caption is not None:
            caption.lines.extend(block_lines)

    return [caption for caption in captions if caption.lines]


def _strip_css_comments(css: str) -> str:
    """
    Remove the comments from CSS.

    A comment without an end runs to the end of the CSS. This scans for
    the comments with ``str.find``, as a non-greedy regex for them rescans
    the rest of the CSS from every comment start without an end, which is
    quadratic in the length of the CSS.

    :param css: the CSS text
    :returns: the CSS without comments
    """
    parts = []
    pos = 0
    while True:
        start = css.find('/*', pos)
        if start < 0:
            break
        parts.append(css[pos:start])
        end = css.find('*/', start + 2)
        if end < 0:
            return ''.join(parts)
        pos = end + 2
    parts.append(css[pos:])
    return ''.join(parts)


def _css_colour(declarations: str) -> typing.Optional[str]:
    """
    Return the colour in the declarations of a CSS rule.

    The last ``color`` declaration applies. ``!important`` is removed, and
    a value that cannot be written in a ``font`` tag is ignored.

    :param declarations: the declarations of the rule
    :returns: the colour, or None when the rule has no colour
    """
    colour = None
    for declaration in declarations.split(';'):
        name, _, value = declaration.partition(':')
        value = value.partition('!')[0].strip()
        if (name.strip().lower() == 'color' and value and
                not any(char in value for char in '"<>')):
            colour = value
    return colour


def _cue_colours(
        styles: typing.Iterable[Style]
        ) -> typing.Dict[str, typing.Tuple[int, str]]:
    """
    Return the colours of the cue classes defined in the styles.

    Only the ``color`` of ``::cue(.class)`` selectors is read. Each class is
    mapped to the colour and the position of its rule, as when a cue has
    more than one class with a colour, the rule that comes last applies.

    :param styles: Iterable of `Style` objects
    :returns: a dict of class name to (rule position, colour)
    """
    colours = {}
    position = 0
    for style in styles:
        # split the rules on braces, as a regex for them is quadratic on
        # text without braces
        for rule in _strip_css_comments(style.text).split('}'):
            selectors, _, declarations = rule.rpartition('{')
            colour = _css_colour(declarations)
            if colour is None:
                continue
            position += 1
            for selector in selectors.split(','):
                match = _CUE_CLASS_SELECTOR.fullmatch(selector.strip())
                if match:
                    colours[match.group(1)] = (position, colour)
    return colours


def _srt_tags(
        tag: str,
        colours: typing.Mapping[str, typing.Tuple[int, str]]
        ) -> typing.Optional[typing.Tuple[str, str, str]]:
    """
    Return the SRT tags for a cue start tag.

    :param tag: the content of the cue start tag
    :param colours: the colours of the cue classes
    :returns: the tag name and the SRT start and end tags, which are empty
        when SRT has no tag for it, or None for a timestamp tag
    """
    name, *classes = (tag.split(maxsplit=1) or [''])[0].split('.')
    # timestamp tags have no name
    if not name.isalpha():
        return None
    # font tags of captions read from SRT are kept as they are
    if name == 'font':
        return name, f'<{tag}>', '</font>'
    start_tags = end_tags = ''
    if name in _SRT_TAGS:
        start_tags, end_tags = f'<{name}>', f'</{name}>'
    matches = [colours[cls] for cls in classes if cls in colours]
    if matches:
        start_tags += f'<font color="{max(matches)[1]}">'
        end_tags = '</font>' + end_tags
    return name, start_tags, end_tags


def _close_tags(
        open_tags: typing.List[typing.Tuple[str, str]],
        name: str
        ) -> typing.List[str]:
    """
    Close the last open tag with a name and the tags opened after it.

    :param open_tags: the names and SRT end tags of the open tags, which
        are removed when closed
    :param name: the name of the cue end tag
    :returns: the SRT end tags, or none when no tag with the name is open
    """
    names = [open_name for open_name, _ in open_tags]
    if name not in names:
        return []
    index = len(names) - 1 - names[::-1].index(name)
    closed = open_tags[index:]
    del open_tags[index:]
    return [end_tags for _, end_tags in reversed(closed)]


def _format_cue_text(
        text: str,
        colours: typing.Mapping[str, typing.Tuple[int, str]]
        ) -> str:
    """
    Convert the cue tags of a cue text to SRT tags.

    Bold, italic, underline and ``font`` tags are kept, and a class with a
    colour adds a ``font`` tag with that colour. Other tags are removed,
    keeping their text, and the tags left open at the end of the text are
    closed. Tags are found in each line, as when the tags are removed from
    the text, but stay open across lines.

    :param text: the cue text
    :param colours: the colours of the cue classes
    :returns: the text with SRT tags
    """
    lines = []
    open_tags: typing.List[typing.Tuple[str, str]] = []
    for line in text.split('\n'):
        output = []
        for token, is_tag in _iter_cue_text_tokens(line):
            if not is_tag:
                output.append(token)
            elif token.startswith('/'):
                output.extend(_close_tags(open_tags, token[1:].strip()))
            else:
                tags = _srt_tags(token, colours)
                if tags is not None:
                    name, start_tags, end_tags = tags
                    output.append(start_tags)
                    open_tags.append((name, end_tags))
        lines.append(''.join(output))
    lines[-1] += ''.join(end_tags for _, end_tags in reversed(open_tags))
    return '\n'.join(lines)


def write(
        f: typing.IO[str],
        captions: typing.Iterable[Caption],
        styles: typing.Optional[typing.Iterable[Style]] = None
        ):
    """
    Write captions to an output.

    :param f: file or file-like object
    :param captions: Iterable of `Caption` objects
    :param styles: Iterable of `Style` objects to keep the formatting of
        the cue text, or None to write the text without cue tags
    """
    colours = None if styles is None else _cue_colours(styles)
    output = []
    for index, caption in enumerate(captions, start=1):
        text = (caption.text if colours is None
                else _format_cue_text(caption.raw_text, colours))
        output.extend([
            f'{index}',
            '{} --> {}'.format(*map(lambda x: x.replace('.', ','),
                                    (caption.start, caption.end))
                               ),
            *(line for line in text.split('\n') if line.strip()),
            ''
            ])
    f.write('\n'.join(output).rstrip())
