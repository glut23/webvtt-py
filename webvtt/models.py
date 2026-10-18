"""Models module."""

import datetime
import math
import re
import typing

from .errors import MalformedCaptionError


class Timestamp:
    """Representation of a timestamp."""

    PATTERN = re.compile(r'(?:(\d{1,}):)?(\d{1,2}):(\d{1,2})\.(\d{1,3})')

    def __init__(
            self,
            hours: int = 0,
            minutes: int = 0,
            seconds: int = 0,
            milliseconds: int = 0
            ):
        """Initialize."""
        self.hours = hours
        self.minutes = minutes
        self.seconds = seconds
        self.milliseconds = milliseconds

    def __str__(self):
        """Return the string representation of the timestamp."""
        return (
            f'{self.hours:02d}:{self.minutes:02d}:{self.seconds:02d}'
            f'.{self.milliseconds:03d}'
            )

    def to_tuple(self) -> typing.Tuple[int, int, int, int]:
        """Return the timestamp in tuple form."""
        return self.hours, self.minutes, self.seconds, self.milliseconds

    def __repr__(self):
        """Return the string representation of the caption."""
        return (f'<{self.__class__.__name__} '
                f'hours={self.hours} '
                f'minutes={self.minutes} '
                f'seconds={self.seconds} '
                f'milliseconds={self.milliseconds}>'
                )

    def __eq__(self, other):
        """Compare equality with other object."""
        return self.to_tuple() == other.to_tuple()

    def __ne__(self, other):
        """Compare a not equality with other object."""
        return self.to_tuple() != other.to_tuple()

    def __gt__(self, other):
        """Compare greater than with other object."""
        return self.to_tuple() > other.to_tuple()

    def __lt__(self, other):
        """Compare less than with other object."""
        return self.to_tuple() < other.to_tuple()

    def __ge__(self, other):
        """Compare greater or equal with other object."""
        return self.to_tuple() >= other.to_tuple()

    def __le__(self, other):
        """Compare less or equal with other object."""
        return self.to_tuple() <= other.to_tuple()

    @classmethod
    def from_string(cls, value: str) -> 'Timestamp':
        """
        Return a `Timestamp` instance from a string value.

        The fields can be shorter than the WebVTT format requires, as in
        ``0:1:5.2``, and the fraction of a second is padded on the right so
        ``.2`` is read as 200 milliseconds.

        :param value: the timestamp in ``[hh:]mm:ss.mmm`` format
        :returns: a `Timestamp` instance

        :raises MalformedCaptionError: if the timestamp is not valid
        """
        if type(value) is not str:
            raise MalformedCaptionError(f'Invalid timestamp {value!r}')

        match = cls.PATTERN.fullmatch(value)
        if not match:
            raise MalformedCaptionError(f'Invalid timestamp {value!r}')

        hours = int(match.group(1) or 0)
        minutes = int(match.group(2))
        seconds = int(match.group(3))
        milliseconds = int(match.group(4).ljust(3, '0'))

        if minutes > 59 or seconds > 59:
            raise MalformedCaptionError(f'Invalid timestamp {value!r}')

        return cls(hours, minutes, seconds, milliseconds)

    @classmethod
    def from_seconds(cls, value: float) -> 'Timestamp':
        """
        Return a `Timestamp` instance from a number of seconds.

        The value is rounded to the nearest millisecond, so ``1.9996`` is
        read as ``00:00:02.000``.

        :param value: the timestamp in seconds
        :returns: a `Timestamp` instance

        :raises MalformedCaptionError: if the value is not a finite number
            of seconds greater than or equal to zero
        """
        if (
                type(value) is bool or
                not isinstance(value, (int, float)) or
                not math.isfinite(value) or
                value < 0
                ):
            raise MalformedCaptionError(f'Invalid timestamp {value!r}')

        hours, remainder = divmod(round(value * 1000), 3_600_000)
        minutes, remainder = divmod(remainder, 60_000)
        seconds, milliseconds = divmod(remainder, 1000)

        return cls(hours, minutes, seconds, milliseconds)

    def in_seconds(self) -> int:
        """
        Return the timestamp in seconds.

        The milliseconds are left out, use `in_milliseconds` for the exact
        value.
        """
        return (self.hours * 3600 +
                self.minutes * 60 +
                self.seconds
                )

    def in_milliseconds(self) -> int:
        """Return the timestamp in milliseconds."""
        return self.in_seconds() * 1000 + self.milliseconds

    def _shifted(self, offset_ms: int) -> 'Timestamp':
        """
        Return a new `Timestamp` moved by a number of milliseconds.

        A result before zero is clamped to ``00:00:00.000``.

        :param offset_ms: the milliseconds to move the timestamp by
        :returns: a `Timestamp` instance
        """
        return self.from_seconds(
            max(self.in_milliseconds() + offset_ms, 0) / 1000
            )


def _offset_in_milliseconds(
        offset: typing.Union[float, datetime.timedelta]
        ) -> int:
    """
    Return a shift offset in milliseconds.

    :param offset: a number of seconds or a ``timedelta``
    :returns: the offset rounded to the nearest millisecond

    :raises TypeError: if the offset is not a number or a ``timedelta``
    :raises ValueError: if the offset is not finite
    """
    if isinstance(offset, datetime.timedelta):
        return round(offset.total_seconds() * 1000)

    if type(offset) is bool or not isinstance(offset, (int, float)):
        raise TypeError(f'Invalid offset {offset!r}')

    if not math.isfinite(offset):
        raise ValueError(f'Invalid offset {offset!r}')

    return round(offset * 1000)


