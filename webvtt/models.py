"""Models module."""

import bisect
import datetime
import decimal
import fractions
import math
import re
import typing

from .errors import MalformedCaptionError
from .utils import _split_lines

# a context of our own, so rounding does not depend on the decimal context
# of the caller
_DECIMAL_CONTEXT = decimal.Context()

# the largest timestamp, 9999999999:59:59.999, as hours have up to 10 digits,
# far more than any video lasts, so times past it are rejected the same on
# every Python version instead of converting huge numbers, which is slow
# before Python 3.11 and raises ValueError after it
_MAX_MILLISECONDS = 10 ** 10 * 3_600_000 - 1
_OUT_OF_RANGE = 'Time after the largest timestamp 9999999999:59:59.999'


class Timestamp:
    """Representation of a timestamp."""

    # hours have up to 10 digits, see _MAX_MILLISECONDS
    PATTERN = re.compile(r'(?:(\d{1,10}):)?(\d{1,2}):(\d{1,2})\.(\d{1,3})')

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
        ``.2`` is read as 200 milliseconds. The hours can have up to 10
        digits.

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
            of seconds greater than or equal to zero, or is after the
            largest timestamp
        """
        if (
                type(value) is bool or
                not isinstance(value, (int, float)) or
                not _is_finite(value) or
                value < 0
                ):
            raise MalformedCaptionError(f'Invalid timestamp {value!r}')

        try:
            return cls._from_milliseconds(_in_milliseconds(value))
        except ValueError as error:
            raise MalformedCaptionError(str(error)) from None

    @classmethod
    def _from_milliseconds(cls, value: int) -> 'Timestamp':
        """
        Return a `Timestamp` instance from a number of milliseconds.

        :param value: the timestamp in milliseconds, zero or greater
        :returns: a `Timestamp` instance

        :raises ValueError: if the value is after the largest timestamp
        """
        if value > _MAX_MILLISECONDS:
            raise ValueError(_OUT_OF_RANGE)

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


def _is_finite(value: typing.Union[float, fractions.Fraction]) -> bool:
    """
    Return whether a number is finite.

    Integers and fractions are always finite, and are not passed to
    ``math.isfinite``, which raises OverflowError for those too large to
    convert to a float.
    """
    return not isinstance(value, float) or math.isfinite(value)


def _in_milliseconds(value: typing.Union[float, datetime.timedelta]) -> int:
    """
    Return a number of seconds or a ``timedelta`` in milliseconds.

    The value is rounded to the nearest millisecond with halves rounded away
    from zero. A float is rounded as written, from its shortest
    representation, so ``259.0395`` is 259040 milliseconds although the
    closest float is slightly smaller. A number past the range of a
    timestamp, in either direction, is returned as one millisecond past it,
    as converting a huge number can overflow.

    :param value: a finite number of seconds or a ``timedelta``
    :returns: the value in milliseconds
    """
    if isinstance(value, datetime.timedelta):
        seconds = decimal.Decimal(
            value // datetime.timedelta(microseconds=1)
            ).scaleb(-6, context=_DECIMAL_CONTEXT)
    elif abs(value) >= (_MAX_MILLISECONDS + 1) // 1000:
        return _MAX_MILLISECONDS + 1 if value > 0 else -_MAX_MILLISECONDS - 1
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

    if not _is_finite(offset):
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
    :raises ValueError: if the value is not finite, is before zero or is
        after the largest timestamp
    """
    if isinstance(value, str):
        return Timestamp.from_string(value).in_milliseconds()

    if isinstance(value, Timestamp):
        return value.in_milliseconds()

    milliseconds = _offset_in_milliseconds(value, name='timestamp')
    if milliseconds < 0:
        raise ValueError(f'Invalid timestamp {value!r}')
    if milliseconds > _MAX_MILLISECONDS:
        raise ValueError(_OUT_OF_RANGE)

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

    if not _is_finite(value) or value <= 0:
        raise ValueError(f'Invalid frame rate {value!r}')

    if isinstance(value, float):
        return fractions.Fraction(decimal.Decimal(float.__repr__(value)))

    return fractions.Fraction(value)


