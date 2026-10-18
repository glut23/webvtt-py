"""Models module."""

import bisect
import datetime
import decimal
import fractions
import math
import re
import typing

from .errors import MalformedCaptionError

# a context of our own, so rounding does not depend on the decimal context
# of the caller
_DECIMAL_CONTEXT = decimal.Context()


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

        The value is rounded to the nearest millisecond as written, with
        halves rounded up, so ``1.9996`` and ``1.9995`` are read as
        ``00:00:02.000``.

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

        return cls._from_milliseconds(_in_milliseconds(value))

    @classmethod
    def _from_milliseconds(cls, value: int) -> 'Timestamp':
        """
        Return a `Timestamp` instance from a number of milliseconds.

        :param value: the timestamp in milliseconds, zero or greater
        :returns: a `Timestamp` instance
        """
        hours, remainder = divmod(value, 3_600_000)
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


def _in_milliseconds(value: typing.Union[float, datetime.timedelta]) -> int:
    """
    Return a number of seconds or a ``timedelta`` in milliseconds.

    The value is rounded to the nearest millisecond with halves rounded away
    from zero. A float is rounded as written, from its shortest
    representation, so ``259.0395`` is 259040 milliseconds although the
    closest float is slightly smaller.

    :param value: a finite number of seconds or a ``timedelta``
    :returns: the value in milliseconds
    """
    if isinstance(value, datetime.timedelta):
        seconds = decimal.Decimal(
            value // datetime.timedelta(microseconds=1)
            ).scaleb(-6, context=_DECIMAL_CONTEXT)
    elif isinstance(value, float):
        seconds = decimal.Decimal(float.__repr__(value))
    else:
        seconds = decimal.Decimal(value)

    return int(
        seconds.scaleb(3, context=_DECIMAL_CONTEXT).to_integral_value(
            rounding=decimal.ROUND_HALF_UP,
            context=_DECIMAL_CONTEXT
            )
        )


def _offset_in_milliseconds(
        offset: typing.Union[float, datetime.timedelta],
        name: str = 'offset'
        ) -> int:
    """
    Return a shift offset in milliseconds.

    :param offset: a number of seconds or a ``timedelta``
    :param name: what the value is, for the error messages
    :returns: the offset rounded to the nearest millisecond, halves away
        from zero

    :raises TypeError: if the offset is not a number or a ``timedelta``
    :raises ValueError: if the offset is not finite
    """
    if isinstance(offset, datetime.timedelta):
        return _in_milliseconds(offset)

    if type(offset) is bool or not isinstance(offset, (int, float)):
        raise TypeError(f'Invalid {name} {offset!r}')

    if not math.isfinite(offset):
        raise ValueError(f'Invalid {name} {offset!r}')

    return _in_milliseconds(offset)


_Position = typing.Union[str, Timestamp, float, datetime.timedelta]


def _position_in_milliseconds(value: _Position) -> int:
    """
    Return a position in the captions in milliseconds.

    :param value: a timestamp, as a string or a `Timestamp`, a number of
        seconds or a ``timedelta``
    :returns: the position rounded to the nearest millisecond, halves away
        from zero

    :raises MalformedCaptionError: if the timestamp string is not valid
    :raises TypeError: if the value is not of a supported type
    :raises ValueError: if the value is not finite or is before zero
    """
    if isinstance(value, str):
        return Timestamp.from_string(value).in_milliseconds()

    if isinstance(value, Timestamp):
        return value.in_milliseconds()

    milliseconds = _offset_in_milliseconds(value, name='timestamp')
    if milliseconds < 0:
        raise ValueError(f'Invalid timestamp {value!r}')

    return milliseconds


def _divide_rounded(numerator: int, denominator: int) -> int:
    """
    Divide two integers rounding to the nearest integer, halves away from zero.

    :param numerator: the dividend
    :param denominator: the divisor, greater than zero
    :returns: the rounded quotient
    """
    quotient, remainder = divmod(abs(numerator), denominator)
    quotient += 2 * remainder >= denominator
    return quotient if numerator >= 0 else -quotient


