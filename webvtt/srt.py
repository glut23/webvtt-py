"""SRT format module."""

import operator
import typing
import re

from .models import (
    Caption,
    CueSettings,
    ParseIssue,
    Style,
    _caption_from_timings,
    _iter_cue_text_tokens,
    _skipped_block
    )
from .errors import MalformedFileError
from . import utils


_TIMESTAMP = r'[0-9]+:[0-9]{1,2}:[0-9]{1,2}[,.][0-9]+'

_CUE_CLASS_SELECTOR = re.compile(r'::cue\(\s*\.([\w-]+)\s*\)')

# the cue tags that SRT players support
_SRT_TAGS = {'b', 'i', 'u'}

# the color of a font tag, quoted or not
_FONT_COLOUR = re.compile(
    r'''\bcolor\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s"']+))''',
    re.IGNORECASE
    )

# a colour that can be written in a style, as a name, a hex colour or a
# function such as rgb(255, 0, 0), with its parentheses balanced so that
# the rest of the style is read
_COLOUR_VALUE = re.compile(r'#?[\w-]+(?:\([\w\s,.%/+-]*\))?')

# a {\anN} tag, which places the cue as the keys of a numeric keypad
_POSITION_TAG = re.compile(r'\{\\an([1-9])\}')

# the line and align cue settings of each {\anN} tag
_POSITIONS: typing.Dict[
    int, typing.Tuple[typing.Optional[str], typing.Optional[str]]
    ] = {
    1: (None, 'left'), 2: (None, None), 3: (None, 'right'),
    4: ('50%,center', 'left'), 5: ('50%,center', None),
    6: ('50%,center', 'right'),
    7: ('0', 'left'), 8: ('0', None), 9: ('0', 'right'),
    }