def _iter_cue_text_tokens(
        line: str
        ) -> typing.Generator[typing.Tuple[str, bool], None, None]:
    """
    Iterate the text and the cue tags of a single line of text.

    A ``<`` without a ``>`` after it is part of the text. The scan stops at
    the first one, as no later ``<`` on the line has a ``>`` after it either,
    which keeps it linear in the length of the line.

    :param line: a line of cue text
    :returns: tuples of the text or the tag content and true for a tag
    """
    pos = 0
    while True:
        start = line.find('<', pos)
        if start < 0:
            break
        end = line.find('>', start + 1)
        if end < 0:
            break
        if start > pos:
            yield line[pos:start], False
        yield line[start + 1:end], True
        pos = end + 1
    if pos < len(line):
        yield line[pos:], False


def _strip_cue_text_tags(line: str) -> str:
    """
    Remove cue tags from a single line of text.

    Gives the same result as ``re.sub('<.*?>', '', line)`` for a line
    without a newline, in linear time. That regex rescans the rest of the
    line from every ``<`` that has no ``>`` after it, which is quadratic in
    the length of the line.
    """
    return ''.join(
        token for token, is_tag in _iter_cue_text_tokens(line) if not is_tag
        )


# the characters WebVTT treats as spaces when splitting settings
_SETTINGS_SEPARATOR = re.compile('[ \t\n\f\r]+')
_PERCENTAGE = re.compile(r'[0-9]+(?:\.[0-9]+)?%')
_LINE_NUMBER = re.compile(r'-?[0-9]+')
_NUMBER_OF_LINES = re.compile(r'[0-9]+')


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


def _is_valid_anchor(value: str) -> bool:
    """Return whether the value is two percentages separated by a comma."""
    x, separator, y = value.partition(',')
    return bool(separator) and _is_percentage(x) and _is_percentage(y)


def _is_valid_identifier(value: str) -> bool:
    """Return whether the value is a valid region identifier."""
    return (
        bool(value) and
        '-->' not in value and
        not _SETTINGS_SEPARATOR.search(value)
        )


def _split_setting(setting: str) -> typing.Optional[typing.Tuple[str, str]]:
    """
    Split a setting in name and value at its first colon.

    :param setting: a setting as written, e.g. ``line:0``
    :returns: the name and value, or None when there is no colon or it is
        the first or last character
    """
    name, _, value = setting.partition(':')
    if not name or not value:
        return None
    return name, value


def _setting_name(setting: str) -> typing.Optional[str]:
    """Return the name of a setting, or None when it has no name."""
    parts = _split_setting(setting)
    return parts[0] if parts else None


def _setting_property(name: str, doc: str) -> property:
    """Return a property to get and set the setting with that name."""
    return property(
        lambda self: self._get(name),
        lambda self, value: self._set(name, value),
        doc=doc
        )


_SettingsT = typing.TypeVar('_SettingsT', bound='_Settings')


