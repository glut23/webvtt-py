"""SRT format module."""

import typing
import re

from .models import Caption, Timestamp
from .errors import MalformedFileError
from . import utils


TIMESTAMP = r'\d+:\d{1,2}:\d{1,2}[,.]\d+'


class SRTCueBlock:
    """Representation of a cue timing block."""

    CUE_TIMINGS_PATTERN = re.compile(
        rf'\s*({TIMESTAMP})\s*-->\s*({TIMESTAMP})'
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


def is_cue_start(lines: typing.Sequence[str]) -> bool:
    """
    Validate if the lines start with a cue index or cue timings.

    :param lines: the lines to be validated
    :returns: true if the lines start a cue
    """
    return lines[0].strip().isdigit() or '-->' in lines[0]


def iter_cue_blocks(
        lines: typing.Sequence[str]
        ) -> typing.Generator[typing.List[str], None, None]:
    """
    Iterate blocks of text, also splitting a block where a cue starts.

    A cue starts at a cue index followed by the cue timings, even without
    an empty line before it.

    :param lines: lines of text
    """
    for block_lines in utils.iter_blocks_of_lines(lines):
        start = 0
        for i in range(1, len(block_lines) - 1):
            if (block_lines[i].strip().isdigit() and
                    '-->' in block_lines[i + 1]):
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

    for block_lines in iter_cue_blocks(lines):
        if is_cue_start(block_lines):
            caption = None
            if SRTCueBlock.is_valid(block_lines):
                cue_block = SRTCueBlock.from_lines(block_lines)
                try:
                    start, end = map(parse_timestamp,
                                     (cue_block.start, cue_block.end))
                except ValueError:
                    continue
                caption = Caption(str(start), str(end), cue_block.payload)
                captions.append(caption)
        elif caption is not None:
            caption.lines.extend(block_lines)

    return [caption for caption in captions if caption.lines]


def parse_timestamp(value: str) -> Timestamp:
    """
    Return a `Timestamp` from a SRT timestamp.

    As in most SRT readers, the separator before the milliseconds can be a
    comma or a dot, the milliseconds are read as a number, so ``07,5`` is 5
    milliseconds, and fields over their range carry over, so ``07,1500``
    is 8.5 seconds.

    :param value: the timestamp in ``hh:mm:ss,mmm`` format
    :returns: a `Timestamp` instance

    :raises ValueError: if a field has too many digits to be read
    """
    hours, minutes, seconds, milliseconds = map(
        int, re.split('[:,.]', value)
        )
    return Timestamp._from_milliseconds(
        ((hours * 60 + minutes) * 60 + seconds) * 1000 + milliseconds
        )


def write(
        f: typing.IO[str],
        captions: typing.Iterable[Caption]
        ):
    """
    Write captions to an output.

    :param f: file or file-like object
    :param captions: Iterable of `Caption` objects
    """
    output = []
    for index, caption in enumerate(captions, start=1):
        output.extend([
            f'{index}',
            '{} --> {}'.format(*map(lambda x: x.replace('.', ','),
                                    (caption.start, caption.end))
                               ),
            *(line for line in caption.text.split('\n') if line.strip()),
            ''
            ])
    f.write('\n'.join(output).rstrip())
