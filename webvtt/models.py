"""Models module."""

import bisect
import datetime
import decimal
import fractions
import math
import re
import typing

from .errors import MalformedCaptionError
from .utils import split_lines

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
        return _divide_rounded(
            to_1 * (from_2 - from_1) + (milliseconds - from_1) * (to_2 - to_1),
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


_FrameRate = typing.Union[float, fractions.Fraction]


def _framerate_mapping(
        from_fps: _FrameRate,
        to_fps: _FrameRate
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


def _frame_rate(value: _FrameRate) -> fractions.Fraction:
    """
    Return a frame rate as an exact fraction, as written.

    :param value: the frame rate, e.g. ``25``, ``23.976`` or
        ``Fraction(24000, 1001)``
    :returns: the frame rate as a fraction

    :raises TypeError: if the frame rate is not a number
    :raises ValueError: if the frame rate is not finite or not above zero
    """
    if (
            type(value) is bool or
            not isinstance(value, (int, float, fractions.Fraction))
            ):
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


# the characters WebVTT treats as spaces when splitting the cue settings
_CUE_SETTINGS_SEPARATOR = re.compile('[ \t\n\f\r]+')
_PERCENTAGE = re.compile(r'[0-9]+(?:\.[0-9]+)?%')
_LINE_NUMBER = re.compile(r'-?[0-9]+')


def _is_percentage(value: str) -> bool:
    """Return whether the value is a WebVTT percentage from 0 to 100."""
    return bool(_PERCENTAGE.fullmatch(value)) and float(value[:-1]) <= 100


def _is_valid_line(value: str) -> bool:
    """Return whether the value is valid for the line cue setting."""
    line, separator, alignment = value.partition(',')
    return (
        (_is_percentage(line) or bool(_LINE_NUMBER.fullmatch(line))) and
        (not separator or alignment in ('start', 'center', 'end'))
        )


def _is_valid_position(value: str) -> bool:
    """Return whether the value is valid for the position cue setting."""
    position, separator, alignment = value.partition(',')
    return (
        _is_percentage(position) and
        (not separator or
         alignment in ('line-left', 'center', 'line-right'))
        )


def _is_valid_region(value: str) -> bool:
    """Return whether the value is a valid region identifier."""
    return (
        bool(value) and
        '-->' not in value and
        not _CUE_SETTINGS_SEPARATOR.search(value)
        )


def _split_cue_setting(
        setting: str
        ) -> typing.Optional[typing.Tuple[str, str]]:
    """
    Split a cue setting in name and value at its first colon.

    :param setting: a cue setting as written in a cue timings line
    :returns: the name and value, or None when there is no colon or it is
        the first or last character
    """
    name, _, value = setting.partition(':')
    if not name or not value:
        return None
    return name, value


def _cue_setting_property(name: str, doc: str) -> property:
    """Return a property to get and set the cue setting with that name."""
    return property(
        lambda self: self._get(name),
        lambda self, value: self._set(name, value),
        doc=doc
        )


class CueSettings:
    """
    Representation of the cue settings of a caption.

    The settings are kept as written and in their original order, so they
    are written back the same, including those that are not valid or not
    known. A property returns the value of its setting when it is valid,
    the last valid one when it is repeated, and validates a new value.
    """

    VALIDATORS: typing.Dict[str, typing.Callable[[str], bool]] = {
        'vertical': lambda value: value in ('rl', 'lr'),
        'line': _is_valid_line,
        'position': _is_valid_position,
        'size': _is_percentage,
        'align': lambda value: value in (
            'start', 'center', 'end', 'left', 'right'
            ),
        'region': _is_valid_region,
        }

    def __init__(self,
                 *,
                 vertical: typing.Optional[str] = None,
                 line: typing.Optional[str] = None,
                 position: typing.Optional[str] = None,
                 size: typing.Optional[str] = None,
                 align: typing.Optional[str] = None,
                 region: typing.Optional[str] = None
                 ):
        """
        Initialize.

        :param vertical: writing direction, ``rl`` or ``lr``
        :param line: line position, as a line number or a percentage with
            an optional alignment, e.g. ``-1`` or ``10%,end``
        :param position: position as a percentage with an optional
            alignment, e.g. ``50%,line-left``
        :param size: size as a percentage, e.g. ``80%``
        :param align: text alignment, ``start``, ``center``, ``end``,
            ``left`` or ``right``
        :param region: identifier of a region

        :raises MalformedCaptionError: if a value is not valid
        """
        self._settings: typing.List[str] = []
        self.vertical = vertical
        self.line = line
        self.position = position
        self.size = size
        self.align = align
        self.region = region

    @classmethod
    def from_string(cls, value: str, strict: bool = False) -> 'CueSettings':
        """
        Return a `CueSettings` instance from the settings of a cue.

        :param value: the cue settings, e.g. ``line:0 align:start``
        :param strict: raise an error on settings that are not known, not
            valid or repeated instead of keeping them
        :returns: a `CueSettings` instance

        :raises MalformedCaptionError: if the value is not a string, or if
            strict and a setting is not known, not valid or repeated
        """
        if type(value) is not str:
            raise MalformedCaptionError(f'Invalid cue settings {value!r}')

        settings = cls()
        settings._settings = [
            setting
            for setting in _CUE_SETTINGS_SEPARATOR.split(value)
            if setting
            ]

        if strict:
            names: typing.Set[str] = set()
            for setting in settings._settings:
                parts = _split_cue_setting(setting)
                if (not parts or
                        parts[0] not in cls.VALIDATORS or
                        not cls.VALIDATORS[parts[0]](parts[1])):
                    raise MalformedCaptionError(
                        f'Invalid cue setting {setting!r}'
                        )
                if parts[0] in names:
                    raise MalformedCaptionError(
                        f'Repeated cue setting {setting!r}'
                        )
                names.add(parts[0])

        return settings

    def __str__(self):
        """Return the settings as written in a cue timings line."""
        return ' '.join(self._settings)

    def __repr__(self):
        """Return the string representation of the cue settings."""
        return f'<{self.__class__.__name__} text={str(self)!r}>'

    def __bool__(self):
        """Return whether there is any setting."""
        return bool(self._settings)

    def __eq__(self, other):
        """Compare equality with another object."""
        if not isinstance(other, type(self)):
            return False

        return self._settings == other._settings

    def _get(self, name: str) -> typing.Optional[str]:
        """Return the value of the last valid setting with that name."""
        value = None
        for setting in self._settings:
            parts = _split_cue_setting(setting)
            if (parts and
                    parts[0] == name and
                    self.VALIDATORS[name](parts[1])):
                value = parts[1]
        return value

    def _set(self, name: str, value: typing.Optional[str]):
        """
        Set the setting with that name, or remove it when the value is None.

        Every setting with that name is replaced by a single one where the
        first of them was, or added at the end when there is none.

        :raises MalformedCaptionError: if the value is not valid
        """
        if value is not None and (
                type(value) is not str or
                not self.VALIDATORS[name](value)
                ):
            raise MalformedCaptionError(
                f'Invalid {name} cue setting {value!r}'
                )

        indexes = [
            index
            for index, setting in enumerate(self._settings)
            if _split_cue_setting(setting) and
            setting.partition(':')[0] == name
            ]
        for index in reversed(indexes):
            del self._settings[index]
        if value is not None:
            self._settings.insert(
                indexes[0] if indexes else len(self._settings),
                f'{name}:{value}'
                )

    vertical = _cue_setting_property(
        'vertical',
        'Writing direction, ``rl`` or ``lr``.'
        )
    line = _cue_setting_property(
        'line',
        'Line position, as a line number or a percentage with an optional '
        'alignment.'
        )
    position = _cue_setting_property(
        'position',
        'Position as a percentage with an optional alignment.'
        )
    size = _cue_setting_property('size', 'Size as a percentage.')
    align = _cue_setting_property(
        'align',
        'Text alignment, ``start``, ``center``, ``end``, ``left`` or '
        '``right``.'
        )
    region = _cue_setting_property('region', 'Identifier of a region.')


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
        self.lines = (split_lines(text)
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

        self.lines = split_lines(value)

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
        self.lines = split_lines(text) if isinstance(text, str) else text
        self.comments: typing.List[str] = []

    @property
    def text(self):
        """Return the text of the style."""
        return '\n'.join(self.lines)
