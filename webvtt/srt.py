"""SRT format module."""

import typing
import re

from .models import Caption
from .errors import MalformedFileError
from . import utils


class SRTCueBlock:
    """Representation of a cue timing block."""

    CUE_TIMINGS_PATTERN = re.compile(
        r'\s*(\d+:\d{2}:\d{2},\d{3})\s*-->\s*(\d+:\d{2}:\d{2},\d{3})'
        )

    def __init__(
            self,
            index: str,
            start: str,
            end: str,
            payload: typing.List[str]
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
          lines[0].isdigit() and
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

        payload = list(lines[2:])

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


def parse_captions(lines: typing.Sequence[str]) -> typing.List[Caption]:
    """
    Parse captions from the text.

    Blocks of text that do not start with a cue index are taken as part
    of the text of the previous cue, as some files have empty lines in
    the caption text.

    :param lines: lines of text
    :returns: list of `Caption` objects
    """
    cue_blocks: typing.List[SRTCueBlock] = []
    cue_block: typing.Optional[SRTCueBlock] = None

    for block_lines in utils.iter_blocks_of_lines(lines):
        if block_lines[0].isdigit():
            cue_block = None
            if SRTCueBlock.is_valid(block_lines):
                cue_block = SRTCueBlock.from_lines(block_lines)
                cue_blocks.append(cue_block)
        elif cue_block:
            cue_block.payload.extend(block_lines)

    captions: typing.List[Caption] = []

    for cue_block in cue_blocks:
        if not cue_block.payload:
            continue

        cue_block.start, cue_block.end = map(
            lambda x: x.replace(',', '.'), (cue_block.start, cue_block.end))

        captions.append(Caption(cue_block.start,
                                cue_block.end,
                                cue_block.payload
                                ))

    return captions


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