def _strip_cue_text_tags(line: str) -> str:
    """
    Remove cue tags from a single line of text.

    Gives the same result as ``re.sub('<.*?>', '', line)`` for a line
    without a newline, in linear time. That regex rescans the rest of the
    line from every ``<`` that has no ``>`` after it, which is quadratic in
    the length of the line; once one ``<`` has no closing ``>``, no later
    ``<`` on the line has one either, so the scan can stop there.
    """
    parts = []
    pos = 0
    while True:
        start = line.find('<', pos)
        if start < 0:
            break
        end = line.find('>', start + 1)
        if end < 0:
            break
        parts.append(line[pos:start])
        pos = end + 1
    parts.append(line[pos:])
    return ''.join(parts)


class Caption:
    """Representation of a caption."""

    CUE_TEXT_TAGS = re.compile('<.*?>')
    VOICE_SPAN_PATTERN = re.compile(r'<v(?:\.\w+)*\s+([^>]+)>')

    def __init__(self,
                 start: typing.Optional[str] = None,
                 end: typing.Optional[str] = None,
                 text: typing.Optional[typing.Union[str,
                                                    typing.Sequence[str]
                                                    ]] = None,
                 identifier: typing.Optional[str] = None
                 ):
        """
        Initialize.

        :param start: start time of the caption
        :param end: end time of the caption
        :param text: the text of the caption
        :param identifier: optional identifier

        :raises MalformedCaptionError: if start or end are not valid
        """
        text = text or []
        self.start = start or '00:00:00.000'
        self.end = end or '00:00:00.000'
        self.identifier = identifier
        self.lines = (text.splitlines()
                      if isinstance(text, str)
                      else
                      list(text)
                      )
        self.comments: typing.List[str] = []

    def __repr__(self):
        """Return the string representation of the caption."""
        cleaned_text = self.text.replace('\n', '\\n')
        return (f'<{self.__class__.__name__} '
                f'start={self.start!r} '
                f'end={self.end!r} '
                f'text={cleaned_text!r} '
                f'identifier={self.identifier!r}>'
                )

    def __str__(self):
        """Return a readable representation of the caption."""
        cleaned_text = self.text.replace('\n', '\\n')
        return f'{self.start} {self.end} {cleaned_text}'

    def __eq__(self, other):
        """Compare equality with another object."""
        if not isinstance(other, type(self)):
            return False

        return (self.start == other.start and
                self.end == other.end and
                self.raw_text == other.raw_text and
                self.identifier == other.identifier
                )

    @property
    def start(self):
        """Return the start time of the caption."""
        return str(self.start_time)

    @start.setter
    def start(self, value: str):
        """Set the start time of the caption."""
        self.start_time = Timestamp.from_string(value)

    @property
    def end(self):
        """Return the end time of the caption."""
        return str(self.end_time)

    @end.setter
    def end(self, value: str):
        """Set the end time of the caption."""
        self.end_time = Timestamp.from_string(value)

    @property
    def start_in_seconds(self) -> int:
        """Return the start time of the caption in seconds."""
        return self.start_time.in_seconds()

    @property
    def end_in_seconds(self):
        """Return the end time of the caption in seconds."""
        return self.end_time.in_seconds()

    def shift(self, offset: typing.Union[float, datetime.timedelta]):
        """
        Shift the start and end time of the caption.

        The offset is rounded to the nearest millisecond and a timestamp
        that would fall before zero is set to ``00:00:00.000``.

        :param offset: a number of seconds or a ``timedelta``, negative
            values move the caption earlier

        :raises TypeError: if the offset is not a number or a ``timedelta``
        :raises ValueError: if the offset is not finite
        """
        offset_ms = _offset_in_milliseconds(offset)
        self.start_time = self.start_time._shifted(offset_ms)
        self.end_time = self.end_time._shifted(offset_ms)

    @property
    def raw_text(self) -> str:
        """Return the text of the caption (including cue tags)."""
        return '\n'.join(self.lines)

    @property
    def text(self) -> str:
        """Return the text of the caption (without cue tags)."""
        return '\n'.join(
            _strip_cue_text_tags(line)
            for line in self.raw_text.split('\n')
        )

    @text.setter
    def text(self, value: str):
        """Set the text of the captions."""
        if not isinstance(value, str):
            raise AttributeError(
                f'String value expected but received {value}.'
                )

        self.lines = value.splitlines()

    @property
    def voice(self) -> typing.Optional[str]:
        """Return the voice span if present."""
        if self.lines and self.lines[0].startswith('<v'):
            match = re.match(self.VOICE_SPAN_PATTERN, self.lines[0])
            if match:
                return match.group(1)

        return None


class Style:
    """Representation of a style."""

    def __init__(self, text: typing.Union[str, typing.List[str]]):
        """Initialize.

        :param: text: the style text
        """
        self.lines = text.splitlines() if isinstance(text, str) else text
        self.comments: typing.List[str] = []

    @property
    def text(self):
        """Return the text of the style."""
        return '\n'.join(self.lines)
