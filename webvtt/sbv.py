"""SBV format module."""

import typing
import re
from collections.abc import Iterable, Sequence

from . import utils
from .models import (
    Caption, ParseIssue, Timestamp, _caption_from_timings, _skipped_block
    )
from .errors import MalformedFileError


class SBVCueBlock:
    """Representation of a cue timing block."""

    CUE_TIMINGS_PATTERN = re.compile(
        r'\s*([0-9]+:[0-9]{1,2}:[0-9]{1,2}\.[0-9]{3}),'
        r'([0-9]+:[0-9]{1,2}:[0-9]{1,2}\.[0-9]{3})'
        )

    def __init__(
            self,
            start: str,
            end: str,
            payload: Sequence[str]
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
            lines: Sequence[str]
            ) -> bool:
        """
        Validate the lines for a match of a cue time block.

        :param lines: the lines to be validated
        :returns: true for a matching cue time block
        """
        return bool(
          len(lines) >= 2 and
          cls.CUE_TIMINGS_PATTERN.match(lines[0]) and
          utils._has_cue_text(lines[1])
          )

    @classmethod
    def from_lines(
            cls,
            lines: Sequence[str]
            ) -> 'SBVCueBlock':
        """
        Create a `SBVCueBlock` from lines of text.

        :param lines: the lines of text
        :returns: `SBVCueBlock` instance
        """
        match = cls.CUE_TIMINGS_PATTERN.match(lines[0])
        assert match is not None

        payload = lines[1:]

        return cls(match.group(1), match.group(2), payload)


def parse(
        lines: Sequence[str],
        issues: list[ParseIssue] | None = None
        ) -> list[Caption]:
    """
    Parse SBV captions from lines of text.

    :param lines: lines of text
    :param issues: a list to add the blocks that are skipped to
    :returns: list of `Caption` objects

    :raises MalformedFileError: if the content is not in SBV format
    """
    if not _is_valid_content(lines):
        raise MalformedFileError('Invalid format')

    return _parse_captions(lines, [] if issues is None else issues)


def _is_valid_content(lines: Sequence[str]) -> bool:
    """
    Validate lines of text for valid SBV content.

    The content is valid when it starts with the cue timings, after any
    blank lines. The first cue can have no text.

    :param lines: lines of text
    :returns: true for a valid SBV content
    """
    first_block = next(utils.iter_blocks_of_lines(lines), None)
    return bool(
        first_block and
        SBVCueBlock.CUE_TIMINGS_PATTERN.match(first_block[0])
        )


def _parse_captions(
        lines: Sequence[str],
        issues: list[ParseIssue]
        ) -> list[Caption]:
    """
    Parse captions from the text.

    The cue timings are read as in SRT, so a field over its range carries
    over, as in ``0:61:00.000``.

    :param lines: lines of text
    :param issues: a list to add the blocks that are skipped to
    :returns: list of `Caption` objects
    """
    captions = []

    for number, block_lines in utils._iter_numbered_blocks(lines):
        caption = _parse_cue(block_lines)
        if caption is None:
            kind = _skipped_block_kind(block_lines)
            issues.append(_skipped_block(number, kind, block_lines))
        else:
            captions.append(caption)

    return captions


def _parse_cue(lines: Sequence[str]) -> Caption | None:
    """
    Parse a cue from the lines of a block.

    :param lines: the lines of the block
    :returns: a `Caption`, or None if the block is not a valid cue
    """
    if not SBVCueBlock.is_valid(lines):
        return None

    cue_block = SBVCueBlock.from_lines(lines)
    # SBV payloads are plain text, including text that looks like a tag.
    payload = [line.replace('&', '&amp;').replace('<', '&lt;')
               for line in cue_block.payload]
    return _caption_from_timings(cue_block.start, cue_block.end, payload)


def _skipped_block_kind(lines: Sequence[str]) -> str:
    """
    Return the description of a block that is not a valid cue.

    :param lines: the lines of the block
    :returns: the description of what is wrong with the block
    """
    if not SBVCueBlock.CUE_TIMINGS_PATTERN.match(lines[0]):
        return 'Invalid block'
    return 'Invalid cue block' if len(lines) > 1 else 'Cue without text'


def write(f: typing.IO[str], captions: Iterable[Caption]) -> None:
    """
    Write captions to an output in SBV format.

    The cue tags are removed, as SBV has no formatting, and captions
    without text, such as text of blank lines or only of cue tags, are left
    out, as a cue without text cannot be read back from SBV. The blank
    lines of the text are removed, as a blank line ends the cue.

    :param f: file or file-like object
    :param captions: Iterable of `Caption` objects
    """
    output = []
    for caption in captions:
        text = caption.text
        if not utils._has_cue_text(text):
            continue
        output.extend([
            f'{_timestamp(caption.start_time)},'
            f'{_timestamp(caption.end_time)}',
            *(line for line in text.split('\n') if utils._has_cue_text(line)),
            ''
            ])
    f.write('\n'.join(output))


def _timestamp(timestamp: Timestamp) -> str:
    """
    Return a timestamp as it is written in SBV, as in ``0:01:02.500``.

    :param timestamp: the timestamp
    :returns: the timestamp with the hours not padded
    """
    return (f'{timestamp.hours}:{timestamp.minutes:02d}:'
            f'{timestamp.seconds:02d}.{timestamp.milliseconds:03d}')