class _Settings:
    """
    Base for settings written as ``name:value`` and separated by spaces.

    The settings are kept as written and in their original order, so they
    are written back the same, including those that are not valid or not
    known. A property returns the value of its setting when it is valid,
    the last valid one when it is repeated, and validates a new value.
    """

    VALIDATORS: typing.ClassVar[
        typing.Dict[str, typing.Callable[[str], bool]]
        ] = {}

    # what a setting is called in error messages
    _KIND = 'setting'

    def __init__(self):
        """Initialize without settings."""
        self._settings: typing.List[str] = []

    @classmethod
    def from_string(
            cls: typing.Type[_SettingsT],
            value: str,
            strict: bool = False
            ) -> _SettingsT:
        """
        Return an instance from settings separated by spaces.

        :param value: the settings, e.g. ``line:0 align:start``
        :param strict: raise an error on settings that are not known, not
            valid or repeated instead of keeping them
        :returns: an instance with the settings

        :raises MalformedCaptionError: if the value is not a string, or if
            strict and a setting is not known, not valid or repeated
        """
        if type(value) is not str:
            raise MalformedCaptionError(f'Invalid {cls._KIND}s {value!r}')

        settings = cls()
        settings._settings = [
            setting
            for setting in _SETTINGS_SEPARATOR.split(value)
            if setting
            ]

        if strict:
            names: typing.Set[str] = set()
            for setting in settings._settings:
                parts = _split_setting(setting)
                if (not parts or
                        parts[0] not in cls.VALIDATORS or
                        not cls.VALIDATORS[parts[0]](parts[1])):
                    raise MalformedCaptionError(
                        f'Invalid {cls._KIND} {setting!r}'
                        )
                if parts[0] in names:
                    raise MalformedCaptionError(
                        f'Repeated {cls._KIND} {setting!r}'
                        )
                names.add(parts[0])

        return settings

    def __str__(self):
        """Return the settings separated by a space."""
        return ' '.join(self._settings)

    def __repr__(self):
        """Return the string representation of the settings."""
        return f'<{self.__class__.__name__} text={str(self)!r}>'

    def __bool__(self):
        """Return whether there is any setting."""
        return bool(self._settings)

    def __iter__(self) -> typing.Iterator[str]:
        """Iterate the settings as written, e.g. ``line:0``."""
        return iter(self._settings)

    def __eq__(self, other):
        """Compare equality with another object."""
        if not isinstance(other, type(self)):
            return False

        return self._settings == other._settings

    def _get(self, name: str) -> typing.Optional[str]:
        """Return the value of the last valid setting with that name."""
        value = None
        for setting in self._settings:
            parts = _split_setting(setting)
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
                f'Invalid {name} {self._KIND} {value!r}'
                )

        indexes = [
            index
            for index, setting in enumerate(self._settings)
            if _setting_name(setting) == name
            ]
        for index in reversed(indexes):
            del self._settings[index]
        if value is not None:
            self._settings.insert(
                indexes[0] if indexes else len(self._settings),
                f'{name}:{value}'
                )


class CueSettings(_Settings):
    """
    Representation of the cue settings of a caption.

    The settings are kept as written and in their original order, so they
    are written back the same, including those that are not valid or not
    known. A property returns the value of its setting when it is valid,
    the last valid one when it is repeated, and validates a new value.
    """

    VALIDATORS = {
        'vertical': lambda value: value in ('rl', 'lr'),
        'line': _is_valid_line,
        'position': _is_valid_position,
        'size': _is_percentage,
        'align': lambda value: value in (
            'start', 'center', 'end', 'left', 'right'
            ),
        'region': _is_valid_identifier,
        }

    _KIND = 'cue setting'

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
        super().__init__()
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
        return super().from_string(value, strict)

    vertical = _setting_property(
        'vertical',
        'Writing direction, ``rl`` or ``lr``.'
        )
    line = _setting_property(
        'line',
        'Line position, as a line number or a percentage with an optional '
        'alignment.'
        )
    position = _setting_property(
        'position',
        'Position as a percentage with an optional alignment.'
        )
    size = _setting_property('size', 'Size as a percentage.')
    align = _setting_property(
        'align',
        'Text alignment, ``start``, ``center``, ``end``, ``left`` or '
        '``right``.'
        )
    region = _setting_property('region', 'Identifier of a region.')


def _to_cue_settings(
        value: typing.Optional[typing.Union[str, CueSettings]]
        ) -> CueSettings:
    """
    Return a new `CueSettings` instance from the value.

    :param value: the cue settings as a string, a `CueSettings` instance
        that is copied, or None for no settings
    :returns: a `CueSettings` instance

    :raises MalformedCaptionError: if the value is not a string, a
        `CueSettings` instance or None
    """
    if isinstance(value, CueSettings):
        settings = CueSettings()
        settings._settings = list(value._settings)
        return settings
    return CueSettings.from_string('' if value is None else value)