def _sync_mapping(
        points: typing.Sequence[typing.Sequence[_Position]]
        ) -> typing.Callable[[int], int]:
    """
    Return the function mapping times in milliseconds for sync points.

    Times are mapped along the line between the two neighbouring points,
    and before the first or after the last point along the line of the
    outermost points.

    :param points: two or more ``(from, to)`` pairs
    :returns: the mapping of milliseconds to milliseconds

    :raises MalformedCaptionError: if a timestamp string is not valid
    :raises TypeError: if a point is not a pair of supported values
    :raises ValueError: if there are fewer than two points, two points have
        the same ``from`` time, or the points would change the order of the
        captions
    """
    if len(points) < 2:
        raise ValueError('At least two sync points are required')

    pairs = sorted(_sync_point(point) for point in points)
    for (from_1, to_1), (from_2, to_2) in zip(pairs, pairs[1:]):
        if from_1 == from_2:
            raise ValueError(
                'Two sync points have the same time '
                f'{Timestamp._from_milliseconds(from_1)}'
                )
        if to_1 >= to_2:
            raise ValueError(
                'Sync points must keep the order of the captions, '
                f'{Timestamp._from_milliseconds(from_1)} is moved to '
                f'{Timestamp._from_milliseconds(to_1)} but '
                f'{Timestamp._from_milliseconds(from_2)} to '
                f'{Timestamp._from_milliseconds(to_2)}'
                )

    from_times = [from_time for from_time, _ in pairs]

    def mapping(milliseconds: int) -> int:
        index = bisect.bisect_right(from_times, milliseconds) - 1
        index = min(max(index, 0), len(pairs) - 2)
        (from_1, to_1), (from_2, to_2) = pairs[index], pairs[index + 1]
        return to_1 + _divide_rounded(
            (milliseconds - from_1) * (to_2 - to_1),
            from_2 - from_1
            )

    return mapping


def _sync_point(point: typing.Sequence[_Position]) -> typing.Tuple[int, int]:
    """
    Return a ``(from, to)`` sync point in milliseconds.

    :param point: a pair of positions
    :returns: the pair in milliseconds

    :raises TypeError: if the point is not a pair
    """
    if not isinstance(point, (tuple, list)) or len(point) != 2:
        raise TypeError(f'Invalid sync point {point!r}')

    return (_position_in_milliseconds(point[0]),
            _position_in_milliseconds(point[1]))


def _framerate_mapping(
        from_fps: float,
        to_fps: float
        ) -> typing.Callable[[int], int]:
    """
    Return the function mapping times in milliseconds between frame rates.

    :param from_fps: the frame rate the captions are timed for
    :param to_fps: the frame rate of the video
    :returns: the mapping of milliseconds to milliseconds

    :raises TypeError: if a frame rate is not a number
    :raises ValueError: if a frame rate is not finite or not above zero
    """
    ratio = _frame_rate(from_fps) / _frame_rate(to_fps)
    return lambda milliseconds: _divide_rounded(
        milliseconds * ratio.numerator,
        ratio.denominator
        )


def _frame_rate(value: float) -> fractions.Fraction:
    """
    Return a frame rate as an exact fraction, as written.

    :param value: the frame rate, e.g. ``25`` or ``23.976``
    :returns: the frame rate as a fraction

    :raises TypeError: if the frame rate is not a number
    :raises ValueError: if the frame rate is not finite or not above zero
    """
    if type(value) is bool or not isinstance(value, (int, float)):
        raise TypeError(f'Invalid frame rate {value!r}')

    if not math.isfinite(value) or value <= 0:
        raise ValueError(f'Invalid frame rate {value!r}')

    if isinstance(value, float):
        return fractions.Fraction(decimal.Decimal(float.__repr__(value)))

    return fractions.Fraction(value)


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

        The offset is rounded to the nearest millisecond, halves away from
        zero, and a timestamp that would fall before zero is set to
        ``00:00:00.000``.

        :param offset: a number of seconds or a ``timedelta``, negative
            values move the caption earlier

        :raises TypeError: if the offset is not a number or a ``timedelta``
        :raises ValueError: if the offset is not finite
        """
        offset_ms = _offset_in_milliseconds(offset)
        self._retime(lambda milliseconds: milliseconds + offset_ms)

    def _retime(self, mapping: typing.Callable[[int], int]):
        """
        Change the start and end time of the caption with a mapping.

        A time mapped before zero is set to ``00:00:00.000``.

        :param mapping: the function mapping a time in milliseconds to the
            new time in milliseconds
        """
        self.start_time = Timestamp._from_milliseconds(
            max(mapping(self.start_time.in_milliseconds()), 0)
            )
        self.end_time = Timestamp._from_milliseconds(
            max(mapping(self.end_time.in_milliseconds()), 0)
            )

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