class SRTCueBlock:
    """Representation of a cue timing block."""

    CUE_TIMINGS_PATTERN = re.compile(
        rf'\s*({_TIMESTAMP})\s*-->\s*({_TIMESTAMP})'
        )

    def __init__(
            self,
            index: typing.Optional[str],
            start: str,
            end: str,
            payload: typing.Sequence[str]
            ):
        """
        Initialize.

        :param index: cue index, or None for a cue without an index
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

        The cue index is optional, as most SRT players read cues without
        one.

        :param lines: the lines to be validated
        :returns: true for a matching cue time block
        """
        timings = _timings_line(lines)
        return bool(
          len(lines) > timings and
          re.match(cls.CUE_TIMINGS_PATTERN, lines[timings])
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
        timings = _timings_line(lines)
        index = lines[0] if timings else None

        match = re.match(cls.CUE_TIMINGS_PATTERN, lines[timings])
        assert match is not None

        payload = lines[timings + 1:]

        return cls(index, match.group(1), match.group(2), payload)


def parse(
        lines: typing.Sequence[str],
        issues: typing.Optional[typing.List[ParseIssue]] = None,
        styles: typing.Optional[typing.List[Style]] = None
        ) -> typing.List[Caption]:
    r"""
    Parse SRT captions from lines of text.

    The colours of ``font`` tags become cue classes, and ``{\anN}`` tags
    become cue settings, see `parse_captions`.

    :param lines: lines of text
    :param issues: a list to add the blocks that are skipped to
    :param styles: a list to add the style of the colours of the cue
        classes to
    :returns: list of `Caption` objects

    :raises MalformedFileError: if the content is not in SRT format
    """
    if not is_valid_content(lines):
        raise MalformedFileError('Invalid format')

    return parse_captions(lines, issues, styles)


def is_valid_content(lines: typing.Sequence[str]) -> bool:
    """
    Validate lines of text for valid SRT content.

    The content is valid when it starts with a cue index and the cue
    timings, after any blank lines. The first cue can have no text.

    :param lines: lines of text
    :returns: true for a valid SRT content
    """
    start = next((i for i, line in enumerate(lines) if line.strip()),
                 len(lines))
    return bool(
        len(lines) >= start + 2 and
        _is_index(lines[start]) and
        '-->' in lines[start + 1]
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
    line = line.strip()
    return line.isascii() and line.isdigit()


def _timings_line(lines: typing.Sequence[str]) -> int:
    """Return the position of the cue timings, after the index if any."""
    return 1 if lines and _is_index(lines[0]) else 0


def _is_index_and_timings(line: str, next_line: str) -> bool:
    """Return whether a line is a cue index followed by the cue timings."""
    return _is_index(line) and '-->' in next_line


def _iter_cue_blocks(
        lines: typing.Sequence[str]
        ) -> typing.Generator[utils._NumberedBlock, None, None]:
    """
    Iterate blocks of text, also splitting a block where a cue starts.

    A cue starts at a cue index followed by the cue timings, even without
    an empty line before it. A block with only a cue index followed by a
    block starting with the cue timings is joined with it, as the index of
    that cue.

    :param lines: lines of text
    :returns: the line number where each block starts, from 1, and its lines
    """
    index_block: typing.Optional[utils._NumberedBlock] = None

    for number, block_lines in _iter_split_blocks(lines):
        if index_block is not None:
            if '-->' in block_lines[0]:
                number = index_block[0]
                block_lines = index_block[1] + block_lines
            else:
                yield index_block
            index_block = None

        if len(block_lines) == 1 and _is_index(block_lines[0]):
            index_block = number, block_lines
        else:
            yield number, block_lines

    if index_block is not None:
        yield index_block


def _iter_split_blocks(
        lines: typing.Sequence[str]
        ) -> typing.Generator[utils._NumberedBlock, None, None]:
    """
    Iterate blocks of text, splitting a block where a cue index follows.

    :param lines: lines of text
    :returns: the line number where each block starts, from 1, and its lines
    """
    for number, block_lines in utils._iter_numbered_blocks(lines):
        start = 0
        for i in range(1, len(block_lines) - 1):
            if _is_index_and_timings(block_lines[i], block_lines[i + 1]):
                yield number + start, block_lines[start:i]
                start = i
        yield number + start, block_lines[start:]


def parse_captions(
        lines: typing.Sequence[str],
        issues: typing.Optional[typing.List[ParseIssue]] = None,
        styles: typing.Optional[typing.List[Style]] = None
        ) -> typing.List[Caption]:
    r"""
    Parse captions from the text.

    Blocks of text that do not start a cue are taken as part of the text
    of the previous cue, as some files have empty lines in the caption
    text. They are skipped when there is no such cue, as when the previous
    cue is not valid.

    A ``font`` tag with a colour becomes a ``c`` tag with a class for the
    colour, named from it, as in ``<c.color-ff0000>``, with a ``::cue``
    rule for each class in a style. Other ``font`` tags and attributes
    are removed, keeping their text. The first ``{\anN}`` tag of a cue
    becomes its ``line`` and ``align`` cue settings, and all of them are
    removed from the text, as are the lines that they leave empty.

    :param lines: lines of text
    :param issues: a list to add the blocks that are skipped to
    :param styles: a list to add the style of the colours of the cue
        classes to, when there are any
    :returns: list of `Caption` objects
    """
    skipped: typing.List[ParseIssue] = []
    cues = _read_cues(lines, skipped)
    _convert_captions([caption for _, _, caption in cues], styles)

    # a cue has no text only after the blocks that can add to it are read
    skipped.extend(
        _skipped_block(number, 'Cue without text', block_lines)
        for number, block_lines, caption in cues if not caption.lines
        )
    if issues is not None:
        issues.extend(sorted(skipped, key=operator.attrgetter('line')))

    return [caption for _, _, caption in cues if caption.lines]


def _read_cues(
        lines: typing.Sequence[str],
        skipped: typing.List[ParseIssue]
        ) -> typing.List[typing.Tuple[int, typing.List[str], Caption]]:
    """
    Read the cues of the text, with the blocks that add to their text.

    :param lines: lines of text
    :param skipped: a list to add the blocks that are skipped to
    :returns: the line number, the lines of the block and the caption of
        each cue
    """
    cues: typing.List[typing.Tuple[int, typing.List[str], Caption]] = []
    caption: typing.Optional[Caption] = None

    for number, block_lines in _iter_cue_blocks(lines):
        if _is_cue_start(block_lines):
            caption = _parse_cue(block_lines)
            if caption is None:
                skipped.append(_skipped_block(
                    number, 'Invalid cue block', block_lines
                    ))
            else:
                cues.append((number, block_lines, caption))
        elif caption is not None:
            caption.lines.extend(block_lines)
        else:
            skipped.append(_skipped_block(
                number, 'Invalid block', block_lines
                ))
    return cues


def _parse_cue(lines: typing.Sequence[str]) -> typing.Optional[Caption]:
    """
    Parse a cue from the lines of a block that starts a cue.

    :param lines: the lines of the block
    :returns: a `Caption`, or None if the cue is not valid
    """
    if not SRTCueBlock.is_valid(lines):
        return None

    cue_block = SRTCueBlock.from_lines(lines)
    return _caption_from_timings(cue_block.start,
                                 cue_block.end,
                                 cue_block.payload
                                 )


def _convert_captions(
        captions: typing.Iterable[Caption],
        styles: typing.Optional[typing.List[Style]]
        ):
    """
    Convert the font and position tags of the captions read from SRT.

    :param captions: the captions, changed in place
    :param styles: a list to add the style of the colours of the cue
        classes to, when there are any
    """
    # the classes of the colours, in order of first use
    classes: typing.Dict[str, str] = {}
    for caption in captions:
        _convert_markup(caption, classes)
    if classes and styles is not None:
        styles.append(_colour_style(classes))


def _convert_markup(caption: Caption, classes: typing.Dict[str, str]):
    """
    Convert the font and position tags of a caption read from SRT.

    :param caption: the caption, changed in place
    :param classes: the classes of the colours, which new colours are
        added to
    """
    position = None
    lines = []
    # whether each open font tag became a c tag, as tags stay open across
    # lines
    open_fonts: typing.List[bool] = []
    for line in caption.lines:
        match = _POSITION_TAG.search(line)
        if match and position is None:
            position = int(match.group(1))
        converted = _convert_fonts(
            _POSITION_TAG.sub('', line), open_fonts, classes
            )
        # a line of only tags that are removed would end the cue
        if converted.strip() or converted == line:
            lines.append(converted)
    caption.lines = lines

    if position is not None:
        line_setting, align = _POSITIONS[position]
        caption.settings = CueSettings(line=line_setting, align=align)


def _convert_fonts(
        line: str,
        open_fonts: typing.List[bool],
        classes: typing.Dict[str, str]
        ) -> str:
    """
    Convert the font tags of a line of text to c tags with a class.

    :param line: the line of text
    :param open_fonts: whether each open font tag became a c tag, which is
        updated with the tags of the line
    :param classes: the classes of the colours, which new colours are
        added to
    :returns: the line with the font tags converted or removed
    """
    output = []
    for token, is_tag in _iter_cue_text_tokens(line):
        if not is_tag:
            output.append(token)
            continue
        name, *attributes = token.split(None, 1) or ['']
        name = name.lower()
        if name == 'font':
            class_name = _colour_class(''.join(attributes), classes)
            open_fonts.append(class_name is not None)
            if class_name is not None:
                output.append(f'<c.{class_name}>')
        elif name == '/font':
            if open_fonts and open_fonts.pop():
                output.append('</c>')
        else:
            output.append(f'<{token}>')
    return ''.join(output)


def _colour_class(
        attributes: str,
        classes: typing.Dict[str, str]
        ) -> typing.Optional[str]:
    """
    Return the class of the colour of a font tag.

    The class is named from the colour, as ``color-ff0000`` for
    ``#ff0000``, with a number added when another colour has the name.

    :param attributes: the attributes of the font tag
    :param classes: the classes of the colours, which a new colour is
        added to
    :returns: the class, or None when the tag has no colour that can be
        written in a style
    """
    match = _FONT_COLOUR.search(attributes)
    if match is None:
        return None
    colour = next(g for g in match.groups() if g is not None).strip().lower()
    words = re.findall(r'[^\W_]+', colour)
    if not words or not _COLOUR_VALUE.fullmatch(colour):
        return None

    if colour not in classes:
        name = base = 'color-' + '-'.join(words)
        taken = set(classes.values())
        number = 2
        while name in taken:
            name = f'{base}-{number}'
            number += 1
        classes[colour] = name
    return classes[colour]


def _colour_style(classes: typing.Mapping[str, str]) -> Style:
    """
    Return the style with the colour of each class.

    :param classes: the classes of the colours
    :returns: a `Style` with a ``::cue`` rule for each class
    """
    lines = []
    for colour, name in classes.items():
        lines.extend([f'::cue(.{name}) {{', f'  color: {colour};', '}'])
    return Style(lines)


def _position_tag(settings: CueSettings) -> str:
    r"""
    Return the ``{\anN}`` tag for the line and align cue settings.

    The line is at the top for a line number from the top or a percentage
    under a third, in the middle for a percentage up to two thirds, and
    at the bottom otherwise. Only the left and right alignments are
    written, as the side of start and end depends on the direction of the
    text, and many files, such as those of YouTube, align every cue to the
    start.

    :param settings: the cue settings
    :returns: the tag, or empty for a cue at the bottom center, where SRT
        players place it, or with vertical text
    """
    if settings.vertical:
        return ''
    # 0 for the bottom, 1 for the middle and 2 for the top
    row = 0
    line = (settings.line or '').partition(',')[0]
    if line.endswith('%'):
        percentage = float(line[:-1])
        if percentage < 100 / 3:
            row = 2
        elif percentage <= 200 / 3:
            row = 1
    elif line and int(line) >= 0:
        row = 2
    column = {'left': 0, 'right': 2}.get(
        settings.align or '', 1
        )
    number = row * 3 + column + 1
    return '' if number == 2 else f'{{\\an{number}}}'


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
    # font tags, as in WebVTT written by versions that kept those of SRT,
    # are kept as they are
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
    r"""
    Write captions to an output.

    Captions without text, such as text of blank lines or only of cue tags,
    are left out, as a cue without text cannot be read back from SRT, and
    the others are numbered consecutively. The ``line`` and ``align`` cue
    settings are written as a ``{\anN}`` tag, see `_position_tag`.

    :param f: file or file-like object
    :param captions: Iterable of `Caption` objects
    :param styles: Iterable of `Style` objects to keep the formatting of
        the cue text, or None to write the text without cue tags
    """
    colours = None if styles is None else _cue_colours(styles)
    output = []
    index = 0
    for caption in captions:
        # the text without cue tags, so tags with no text are left out also
        # when keeping the formatting
        if not caption.text.strip():
            continue
        text = (caption.text if colours is None
                else _format_cue_text(caption.raw_text, colours))
        lines = [line for line in text.split('\n') if line.strip()]
        # a text with a position tag, as written by earlier versions, keeps
        # it
        if not _POSITION_TAG.search(text):
            lines[0] = _position_tag(caption.settings) + lines[0]
        index += 1
        output.extend([
            f'{index}',
            '{} --> {}'.format(*map(lambda x: x.replace('.', ','),
                                    (caption.start, caption.end))
                               ),
            *lines,
            ''
            ])
    f.write('\n'.join(output))