class Caption:
    """Representation of a caption."""

    CUE_TEXT_TAGS = re.compile('<.*?>')
    VOICE_SPAN_PATTERN = re.compile(r'<v(?:\.\w+)*\s+([^>\s][^>]*)>')

    def __init__(self,
                 start: typing.Optional[str] = None,
                 end: typing.Optional[str] = None,
                 text: typing.Optional[typing.Union[str,
                                                    typing.Sequence[str]
                                                    ]] = None,
                 identifier: typing.Optional[str] = None,
                 settings: typing.Optional[typing.Union[str,
                                                        CueSettings
                                                        ]] = None
                 ):
        """
        Initialize.

        :param start: start time of the caption
        :param end: end time of the caption
        :param text: the text of the caption
        :param identifier: optional identifier
        :param settings: optional cue settings, as a string such as
            ``line:0 align:start`` or a `CueSettings` instance

        :raises MalformedCaptionError: if start or end are not valid, or
            settings is not a string, a `CueSettings` instance or None
        """
        text = text or []
        self.start = start or '00:00:00.000'
        self.end = end or '00:00:00.000'
        self.identifier = identifier
        self._settings = _to_cue_settings(settings)
        self.lines = (_split_lines(text)
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
                f'identifier={self.identifier!r} '
                f'settings={str(self.settings)!r}>'
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
                self.identifier == other.identifier and
                self.settings == other.settings
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
    def settings(self) -> CueSettings:
        """Return the cue settings of the caption."""
        return self._settings

    @settings.setter
    def settings(self, value: typing.Optional[typing.Union[str, CueSettings]]):
        """
        Set the cue settings of the caption, or clear them when None.

        A `CueSettings` instance is copied, so it is not shared with the
        caption it may come from.

        :raises MalformedCaptionError: if the value is not a string, a
            `CueSettings` instance or None
        """
        self._settings = _to_cue_settings(value)

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
        :raises ValueError: if the offset is not finite, or would move a
            time after the largest timestamp, leaving the caption unchanged
        """
        offset_ms = _offset_in_milliseconds(offset)
        _retime_captions([self], lambda milliseconds: milliseconds + offset_ms)

    def _retimed(
            self,
            mapping: typing.Callable[[int], int]
            ) -> typing.Tuple[Timestamp, Timestamp]:
        """
        Return the start and end time of the caption mapped to new times.

        A time mapped before zero is set to ``00:00:00.000``.

        :param mapping: the function mapping a time in milliseconds to the
            new time in milliseconds
        :returns: the new start and end time

        :raises ValueError: if a time is mapped after the largest timestamp
        """
        return (
            Timestamp._from_milliseconds(
                max(mapping(self.start_time.in_milliseconds()), 0)
                ),
            Timestamp._from_milliseconds(
                max(mapping(self.end_time.in_milliseconds()), 0)
                )
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

        self.lines = _split_lines(value)

    @property
    def voice(self) -> typing.Optional[str]:
        """Return the voice span if present."""
        if self.lines and self.lines[0].startswith('<v'):
            match = re.match(self.VOICE_SPAN_PATTERN, self.lines[0])
            if match:
                return match.group(1)

        return None


def _retime_captions(
        captions: typing.Iterable[Caption],
        mapping: typing.Callable[[int], int]
        ):
    """
    Change the start and end time of the captions with a mapping.

    The new times of every caption are computed before any caption is
    changed, so the captions are left unchanged when one cannot be.

    :param captions: the captions to change
    :param mapping: the function mapping a time in milliseconds to the new
        time in milliseconds

    :raises ValueError: if a time is mapped after the largest timestamp
    """
    captions = list(captions)
    times = [caption._retimed(mapping) for caption in captions]
    for caption, (start_time, end_time) in zip(captions, times):
        caption.start_time, caption.end_time = start_time, end_time


def _timing_in_milliseconds(value: str) -> int:
    """
    Return the milliseconds of a SRT or SBV timestamp.

    As in most SRT readers, the separator before the milliseconds can be a
    comma or a dot, the milliseconds are read as a number, so ``07,5`` is 5
    milliseconds, and fields over their range carry over, so ``07,1500``
    is 8.5 seconds.

    :param value: the timestamp in ``hh:mm:ss,mmm`` format
    :returns: the timestamp in milliseconds

    :raises ValueError: if a field is past the range of a timestamp
    """
    fields = re.split('[:,.]', value)
    # a field with more than 17 significant digits is past the largest
    # timestamp whatever its unit, so it is rejected without converting it
    if any(len(field.lstrip('0')) > 17 for field in fields):
        raise ValueError(_OUT_OF_RANGE)

    hours, minutes, seconds, milliseconds = map(int, fields)
    return ((hours * 60 + minutes) * 60 + seconds) * 1000 + milliseconds


def _caption_from_timings(
        start: str,
        end: str,
        lines: typing.Sequence[str]
        ) -> typing.Optional[Caption]:
    """
    Return a caption from the cue timings of SRT or SBV.

    :param start: the start time in ``hh:mm:ss,mmm`` format
    :param end: the end time in ``hh:mm:ss,mmm`` format
    :param lines: the lines of the caption text
    :returns: a `Caption` instance, or None if a time cannot be read or
        is after the largest timestamp
    """
    try:
        start_time, end_time = (
            Timestamp._from_milliseconds(_timing_in_milliseconds(timing))
            for timing in (start, end)
            )
    except ValueError:
        return None

    return Caption(str(start_time), str(end_time), lines)


class Style:
    """Representation of a style."""

    def __init__(self, text: typing.Union[str, typing.List[str]]):
        """Initialize.

        :param: text: the style text
        """
        self.lines = _split_lines(text) if isinstance(text, str) else text
        self.comments: typing.List[str] = []

    @property
    def text(self):
        """Return the text of the style."""
        return '\n'.join(self.lines)


class Region(_Settings):
    """
    Representation of a region.

    A region is an area of the video where captions are rendered, defined
    in a REGION block of the header and referred to by its identifier in
    the ``region`` cue setting of the captions.

    The settings are kept as written and in their original order, so they
    are written back the same, including those that are not valid or not
    known. A property returns the value of its setting when it is valid,
    the last valid one when it is repeated, and validates a new value.
    """

    VALIDATORS = {
        'id': _is_valid_identifier,
        'width': _is_percentage,
        'lines': lambda value: bool(_NUMBER_OF_LINES.fullmatch(value)),
        'regionanchor': _is_valid_anchor,
        'viewportanchor': _is_valid_anchor,
        'scroll': lambda value: value == 'up',
        }

    _KIND = 'region setting'

    def __init__(self,
                 *,
                 id: typing.Optional[str] = None,
                 width: typing.Optional[str] = None,
                 lines: typing.Optional[str] = None,
                 regionanchor: typing.Optional[str] = None,
                 viewportanchor: typing.Optional[str] = None,
                 scroll: typing.Optional[str] = None
                 ):
        """
        Initialize.

        :param id: identifier of the region
        :param width: width as a percentage of the video, e.g. ``40%``
        :param lines: number of lines of text, e.g. ``3``
        :param regionanchor: point of the region anchored to the video, as
            two percentages of the region, e.g. ``0%,100%``
        :param viewportanchor: point of the video the region is anchored
            to, as two percentages of the video, e.g. ``10%,90%``
        :param scroll: ``up`` for the lines to scroll up

        :raises MalformedCaptionError: if a value is not valid
        """
        super().__init__()
        self.id = id
        self.width = width
        self.lines = lines
        self.regionanchor = regionanchor
        self.viewportanchor = viewportanchor
        self.scroll = scroll
        self.comments: typing.List[str] = []

    @classmethod
    def from_string(cls, value: str, strict: bool = False) -> 'Region':
        """
        Return a `Region` instance from the settings of a region block.

        :param value: the region settings separated by spaces or line
            breaks, e.g. ``id:fred width:40%``
        :param strict: raise an error on settings that are not known, not
            valid or repeated instead of keeping them
        :returns: a `Region` instance

        :raises MalformedCaptionError: if the value is not a string or
            contains ``-->``, which cannot be in a region block, or if strict
            and a setting is not known, not valid or repeated
        """
        if type(value) is str and '-->' in value:
            raise MalformedCaptionError(f'Invalid region settings {value!r}')
        return super().from_string(value, strict)

    id = _setting_property('id', 'Identifier of the region.')
    width = _setting_property(
        'width',
        'Width as a percentage of the video.'
        )
    lines = _setting_property('lines', 'Number of lines of text.')
    regionanchor = _setting_property(
        'regionanchor',
        'Point of the region anchored to the video, as two percentages.'
        )
    viewportanchor = _setting_property(
        'viewportanchor',
        'Point of the video the region is anchored to, as two percentages.'
        )
    scroll = _setting_property('scroll', '``up`` if the lines scroll up.')
