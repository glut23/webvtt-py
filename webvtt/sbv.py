"""SBV format module."""

import typing
import re

from . import utils
from .models import Caption, _caption_from_timings
from .errors import MalformedFileError


class SBVCueBlock:
    """Representation of a cue timing block."""

    CUE_TIMINGS_PATTERN = re.compile(
        r'\s*(\d+:\d{1,2}:\d{1,2}\.\d{3}),(\d+:\d{1,2}:\d{1,2}\.\d{3})'
        )

    def __init__(
            self,
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
          re.match(cls.CUE_TIMINGS_PATTERN, lines[0]) and
          lines[1].strip()
          )

    @classmethod
    def from_lines(
            cls,
            lines: typing.Sequence[str]
            ) -> 'SBVCueBlock':
        """
        Create a `SBVCueBlock` from lines of text.

        :param lines: the lines of text
        :returns: `SBVCueBlock` instance
        """
        match = re.match(cls.CUE_TIMINGS_PATTERN, lines[0])
        assert match is not None

        payload = lines[1:]

        return cls(match.group(1), match.group(2), payload)


def parse(lines: typing.Sequence[str]) -> typing.List[Caption]:
    """
    Parse SBV captions from lines of text.

    :param lines: lines of text
    :returns: list of `Caption` objects

    :raises MalformedFileError: if the content is not in SBV format
    """
    if not _is_valid_content(lines):
        raise MalformedFileError('Invalid format')

    return _parse_captions(lines)


def _is_valid_content(lines: typing.Sequence[str]) -> bool:
    """
    Validate lines of text for valid SBV content.

    :param lines: lines of text
    :returns: true for a valid SBV content
    """
    if len(lines) < 2:
        return False

    first_block = next(utils.iter_blocks_of_lines(lines))
    return bool(first_block and SBVCueBlock.is_valid(first_block))


def _parse_captions(lines: typing.Sequence[str]) -> typing.List[Caption]:
    """
    Parse captions from the text.

    The cue timings are read as in SRT, so a field over its range carries
    over, as in ``0:61:00.000``.

    :param lines: lines of text
    :returns: list of `Caption` objects
    """
    captions = []

    for block_lines in utils.iter_blocks_of_lines(lines):
        if not SBVCueBlock.is_valid(block_lines):
            continue

        cue_block = SBVCueBlock.from_lines(block_lines)
        caption = _caption_from_timings(cue_block.start,
                                        cue_block.end,
                                        cue_block.payload
                                        )
        if caption is not None:
            captions.append(caption)

    return captions
