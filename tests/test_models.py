import copy
import datetime
import re
import time
import unittest
import unittest.mock

from webvtt.models import (
    Timestamp, Caption, CueSettings, ParseIssue, Region, Style
    )
from webvtt.errors import MalformedCaptionError, MalformedRegionError


class TestTimestamp(unittest.TestCase):

    def test_instantiation(self):
        timestamp = Timestamp(
            hours=1, minutes=12, seconds=23, milliseconds=500
            )
        self.assertEqual(timestamp.hours, 1)
        self.assertEqual(timestamp.minutes, 12)
        self.assertEqual(timestamp.seconds, 23)
        self.assertEqual(timestamp.milliseconds, 500)

    def test_from_string(self):
        timestamp = Timestamp.from_string('01:24:11.670')
        self.assertEqual(timestamp.hours, 1)
        self.assertEqual(timestamp.minutes, 24)
        self.assertEqual(timestamp.seconds, 11)
        self.assertEqual(timestamp.milliseconds, 670)

    def test_from_string_single_digits(self):
        timestamp = Timestamp.from_string('1:2:7.670')
        self.assertEqual(timestamp.hours, 1)
        self.assertEqual(timestamp.minutes, 2)
        self.assertEqual(timestamp.seconds, 7)
        self.assertEqual(timestamp.milliseconds, 670)

    def test_from_string_short_fraction(self):
        timestamp = Timestamp.from_string('0:1:5.2')
        self.assertEqual(timestamp.hours, 0)
        self.assertEqual(timestamp.minutes, 1)
        self.assertEqual(timestamp.seconds, 5)
        self.assertEqual(timestamp.milliseconds, 200)
        self.assertEqual(str(timestamp), '00:01:05.200')
        self.assertEqual(Timestamp.from_string('00:12.54').milliseconds, 540)

    def test_from_string_missing_hours(self):
        timestamp = Timestamp.from_string('24:11.670')
        self.assertEqual(timestamp.hours, 0)
        self.assertEqual(timestamp.minutes, 24)
        self.assertEqual(timestamp.seconds, 11)
        self.assertEqual(timestamp.milliseconds, 670)

    def test_from_string_more_than_two_digits_hours(self):
        timestamp = Timestamp.from_string('100:24:11.670')
        self.assertEqual(timestamp.hours, 100)
        self.assertEqual(timestamp.minutes, 24)
        self.assertEqual(timestamp.seconds, 11)
        self.assertEqual(timestamp.milliseconds, 670)
        self.assertEqual(str(timestamp), '100:24:11.670')

    def test_from_string_ten_digits_hours(self):
        timestamp = Timestamp.from_string('9999999999:00:00.000')
        self.assertEqual(timestamp.hours, 9999999999)
        self.assertEqual(str(timestamp), '9999999999:00:00.000')

    def test_from_string_too_many_digits_hours(self):
        for value in ('10000000000:00:00.000', '1' * 5000 + ':00:00.000'):
            with self.subTest(digits=len(value) - 10):
                with self.assertRaises(MalformedCaptionError):
                    Timestamp.from_string(value)

    def test_from_string_wrong_minutes(self):
        with self.assertRaises(MalformedCaptionError):
            Timestamp.from_string('01:76:11.670')

    def test_from_string_wrong_seconds(self):
        with self.assertRaises(MalformedCaptionError):
            Timestamp.from_string('01:24:87.670')

    def test_from_string_non_ascii_digits(self):
        for value in ('\u0660\u0660:\u0660\u0661.\u0665\u0660\u0660',
                      '00:0\uff11.500'):
            with self.subTest(value=value):
                with self.assertRaises(MalformedCaptionError):
                    Timestamp.from_string(value)

    def test_from_string_wrong_type(self):
        with self.assertRaises(MalformedCaptionError):
            Timestamp.from_string(1234)

    def test_from_string_wrong_value(self):
        with self.assertRaises(MalformedCaptionError):
            Timestamp.from_string('01:24:11:670')

    def test_from_string_trailing_characters(self):
        for value in ('01:24:11.6705', '01:24:11.670abc', '01:24:11.670 '):
            with self.assertRaises(MalformedCaptionError):
                Timestamp.from_string(value)

    def test_to_tuple(self):
        self.assertEqual(
            Timestamp(
                hours=1, minutes=12, seconds=23, milliseconds=500
                ).to_tuple(),
            (1, 12, 23, 500)
            )

    def test_equality(self):
        self.assertTrue(
            Timestamp(
                hours=1, minutes=12, seconds=23, milliseconds=500
                ) ==
            Timestamp.from_string('01:12:23.500')
            )

    def test_not_equality(self):
        self.assertTrue(
            Timestamp(
                hours=1, minutes=12, seconds=23, milliseconds=500
                ) !=
            Timestamp.from_string('01:12:23.600')
            )

    def test_greater_than(self):
        self.assertTrue(
            Timestamp(
                hours=1, minutes=12, seconds=23, milliseconds=600
                ) >
            Timestamp.from_string('01:12:23.500')
            )

    def test_less_than(self):
        self.assertTrue(
            Timestamp(
                hours=1, minutes=12, seconds=23, milliseconds=500
                ) <
            Timestamp.from_string('01:12:23.600')
            )

    def test_greater_or_equal_than(self):
        self.assertTrue(
            Timestamp(
                hours=1, minutes=12, seconds=23, milliseconds=500
                ) >=
            Timestamp.from_string('01:12:23.500')
            )
        self.assertTrue(
            Timestamp(
                hours=1, minutes=12, seconds=23, milliseconds=600
                ) >=
            Timestamp.from_string('01:12:23.500')
            )

    def test_less_or_equal_than(self):
        self.assertTrue(
            Timestamp(
                hours=1, minutes=12, seconds=23, milliseconds=500
                ) <=
            Timestamp.from_string('01:12:23.500')
            )
        self.assertTrue(
            Timestamp(
                hours=1, minutes=12, seconds=23, milliseconds=500
                ) <=
            Timestamp.from_string('01:12:23.600')
            )

    def test_equality_other_types(self):
        timestamp = Timestamp(seconds=1)
        for other in (None, '00:00:01.000', 1, (0, 0, 1, 0)):
            with self.subTest(other=other):
                self.assertFalse(timestamp == other)
                self.assertTrue(timestamp != other)
        self.assertNotIn(None, [timestamp])

    def test_ordering_other_types(self):
        timestamp = Timestamp(seconds=1)
        for other in (None, '00:00:01.000', 1):
            with self.subTest(other=other):
                with self.assertRaises(TypeError):
                    timestamp < other
                with self.assertRaises(TypeError):
                    timestamp > other
                with self.assertRaises(TypeError):
                    timestamp <= other
                with self.assertRaises(TypeError):
                    timestamp >= other
                with self.assertRaises(TypeError):
                    other < timestamp

    def test_sort(self):
        self.assertEqual(
            sorted([Timestamp(seconds=2), Timestamp(), Timestamp(seconds=1)]),
            [Timestamp(), Timestamp(seconds=1), Timestamp(seconds=2)]
            )

    def test_repr(self):
        timestamp = Timestamp(
            hours=1,
            minutes=12,
            seconds=45,
            milliseconds=320
            )

        self.assertEqual(
            repr(timestamp),
            '<Timestamp hours=1 minutes=12 seconds=45 milliseconds=320>'
            )

    def test_from_seconds(self):
        timestamp = Timestamp.from_seconds(5051.67)
        self.assertEqual(timestamp.hours, 1)
        self.assertEqual(timestamp.minutes, 24)
        self.assertEqual(timestamp.seconds, 11)
        self.assertEqual(timestamp.milliseconds, 670)
        self.assertEqual(str(timestamp), '01:24:11.670')

    def test_from_seconds_int(self):
        self.assertEqual(str(Timestamp.from_seconds(0)), '00:00:00.000')
        self.assertEqual(str(Timestamp.from_seconds(65)), '00:01:05.000')

    def test_from_seconds_over_24_hours(self):
        self.assertEqual(
            str(Timestamp.from_seconds(360005.2)),
            '100:00:05.200'
            )

    def test_from_seconds_rounds_to_milliseconds(self):
        self.assertEqual(str(Timestamp.from_seconds(0.0004)), '00:00:00.000')
        self.assertEqual(str(Timestamp.from_seconds(1.2346)), '00:00:01.235')
        self.assertEqual(str(Timestamp.from_seconds(59.9996)), '00:01:00.000')
        self.assertEqual(
            str(Timestamp.from_seconds(3599.9999)),
            '01:00:00.000'
            )

    def test_from_seconds_rounds_halves_up(self):
        for value, expected in ((0.0005, '00:00:00.001'),
                                (0.0015, '00:00:00.002'),
                                (0.0025, '00:00:00.003'),
                                (1.0005, '00:00:01.001'),
                                (1.9995, '00:00:02.000'),
                                (0.5075, '00:00:00.508'),
                                (259.0395, '00:04:19.040'),
                                (0.0004999, '00:00:00.000')):
            with self.subTest(value=value):
                self.assertEqual(str(Timestamp.from_seconds(value)), expected)

    def test_from_seconds_largest_timestamp(self):
        self.assertEqual(str(Timestamp.from_seconds(35999999999999)),
                         '9999999999:59:59.000')

    def test_from_seconds_after_largest_timestamp(self):
        for value in (36000000000000, 1e300, 10 ** 400, 10 ** 1000000):
            with self.subTest(value=type(value).__name__):
                with self.assertRaises(MalformedCaptionError):
                    Timestamp.from_seconds(value)

    def test_from_seconds_invalid(self):
        for value in (-0.001, -1, float('nan'), float('inf'), '12', None,
                      True):
            with self.subTest(value=value):
                with self.assertRaises(MalformedCaptionError):
                    Timestamp.from_seconds(value)

    def test_from_seconds_round_trip(self):
        for value in ('00:00:00.000', '00:00:00.001', '01:24:11.670',
                      '23:59:59.999', '100:24:11.670'):
            with self.subTest(value=value):
                timestamp = Timestamp.from_string(value)
                self.assertEqual(
                    Timestamp.from_seconds(
                        timestamp.in_milliseconds() / 1000
                        ),
                    timestamp
                    )

    def test_in_seconds(self):
        self.assertEqual(Timestamp.from_string('01:24:11.999').in_seconds(),
                         5051
                         )

    def test_in_milliseconds(self):
        self.assertEqual(
            Timestamp.from_string('01:24:11.670').in_milliseconds(),
            5051670
            )
        self.assertEqual(
            Timestamp.from_string('00:00:00.000').in_milliseconds(),
            0
            )


class TestCaption(unittest.TestCase):

    def test_instantiation(self):
        caption = Caption(
            start='00:00:07.000',
            end='00:00:11.890',
            text='Hello test!',
            identifier='A test caption'
            )
        self.assertEqual(caption.start, '00:00:07.000')
        self.assertEqual(caption.end, '00:00:11.890')
        self.assertEqual(caption.text, 'Hello test!')
        self.assertEqual(caption.identifier, 'A test caption')

    def test_timestamp_wrong_type(self):
        with self.assertRaises(MalformedCaptionError):
            Caption(
                start=['00:00:07.000'],
                end='00:00:11.890',
                text='Hello test!',
                identifier='A test caption'
                )

    def test_identifier_is_optional(self):
        caption = Caption(
            start='00:00:07.000',
            end='00:00:11.890',
            text='Hello test!',
            )
        self.assertIsNone(caption.identifier)

    def test_multi_lines(self):
        caption = Caption(
            start='00:00:07.000',
            end='00:00:11.890',
            text='Hello test!\nThis is the second line',
            identifier='A test caption'
            )
        self.assertEqual(caption.text, 'Hello test!\nThis is the second line')
        self.assertListEqual(
            caption.lines,
            ['Hello test!', 'This is the second line']
            )

    def test_multi_lines_accepts_list(self):
        caption = Caption(
            start='00:00:07.000',
            end='00:00:11.890',
            text=['Hello test!', 'This is the second line'],
            identifier='A test caption'
            )
        self.assertEqual(caption.text, 'Hello test!\nThis is the second line')
        self.assertListEqual(
            caption.lines,
            ['Hello test!', 'This is the second line']
            )

    def test_cuetags(self):
        caption = Caption(
            start='00:00:07.000',
            end='00:00:11.890',
            text=[
                'Hello <c.colorE5E5E5>test</c>!',
                'This is the <c.colorE5E5E5>second</c> line'
                ],
            identifier='A test caption'
            )
        self.assertEqual(caption.text, 'Hello test!\nThis is the second line')
        self.assertEqual(
            caption.raw_text,
            'Hello <c.colorE5E5E5>test</c>!\n'
            'This is the <c.colorE5E5E5>second</c> line'
            )

    def test_in_seconds(self):
        caption = Caption(
            start='00:00:07.000',
            end='00:00:11.890',
            text=['Hello test!', 'This is the second line'],
            identifier='A test caption'
            )
        self.assertEqual(caption.start_in_seconds, 7)
        self.assertEqual(caption.end_in_seconds, 11)

    def test_in_milliseconds(self):
        caption = Caption('00:00:07.000', '00:00:11.890', 'Hello test!')
        self.assertEqual(caption.start_in_milliseconds, 7000)
        self.assertEqual(caption.end_in_milliseconds, 11890)

    def test_duration(self):
        caption = Caption('00:00:07.000', '00:00:11.890', 'Hello test!')
        self.assertEqual(caption.duration, 4.89)

    def test_duration_caption_ends_before_start(self):
        caption = Caption('00:00:05.000', '00:00:01.000', 'x')
        self.assertEqual(caption.duration, 0.0)

    def test_shift(self):
        caption = Caption('00:00:07.000', '00:00:11.890', 'Hello test!')
        caption.shift(1.5)
        self.assertEqual(caption.start, '00:00:08.500')
        self.assertEqual(caption.end, '00:00:13.390')
        self.assertEqual(caption.text, 'Hello test!')

    def test_shift_int(self):
        caption = Caption('00:00:07.000', '00:00:11.890')
        caption.shift(3600)
        self.assertEqual(caption.start, '01:00:07.000')
        self.assertEqual(caption.end, '01:00:11.890')

    def test_shift_negative(self):
        caption = Caption('00:01:07.000', '00:01:11.890')
        caption.shift(-62.25)
        self.assertEqual(caption.start, '00:00:04.750')
        self.assertEqual(caption.end, '00:00:09.640')

    def test_shift_timedelta(self):
        caption = Caption('00:00:07.000', '00:00:11.890')
        caption.shift(datetime.timedelta(minutes=1, milliseconds=10))
        self.assertEqual(caption.start, '00:01:07.010')
        self.assertEqual(caption.end, '00:01:11.900')

        caption.shift(datetime.timedelta(seconds=-60))
        self.assertEqual(caption.start, '00:00:07.010')
        self.assertEqual(caption.end, '00:00:11.900')

    def test_shift_rounds_to_milliseconds(self):
        caption = Caption('00:00:07.000', '00:00:11.890')
        caption.shift(0.0016)
        self.assertEqual(caption.start, '00:00:07.002')
        self.assertEqual(caption.end, '00:00:11.892')

        caption.shift(datetime.timedelta(microseconds=-1600))
        self.assertEqual(caption.start, '00:00:07.000')
        self.assertEqual(caption.end, '00:00:11.890')

    def test_shift_rounds_halves_away_from_zero(self):
        for offset, expected in ((0.0005, '00:00:10.001'),
                                 (-0.0005, '00:00:09.999'),
                                 (0.0025, '00:00:10.003'),
                                 (-0.0025, '00:00:09.997'),
                                 (0.0004999, '00:00:10.000'),
                                 (0.5075, '00:00:10.508'),
                                 (-0.5075, '00:00:09.492'),
                                 (259.0395, '00:04:29.040'),
                                 (datetime.timedelta(microseconds=500),
                                  '00:00:10.001'),
                                 (datetime.timedelta(microseconds=-500),
                                  '00:00:09.999'),
                                 (datetime.timedelta(microseconds=2500),
                                  '00:00:10.003'),
                                 (datetime.timedelta(microseconds=-2500),
                                  '00:00:09.997'),
                                 (datetime.timedelta(microseconds=499),
                                  '00:00:10.000')):
            with self.subTest(offset=offset):
                caption = Caption('00:00:10.000', '00:00:11.000')
                caption.shift(offset)
                self.assertEqual(caption.start, expected)

    def test_shift_and_back(self):
        caption = Caption('00:00:10.000', '00:00:11.000')
        for offset in (0.0005, 0.0025, 1.0005, -3.7775):
            with self.subTest(offset=offset):
                caption.shift(offset)
                caption.shift(-offset)
                self.assertEqual(caption.start, '00:00:10.000')
                self.assertEqual(caption.end, '00:00:11.000')

    def test_shift_clamps_start_to_zero(self):
        caption = Caption('00:00:00.500', '00:00:04.000')
        caption.shift(-2)
        self.assertEqual(caption.start, '00:00:00.000')
        self.assertEqual(caption.end, '00:00:02.000')

    def test_shift_clamps_start_and_end_to_zero(self):
        caption = Caption('00:00:00.500', '00:00:04.000')
        caption.shift(-10)
        self.assertEqual(caption.start, '00:00:00.000')
        self.assertEqual(caption.end, '00:00:00.000')

    def test_shift_invalid_type(self):
        for value in ('1.5', None, True, [1]):
            with self.subTest(value=value):
                caption = Caption('00:00:07.000', '00:00:11.890')
                with self.assertRaises(TypeError):
                    caption.shift(value)
                self.assertEqual(caption.start, '00:00:07.000')
                self.assertEqual(caption.end, '00:00:11.890')

    def test_shift_to_largest_timestamp(self):
        caption = Caption('00:00:07.000', '00:00:11.890')
        caption.shift(datetime.timedelta(milliseconds=35999999999988109))
        self.assertEqual(caption.end, '9999999999:59:59.999')

    def test_shift_after_largest_timestamp(self):
        for value in (datetime.timedelta(milliseconds=35999999999988110),
                      1e300, 10 ** 400, 10 ** 1000000):
            with self.subTest(value=type(value).__name__):
                caption = Caption('00:00:07.000', '00:00:11.890')
                with self.assertRaises(ValueError):
                    caption.shift(value)
                self.assertEqual(caption.start, '00:00:07.000')
                self.assertEqual(caption.end, '00:00:11.890')

    def test_shift_before_zero_by_a_huge_offset(self):
        for value in (-1e300, -10 ** 400, -10 ** 1000000):
            with self.subTest(value=type(value).__name__):
                caption = Caption('00:00:07.000', '00:00:11.890')
                caption.shift(value)
                self.assertEqual(caption.start, '00:00:00.000')
                self.assertEqual(caption.end, '00:00:00.000')

    def test_shift_not_finite(self):
        for value in (float('nan'), float('inf'), float('-inf')):
            with self.subTest(value=value):
                caption = Caption('00:00:07.000', '00:00:11.890')
                with self.assertRaises(ValueError):
                    caption.shift(value)
                self.assertEqual(caption.start, '00:00:07.000')
                self.assertEqual(caption.end, '00:00:11.890')

    def test_wrong_start_timestamp(self):
        self.assertRaises(
            MalformedCaptionError,
            Caption,
            start='1234',
            end='00:00:11.890',
            text='Hello Test!'
            )

    def test_wrong_type_start_timestamp(self):
        self.assertRaises(
            MalformedCaptionError,
            Caption,
            start=['00:00:07.000'],
            end='00:00:11.890',
            text='Hello Test!'
            )

    def test_wrong_end_timestamp(self):
        self.assertRaises(
            MalformedCaptionError,
            Caption,
            start='00:00:07.000',
            end='1234',
            text='Hello Test!'
            )

    def test_wrong_type_end_timestamp(self):
        self.assertRaises(
            MalformedCaptionError,
            Caption,
            start='00:00:07.000',
            end=['00:00:11.890'],
            text='Hello Test!'
            )

    def test_times_of_other_types(self):
        for start, end in (
                (1.5, 2),
                (Timestamp(0, 0, 1, 500), Timestamp(0, 0, 2, 0)),
                (datetime.timedelta(seconds=1.5),
                 datetime.timedelta(seconds=2)),
                ('00:00:01.500', 2.0)):
            with self.subTest(start=start, end=end):
                caption = Caption(start, end, 'x')
                self.assertEqual(caption.start, '00:00:01.500')
                self.assertEqual(caption.end, '00:00:02.000')

    def test_times_of_other_types_set(self):
        caption = Caption('00:00:01.000', '00:00:02.000', 'x')

        caption.start = Timestamp(0, 0, 3, 0)
        caption.end = 4.25
        self.assertEqual((caption.start, caption.end),
                         ('00:00:03.000', '00:00:04.250'))

        caption.start = datetime.timedelta(minutes=1)
        self.assertEqual(caption.start, '00:01:00.000')

    def test_times_zero(self):
        for value in (0, 0.0, datetime.timedelta(0), Timestamp(), '', None):
            with self.subTest(value=value):
                caption = Caption(value, value, 'x')
                self.assertEqual(caption.start, '00:00:00.000')
                self.assertEqual(caption.end, '00:00:00.000')

    def test_times_rounded_to_milliseconds(self):
        caption = Caption(1.0005, datetime.timedelta(microseconds=2_499_500))
        self.assertEqual(caption.start, '00:00:01.001')
        self.assertEqual(caption.end, '00:00:02.500')

    def test_timestamp_copied(self):
        timestamp = Timestamp(0, 0, 3, 0)
        caption = Caption(timestamp, timestamp, 'x')
        timestamp.seconds = 9

        self.assertEqual((caption.start, caption.end),
                         ('00:00:03.000', '00:00:03.000'))
        self.assertIsNot(caption.start_time, caption.end_time)

    def test_timestamp_fields_normalized(self):
        caption = Caption(Timestamp(0, 0, 75, 0), Timestamp(0, 90, 0, 0))
        self.assertEqual(caption.start, '00:01:15.000')
        self.assertEqual(caption.end, '01:30:00.000')

    def test_invalid_times_of_other_types(self):
        for value in (-1, -0.5, float('nan'), float('inf'), True, False,
                      10 ** 20, datetime.timedelta(seconds=-1),
                      Timestamp(0, 0, -1, 0), Timestamp(0, 0, 1.5, 0),
                      Timestamp(0, 0, True, 0), b'00:00:01.000', [1]):
            with self.subTest(value=value):
                with self.assertRaises(MalformedCaptionError):
                    Caption(value, '00:00:02.000', 'x')
                with self.assertRaises(MalformedCaptionError):
                    Caption('00:00:01.000', value, 'x')

                caption = Caption('00:00:01.000', '00:00:02.000', 'x')
                with self.assertRaises(MalformedCaptionError):
                    caption.start = value
                with self.assertRaises(MalformedCaptionError):
                    caption.end = value
                self.assertEqual((caption.start, caption.end),
                                 ('00:00:01.000', '00:00:02.000'))

    def test_copy(self):
        caption = Caption('00:00:01.000', '00:00:02.000', ['a', 'b'],
                          identifier='1', settings='line:0')
        caption.comments.append('note')

        copied = caption.copy()
        self.assertIsNot(copied, caption)
        self.assertEqual(copied, caption)
        self.assertEqual(copied.comments, ['note'])

        copied.lines.append('c')
        copied.comments.append('other')
        copied.settings.line = '1'
        copied.start_time.seconds = 5
        copied.end_time.seconds = 6
        copied.identifier = '2'

        self.assertEqual(caption.lines, ['a', 'b'])
        self.assertEqual(caption.comments, ['note'])
        self.assertEqual(str(caption.settings), 'line:0')
        self.assertEqual((caption.start, caption.end),
                         ('00:00:01.000', '00:00:02.000'))
        self.assertEqual(caption.identifier, '1')

    def test_equality(self):
        caption1 = Caption(
            start='00:00:07.000',
            end='00:00:11.890',
            text='Hello test!',
            identifier='A test caption'
            )

        caption2 = Caption(
            start='00:00:07.000',
            end='00:00:11.890',
            text='Hello test!',
            identifier='A test caption'
            )

        self.assertTrue(caption1 == caption2)

        caption1 = Caption(
            start='00:00:02.000',
            end='00:00:11.890',
            text='Hello test!',
            identifier='A test caption'
            )

        caption2 = Caption(
            start='00:00:07.000',
            end='00:00:11.890',
            text='Hello test!',
            identifier='A test caption'
            )

        self.assertFalse(caption1 == caption2)

        self.assertFalse(
            Caption(
                start='00:00:07.000',
                end='00:00:11.890',
                text='Hello test!',
                identifier='A test caption'
                ) == 1234
            )

    def test_repr(self):
        caption = Caption(
            start='00:00:07.000',
            end='00:00:11.890',
            text='Hello test!',
            identifier='A test caption'
            )

        self.assertEqual(
            repr(caption),
            "<Caption start='00:00:07.000' end='00:00:11.890' "
            "text='Hello test!' identifier='A test caption' settings=''>"
            )

    def test_repr_with_settings(self):
        caption = Caption(
            start='00:00:07.000',
            end='00:00:11.890',
            text='Hello test!',
            settings='line:0 align:start'
            )

        self.assertEqual(
            repr(caption),
            "<Caption start='00:00:07.000' end='00:00:11.890' "
            "text='Hello test!' identifier=None "
            "settings='line:0 align:start'>"
            )

    def test_settings_default(self):
        caption = Caption('00:00:07.000', '00:00:11.890', 'Hello test!')
        self.assertIsInstance(caption.settings, CueSettings)
        self.assertFalse(caption.settings)

    def test_settings_from_string(self):
        caption = Caption(
            '00:00:07.000',
            '00:00:11.890',
            'Hello test!',
            settings='line:0 align:middle'
            )
        self.assertEqual(caption.settings.line, '0')
        self.assertIsNone(caption.settings.align)
        self.assertEqual(str(caption.settings), 'line:0 align:middle')

    def test_settings_from_cue_settings_are_copied(self):
        settings = CueSettings(line='0')
        caption = Caption(
            '00:00:07.000',
            '00:00:11.890',
            'Hello test!',
            settings=settings
            )
        other = Caption('00:00:11.890', '00:00:13.000', 'Other')
        other.settings = caption.settings

        settings.line = '1'
        other.settings.line = '2'

        self.assertEqual(caption.settings.line, '0')
        self.assertEqual(other.settings.line, '2')

    def test_update_settings(self):
        caption = Caption(
            '00:00:07.000',
            '00:00:11.890',
            'Hello test!',
            settings='line:0'
            )
        caption.settings.align = 'start'
        self.assertEqual(str(caption.settings), 'line:0 align:start')

        caption.settings = 'size:50%'
        self.assertEqual(str(caption.settings), 'size:50%')

        caption.settings = None
        self.assertFalse(caption.settings)

    def test_settings_wrong_type(self):
        with self.assertRaises(MalformedCaptionError):
            Caption('00:00:07.000', '00:00:11.890', settings=['line:0'])

    def test_settings_not_validated(self):
        caption = Caption(
            '00:00:07.000',
            '00:00:11.890',
            settings='foo:bar line:0 line:1'
            )
        self.assertEqual(str(caption.settings), 'foo:bar line:0 line:1')

    def test_not_equality_settings(self):
        self.assertNotEqual(
            Caption(
                '00:00:07.000',
                '00:00:11.890',
                'Hello',
                settings='line:0'
                ),
            Caption('00:00:07.000', '00:00:11.890', 'Hello')
            )
        self.assertEqual(
            Caption(
                '00:00:07.000',
                '00:00:11.890',
                'Hello',
                settings='line:0'
                ),
            Caption(
                '00:00:07.000',
                '00:00:11.890',
                'Hello',
                settings=CueSettings(line='0')
                )
            )

    def test_str(self):
        caption = Caption(
            start='00:00:07.000',
            end='00:00:11.890',
            text='Hello test!',
            identifier='A test caption'
            )

        self.assertEqual(
            str(caption),
            '00:00:07.000 00:00:11.890 Hello test!'
            )

    def test_accept_comments(self):
        caption = Caption(
            start='00:00:07.000',
            end='00:00:11.890',
            text='Hello test!',
            identifier='A test caption'
            )
        caption.comments.append('One comment')
        caption.comments.append('Another comment')

        self.assertListEqual(
            caption.comments,
            ['One comment', 'Another comment']
            )

    def test_timestamp_update(self):
        c = Caption('00:00:00.500', '00:00:07.000')
        c.start = '00:00:01.750'
        c.end = '00:00:08.250'

        self.assertEqual(c.start, '00:00:01.750')
        self.assertEqual(c.end, '00:00:08.250')

    def test_timestamp_format(self):
        c = Caption('01:02:03.400', '02:03:04.500')
        self.assertEqual(c.start, '01:02:03.400')
        self.assertEqual(c.end, '02:03:04.500')

        c = Caption('02:03.400', '03:04.500')
        self.assertEqual(c.start, '00:02:03.400')
        self.assertEqual(c.end, '00:03:04.500')

    def test_update_text(self):
        c = Caption(text='Caption line #1')
        c.text = 'Caption line #1 updated'
        self.assertEqual(
            c.text,
            'Caption line #1 updated'
            )

    def test_update_text_multiline(self):
        c = Caption(text='Caption line #1')
        c.text = 'Caption line #1\nCaption line #2'

        self.assertEqual(
            len(c.lines),
            2
            )

        self.assertEqual(
            c.text,
            'Caption line #1\nCaption line #2'
            )

    def test_text_only_split_on_cr_and_lf(self):
        caption = Caption(text='line 1\u2028still line 1\r\nline 2\x85\n')
        self.assertListEqual(
            caption.lines,
            ['line 1\u2028still line 1', 'line 2\x85']
            )

        caption.text = 'line 1\x0cstill line 1\rline 2\n'
        self.assertListEqual(
            caption.lines,
            ['line 1\x0cstill line 1', 'line 2']
            )

    def test_set_text_keeps_lines(self):
        caption = Caption(text=['line 1\u2028still line 1', 'line 2'])
        caption.text = caption.text
        self.assertListEqual(
            caption.lines,
            ['line 1\u2028still line 1', 'line 2']
            )

    def test_empty_text(self):
        self.assertListEqual(Caption(text='').lines, [])

        caption = Caption(text='Caption line #1')
        caption.text = ''
        self.assertListEqual(caption.lines, [])

    def test_update_text_wrong_type(self):
        c = Caption(text='Caption line #1')
        for value in (123, None, b'text', ['line 1', 2]):
            with self.subTest(value=value):
                with self.assertRaises(TypeError) as cm:
                    c.text = value

                self.assertIn(repr(value), str(cm.exception))
                self.assertListEqual(c.lines, ['Caption line #1'])

    def test_update_text_with_lines(self):
        c = Caption(text='Caption line #1')
        for value in (['line 1', 'line 2'], ('line 1', 'line 2')):
            with self.subTest(value=value):
                c.text = value

                self.assertListEqual(c.lines, ['line 1', 'line 2'])
                self.assertEqual(c.text, 'line 1\nline 2')

        lines = ['line 1']
        c.text = lines
        lines.append('line 2')
        self.assertListEqual(c.lines, ['line 1'])

    def test_text_wrong_type(self):
        for text in (123, 0, b'text', b'', ['line 1', 2]):
            with self.subTest(text=text):
                with self.assertRaises(TypeError) as cm:
                    Caption(text=text)

                self.assertIn(repr(text), str(cm.exception))

    def test_text_from_iterable_of_lines(self):
        self.assertListEqual(
            Caption(text=(line for line in ('line 1', 'line 2'))).lines,
            ['line 1', 'line 2']
            )

    def test_manipulate_lines(self):
        c = Caption(text=['Caption line #1', 'Caption line #2'])
        c.lines[0] = 'Caption line #1 updated'
        self.assertEqual(
            c.lines[0],
            'Caption line #1 updated'
            )

    def test_malformed_start_timestamp(self):
        self.assertRaises(
            MalformedCaptionError,
            Caption,
            '01:00'
            )

    def test_voice_span(self):
        caption = Caption(text='<v Homer Simpson>Hello there!</v>')
        self.assertEqual(caption.text, 'Hello there!')
        self.assertEqual(caption.raw_text, '<v Homer Simpson>Hello there!</v>')
        self.assertEqual(caption.voice, 'Homer Simpson')

    def test_voice_span_with_classes(self):
        caption = Caption(text='<v.quiet.slow Lisa Simpson>I am Lisa</v>')
        self.assertEqual(caption.text, 'I am Lisa')
        self.assertEqual(
            caption.raw_text,
            '<v.quiet.slow Lisa Simpson>I am Lisa</v>'
            )
        self.assertEqual(caption.voice, 'Lisa Simpson')

    def test_voice_span_is_invalid(self):
        caption = Caption(text='<v Lets eat donuts')
        self.assertEqual(caption.text, '<v Lets eat donuts')
        self.assertEqual(
            caption.raw_text,
            '<v Lets eat donuts'
            )
        self.assertIsNone(caption.voice)

    def test_voice_span_injected(self):
        caption = Caption(text='This is a test')
        self.assertEqual(caption.text, 'This is a test')
        self.assertEqual(caption.raw_text, 'This is a test')
        self.assertIsNone(caption.voice)
        caption.text = '<v Homer Simpson>I like tests</v>'
        self.assertEqual(caption.text, 'I like tests')
        self.assertEqual(caption.raw_text, '<v Homer Simpson>I like tests</v>')
        self.assertEqual(caption.voice, 'Homer Simpson')

    def test_voice_span_removed(self):
        caption = Caption(text='<v Homer Simpson>I like tests</v>')
        self.assertEqual(caption.text, 'I like tests')
        self.assertEqual(caption.raw_text, '<v Homer Simpson>I like tests</v>')
        self.assertEqual(caption.voice, 'Homer Simpson')
        caption.text = 'This is a test'
        self.assertEqual(caption.text, 'This is a test')
        self.assertEqual(caption.raw_text, 'This is a test')
        self.assertIsNone(caption.voice)

    def test_voices(self):
        for raw_text, voices in (
                ('<v Homer Simpson>Hello there!</v>', ['Homer Simpson']),
                ('Hi <v Bob>there</v>', ['Bob']),
                ('<v Bob>Hi</v> <v.loud Alice>Hello</v>', ['Bob', 'Alice']),
                ('<v Bob>Hi\n<v Alice>Hello</v>\n<v Bob>Bye',
                 ['Bob', 'Alice', 'Bob']),
                ('<b><v.quiet.slow Lisa Simpson>I am Lisa</v></b>',
                 ['Lisa Simpson']),
                ('No voice <b>here</b>', []),
                ('', []),
                ('<v>no name</v> <v  >spaces</v> <V Bob>upper</V>', []),
                ('<vBob>no space</v> <voice Bob>other tag</voice>', []),
                ('</v Bob> end tag', []),
                ('<v Lets eat donuts', []),
                ('<v Bob>Hi <v Alice', ['Bob'])):
            with self.subTest(raw_text=raw_text):
                self.assertEqual(Caption(text=raw_text).voices, voices)

    def test_voices_first_is_voice(self):
        for raw_text in ('<v Homer Simpson>Hello there!</v>',
                         '<v.quiet.slow Lisa Simpson>I am Lisa</v>',
                         '<v Bob  >trailing spaces</v> <v Alice>x</v>'):
            with self.subTest(raw_text=raw_text):
                caption = Caption(text=raw_text)
                self.assertEqual(caption.voices[0], caption.voice)

    def test_voices_follow_the_text(self):
        caption = Caption(text='This is a test')
        self.assertEqual(caption.voices, [])
        caption.text = ['<v Bob>One</v>', '<v Alice>Two</v>']
        self.assertEqual(caption.voices, ['Bob', 'Alice'])
        caption.lines.append('<v Carol>Three</v>')
        self.assertEqual(caption.voices, ['Bob', 'Alice', 'Carol'])

    def test_text_decodes_each_text_token_once(self):
        for raw_text, plain_text in (
            ('<v Bob>Tom &amp; Jerry &lt;3</v>', 'Tom & Jerry <3'),
            ('&lt;b&gt;literal&lt;/b&gt;', '<b>literal</b>'),
            ('&amp;lt;', '&lt;'),
            ('&am<lang en></lang>p;', '&amp;'),
        ):
            with self.subTest(raw_text=raw_text):
                caption = Caption(text=raw_text)
                self.assertEqual(caption.text, plain_text)
                self.assertEqual(caption.raw_text, raw_text)

    def test_text_decodes_long_decimal_references(self):
        caption = Caption(text='&#' + '0' * 5000 + '60;')
        self.assertEqual(caption.text, '<')

        caption.text = '&#' + '9' * 5000 + ';'
        self.assertEqual(caption.text, '\ufffd')

    def test_text_strips_tags_like_regex(self):
        for raw_text in (
            '<v Bob>Hello <b>test</b>!',
            'a <unclosed tag',
            'a <b <i>nested< one',
            '<b>first line\nsecond</b> line <',
            '',
        ):
            caption = Caption(text=raw_text)
            self.assertEqual(
                caption.text,
                re.sub('<.*?>', '', raw_text)
            )


class TestLinearTime(unittest.TestCase):
    """
    The text and voices of captions, which were quadratic in the length of
    a line.

    The lines are long enough for a quadratic time to take many minutes, as
    re.sub('<.*?>', '', line) for the text took about 10 seconds on 64000
    "<", while a linear one takes less than a second.
    """

    LENGTH = 10 ** 6
    # seconds, for slow machines
    LIMIT = 5

    def assertLinear(self, cases, attribute):
        """Check the attribute of captions with each text and its value."""
        for name, text, expected in cases:
            with self.subTest(name):
                caption = Caption(text=text)
                start = time.perf_counter()
                value = getattr(caption, attribute)
                self.assertLess(time.perf_counter() - start, self.LIMIT)
                self.assertEqual(value, expected)

    def test_text(self):
        n = self.LENGTH
        lines = '\n'.join(['<'] * (n // 4))
        self.assertLinear((
            ('unclosed tags', '<' * n, '<' * n),
            ('text and unclosed tags', 'a<' * n, 'a<' * n),
            ('tags', '<b>a' * (n // 4), 'a' * (n // 4)),
            ('lines', lines, lines),
            ), 'text')

    def test_voice(self):
        n = self.LENGTH
        self.assertLinear((
            ('whitespace', '<v' + ' ' * n, None),
            ('unclosed name', '<v' + ' ' * n + 'a' * n, None),
            ('words', '<v' + ' a' * n, None),
            ('classes', '<v' + '.a' * n, None),
            ), 'voice')

    def test_voices(self):
        n = self.LENGTH
        self.assertLinear((
            ('whitespace', '<v' + ' ' * n + '>', []),
            ('unclosed spans', '<v ' * n, []),
            ('classes', '<v' + '.a' * n + '>', []),
            ('spans', '<v Bob>a' * (n // 10), ['Bob'] * (n // 10)),
            ), 'voices')


class TestStyle(unittest.TestCase):

    def test_instantiation(self):
        style = Style(text='::cue(b) {\ncolor: peachpuff;\n}')
        self.assertEqual(style.text, '::cue(b) {\ncolor: peachpuff;\n}')
        self.assertListEqual(
            style.lines,
            ['::cue(b) {', 'color: peachpuff;', '}']
            )

    def test_text_only_split_on_cr_and_lf(self):
        style = Style(text='::cue {\x0c color: red;\r\n}\n')
        self.assertListEqual(style.lines, ['::cue {\x0c color: red;', '}'])

    def test_text_accept_list_of_strings(self):
        style = Style(text=['::cue(b) {', 'color: peachpuff;', '}'])
        self.assertEqual(style.text, '::cue(b) {\ncolor: peachpuff;\n}')
        self.assertListEqual(
            style.lines,
            ['::cue(b) {', 'color: peachpuff;', '}']
            )

    def test_text_list_is_copied(self):
        lines = ['::cue(b) {', 'color: peachpuff;', '}']
        style = Style(lines)
        lines.append('::cue(i) {}')

        self.assertListEqual(
            style.lines,
            ['::cue(b) {', 'color: peachpuff;', '}']
            )

    def test_accept_comments(self):
        style = Style(text='::cue(b) {\ncolor: peachpuff;\n}')
        style.comments.append('One comment')
        style.comments.append('Another comment')

        self.assertListEqual(
            style.comments,
            ['One comment', 'Another comment']
            )

    def test_get_text(self):
        style = Style(['::cue(b) {', '  color: peachpuff;', '}'])
        self.assertEqual(
            style.text,
            '::cue(b) {\n  color: peachpuff;\n}'
            )

    def test_equality(self):
        style = Style('::cue(b) {\ncolor: peachpuff;\n}')
        other = Style(['::cue(b) {', 'color: peachpuff;', '}'])
        other.comments.append('Comments are not compared')
        self.assertEqual(style, other)
        self.assertNotEqual(style, Style('::cue(b) {}'))
        self.assertNotEqual(style, '::cue(b) {\ncolor: peachpuff;\n}')

    def test_equality_subclass_and_other_types(self):
        class MyStyle(Style):
            pass

        self.assertEqual(Style('a'), MyStyle('a'))
        self.assertEqual(MyStyle('a'), Style('a'))
        self.assertEqual(Style('a'), unittest.mock.ANY)

    def test_repr(self):
        self.assertEqual(
            repr(Style('::cue(b) {\ncolor: peachpuff;\n}')),
            "<Style text='::cue(b) {\\ncolor: peachpuff;\\n}'>"
            )


class TestCueSettings(unittest.TestCase):

    def test_instantiation_without_settings(self):
        settings = CueSettings()
        self.assertEqual(str(settings), '')
        self.assertFalse(settings)
        self.assertIsNone(settings.vertical)
        self.assertIsNone(settings.line)
        self.assertIsNone(settings.position)
        self.assertIsNone(settings.size)
        self.assertIsNone(settings.align)
        self.assertIsNone(settings.region)

    def test_instantiation(self):
        settings = CueSettings(
            vertical='rl',
            line='10%,end',
            position='50%,line-left',
            size='80%',
            align='start',
            region='fred'
            )
        self.assertTrue(settings)
        self.assertEqual(settings.vertical, 'rl')
        self.assertEqual(settings.line, '10%,end')
        self.assertEqual(settings.position, '50%,line-left')
        self.assertEqual(settings.size, '80%')
        self.assertEqual(settings.align, 'start')
        self.assertEqual(settings.region, 'fred')
        self.assertEqual(
            str(settings),
            'vertical:rl line:10%,end position:50%,line-left size:80% '
            'align:start region:fred'
            )

    def test_instantiation_only_keyword_arguments(self):
        with self.assertRaises(TypeError):
            CueSettings('rl')

    def test_instantiation_invalid_value(self):
        with self.assertRaises(MalformedCaptionError):
            CueSettings(align='middle')

    def test_from_string(self):
        settings = CueSettings.from_string('line:0 align:start')
        self.assertEqual(settings.line, '0')
        self.assertEqual(settings.align, 'start')
        self.assertIsNone(settings.position)
        self.assertEqual(str(settings), 'line:0 align:start')

    def test_from_string_empty(self):
        for value in ('', ' ', ' \t '):
            settings = CueSettings.from_string(value)
            self.assertFalse(settings)
            self.assertEqual(str(settings), '')

    def test_from_string_keeps_order(self):
        settings = CueSettings.from_string(
            'align:end size:50% vertical:lr line:2'
            )
        self.assertEqual(
            str(settings),
            'align:end size:50% vertical:lr line:2'
            )

    def test_from_string_splits_on_spaces(self):
        settings = CueSettings.from_string(
            ' line:0\talign:start\x0csize:50%\r\nregion:fred  '
            )
        self.assertEqual(settings.line, '0')
        self.assertEqual(settings.align, 'start')
        self.assertEqual(settings.size, '50%')
        self.assertEqual(settings.region, 'fred')
        self.assertEqual(
            str(settings),
            'line:0 align:start size:50% region:fred'
            )

    def test_from_string_only_splits_on_ascii_spaces(self):
        settings = CueSettings.from_string('line:0\xa0align:start')
        self.assertIsNone(settings.line)
        self.assertIsNone(settings.align)
        self.assertEqual(str(settings), 'line:0\xa0align:start')

    def test_from_string_keeps_invalid_settings(self):
        settings = CueSettings.from_string(
            'line:90% position:50% align:middle'
            )
        self.assertEqual(settings.line, '90%')
        self.assertEqual(settings.position, '50%')
        self.assertIsNone(settings.align)
        self.assertEqual(
            str(settings),
            'line:90% position:50% align:middle'
            )

    def test_from_string_keeps_unknown_settings(self):
        settings = CueSettings.from_string('foo:bar line:0 baz :x y:')
        self.assertEqual(settings.line, '0')
        self.assertEqual(str(settings), 'foo:bar line:0 baz :x y:')

    def test_from_string_repeated_setting(self):
        settings = CueSettings.from_string('line:0 align:start line:5')
        self.assertEqual(settings.line, '5')
        self.assertEqual(str(settings), 'line:0 align:start line:5')

    def test_from_string_repeated_setting_last_valid(self):
        settings = CueSettings.from_string('line:0 line:top')
        self.assertEqual(settings.line, '0')

    def test_from_string_value_with_colon(self):
        settings = CueSettings.from_string('region:a:b')
        self.assertEqual(settings.region, 'a:b')

    def test_from_string_wrong_type(self):
        with self.assertRaises(MalformedCaptionError):
            CueSettings.from_string(None)

    def test_from_string_strict(self):
        settings = CueSettings.from_string(
            'vertical:lr line:-1,center position:10%,line-right size:0% '
            'align:right region:fred',
            strict=True
            )
        self.assertEqual(settings.line, '-1,center')
        self.assertEqual(settings.region, 'fred')

    def test_from_string_strict_invalid_settings(self):
        for value in ('align:middle',
                      'line:0 foo:bar',
                      'line:0 baz',
                      ':start',
                      'align:',
                      ):
            with self.subTest(value=value):
                with self.assertRaises(MalformedCaptionError):
                    CueSettings.from_string(value, strict=True)

    def test_from_string_strict_repeated_setting(self):
        with self.assertRaises(MalformedCaptionError) as cm:
            CueSettings.from_string('line:0 line:5', strict=True)
        self.assertIn('line:5', str(cm.exception))

    def test_valid_values(self):
        valid_values = {
            'vertical': ('rl', 'lr'),
            'line': ('0', '-1', '12', '0%', '100%', '33.5%', '10%,start',
                     '2,center', '-3,end'),
            'position': ('0%', '50%', '100%', '12.25%', '50%,line-left',
                         '50%,center', '50%,line-right'),
            'size': ('0%', '80%', '100%', '99.9%'),
            'align': ('start', 'center', 'end', 'left', 'right'),
            'region': ('fred', 'a:b', 'région-1'),
            }
        for name, values in valid_values.items():
            for value in values:
                with self.subTest(name=name, value=value):
                    settings = CueSettings()
                    setattr(settings, name, value)
                    self.assertEqual(getattr(settings, name), value)
                    self.assertEqual(str(settings), f'{name}:{value}')
                    self.assertEqual(
                        getattr(CueSettings.from_string(str(settings)), name),
                        value
                        )

    def test_invalid_values(self):
        invalid_values = {
            'vertical': ('', 'RL', 'rr'),
            'line': ('', 'top', '1.5', '--1', '1-', '+1', '-10%', '101%',
                     '10%,', '10%,top', '0,start,end', '٣'),
            'position': ('', '50', '-1%', '100.1%', '.5%', '5.%', '50%,',
                         '50%,start', '٥٠%'),
            'size': ('', '80', '101%', '1e2%', 'auto'),
            'align': ('', 'middle', 'Start', 'line-left'),
            'region': ('', 'a-->b'),
            }
        for name, values in invalid_values.items():
            for value in values:
                with self.subTest(name=name, value=value):
                    with self.assertRaises(MalformedCaptionError):
                        setattr(CueSettings(), name, value)
                    self.assertIsNone(
                        getattr(
                            CueSettings.from_string(f'{name}:{value}'),
                            name
                            )
                        )

    def test_set_value_with_spaces(self):
        for name, value in (('vertical', 'rl '),
                            ('line', '0 align:start'),
                            ('size', ' 50%'),
                            ('region', 'a b'),
                            ('region', 'a\tb'),
                            ('region', 'a\nb'),
                            ):
            with self.subTest(name=name, value=value):
                with self.assertRaises(MalformedCaptionError):
                    setattr(CueSettings(), name, value)

    def test_set_wrong_type(self):
        for value in (0, 50.0, b'start'):
            with self.subTest(value=value):
                with self.assertRaises(MalformedCaptionError):
                    CueSettings().line = value

    def test_set_adds_setting_at_the_end(self):
        settings = CueSettings.from_string('line:0 foo:bar')
        settings.align = 'start'
        self.assertEqual(str(settings), 'line:0 foo:bar align:start')

    def test_set_replaces_setting_in_place(self):
        settings = CueSettings.from_string('line:0 align:start size:50%')
        settings.align = 'end'
        self.assertEqual(str(settings), 'line:0 align:end size:50%')

    def test_set_replaces_invalid_setting(self):
        settings = CueSettings.from_string('line:90% align:middle')
        settings.align = 'center'
        self.assertEqual(settings.align, 'center')
        self.assertEqual(str(settings), 'line:90% align:center')

    def test_set_replaces_repeated_setting(self):
        settings = CueSettings.from_string('line:0 align:start line:5')
        settings.line = '-1'
        self.assertEqual(str(settings), 'line:-1 align:start')

    def test_set_invalid_value_keeps_settings(self):
        settings = CueSettings.from_string('line:0 align:start')
        with self.assertRaises(MalformedCaptionError):
            settings.align = 'middle'
        self.assertEqual(str(settings), 'line:0 align:start')

    def test_set_none_removes_setting(self):
        settings = CueSettings.from_string(
            'line:0 align:middle size:50% align:start'
            )
        settings.align = None
        self.assertIsNone(settings.align)
        self.assertEqual(str(settings), 'line:0 size:50%')

    def test_set_none_without_setting(self):
        settings = CueSettings.from_string('line:0')
        settings.align = None
        self.assertEqual(str(settings), 'line:0')

    def test_set_does_not_change_unknown_settings(self):
        settings = CueSettings.from_string('line foo:bar line:0')
        settings.line = None
        self.assertEqual(str(settings), 'line foo:bar')

    def test_equality(self):
        self.assertEqual(
            CueSettings.from_string('line:0 align:start'),
            CueSettings(line='0', align='start')
            )
        self.assertEqual(CueSettings(), CueSettings.from_string(''))

    def test_not_equality(self):
        self.assertNotEqual(
            CueSettings.from_string('line:0 align:start'),
            CueSettings.from_string('align:start line:0')
            )
        self.assertNotEqual(
            CueSettings.from_string('line:0'),
            CueSettings.from_string('line:1')
            )
        self.assertNotEqual(CueSettings.from_string('line:0'), 'line:0')

    def test_repr(self):
        self.assertEqual(
            repr(CueSettings.from_string('line:0 align:start')),
            "<CueSettings text='line:0 align:start'>"
            )

    def test_iterate_settings(self):
        settings = CueSettings.from_string('line:0 foo align:middle')
        self.assertListEqual(list(settings), ['line:0', 'foo', 'align:middle'])
        self.assertListEqual(list(CueSettings()), [])


class TestRegion(unittest.TestCase):

    def test_instantiation_without_settings(self):
        region = Region()
        self.assertFalse(region)
        self.assertEqual(str(region), '')
        self.assertIsNone(region.id)
        self.assertIsNone(region.width)
        self.assertIsNone(region.lines)
        self.assertIsNone(region.regionanchor)
        self.assertIsNone(region.viewportanchor)
        self.assertIsNone(region.scroll)
        self.assertListEqual(region.comments, [])

    def test_instantiation(self):
        region = Region(
            id='fred',
            width='40%',
            lines='3',
            regionanchor='0%,100%',
            viewportanchor='10%,90%',
            scroll='up'
            )
        self.assertEqual(region.id, 'fred')
        self.assertEqual(region.width, '40%')
        self.assertEqual(region.lines, '3')
        self.assertEqual(region.regionanchor, '0%,100%')
        self.assertEqual(region.viewportanchor, '10%,90%')
        self.assertEqual(region.scroll, 'up')
        self.assertListEqual(
            list(region),
            ['id:fred', 'width:40%', 'lines:3', 'regionanchor:0%,100%',
             'viewportanchor:10%,90%', 'scroll:up']
            )

    def test_instantiation_only_keyword_arguments(self):
        with self.assertRaises(TypeError):
            Region('fred')

    def test_instantiation_invalid_value(self):
        with self.assertRaises(MalformedRegionError) as cm:
            Region(scroll='down')
        self.assertIn('scroll region setting', str(cm.exception))

    def test_from_string_multiple_lines(self):
        region = Region.from_string(
            'id:fred width:40%\nlines:3\r\nscroll:up'
            )
        self.assertEqual(region.id, 'fred')
        self.assertEqual(region.lines, '3')
        self.assertListEqual(
            list(region),
            ['id:fred', 'width:40%', 'lines:3', 'scroll:up']
            )
        self.assertListEqual(region.comments, [])

    def test_from_string_keeps_invalid_and_unknown_settings(self):
        region = Region.from_string('id:fred lines:2.5 foo:bar id:bill')
        self.assertEqual(region.id, 'bill')
        self.assertIsNone(region.lines)
        self.assertListEqual(
            list(region),
            ['id:fred', 'lines:2.5', 'foo:bar', 'id:bill']
            )

    def test_from_string_strict(self):
        region = Region.from_string(
            'id:fred width:40% lines:3 regionanchor:0%,100% '
            'viewportanchor:10%,90% scroll:up',
            strict=True
            )
        self.assertEqual(region.viewportanchor, '10%,90%')

    def test_from_string_strict_invalid_settings(self):
        for value, message in (('id:fred scroll:down', 'Invalid'),
                               ('id:fred foo:bar', 'Invalid'),
                               ('id:fred id:bill', 'Repeated'),
                               ):
            with self.subTest(value=value):
                with self.assertRaises(MalformedRegionError) as cm:
                    Region.from_string(value, strict=True)
                self.assertIn(f'{message} region setting', str(cm.exception))

    def test_from_string_wrong_type(self):
        with self.assertRaises(MalformedRegionError) as cm:
            Region.from_string(None)
        self.assertIn('Invalid region settings', str(cm.exception))

    def test_valid_values(self):
        valid_values = {
            'id': ('fred', 'a:b', 'région-1'),
            'width': ('0%', '40%', '100%', '33.3%'),
            'lines': ('0', '3', '12'),
            'regionanchor': ('0%,100%', '50.5%,0%'),
            'viewportanchor': ('10%,90%', '100%,100%'),
            'scroll': ('up',),
            }
        for name, values in valid_values.items():
            for value in values:
                with self.subTest(name=name, value=value):
                    region = Region()
                    setattr(region, name, value)
                    self.assertEqual(getattr(region, name), value)
                    self.assertEqual(
                        getattr(Region.from_string(str(region)), name),
                        value
                        )

    def test_invalid_values(self):
        invalid_values = {
            'id': ('',),
            'width': ('', '40', '101%', '-1%'),
            'lines': ('', '-1', '2.5', '+3', '\u0663'),
            'regionanchor': ('', '0%', '0%,', ',100%', '0%,100%,0%',
                             '0,100', '101%,0%'),
            'viewportanchor': ('', '10%;90%', '10%,-90%'),
            'scroll': ('', 'down', 'Up', 'none'),
            }
        for name, values in invalid_values.items():
            for value in values:
                with self.subTest(name=name, value=value):
                    with self.assertRaises(MalformedRegionError):
                        setattr(Region(), name, value)
                    self.assertIsNone(
                        getattr(Region.from_string(f'{name}:{value}'), name)
                        )

    def test_set_value_with_arrow(self):
        with self.assertRaises(MalformedRegionError):
            Region().id = 'a-->b'

    def test_from_string_with_arrow(self):
        for value in ('id:a-->b', 'id:fred -->', 'id:fred\n-->'):
            with self.subTest(value=value):
                with self.assertRaises(MalformedRegionError) as cm:
                    Region.from_string(value)
                self.assertIn('Invalid region settings', str(cm.exception))

    def test_set_value_with_spaces(self):
        for value in ('fred bill', 'fred\nbill'):
            with self.subTest(value=value):
                with self.assertRaises(MalformedRegionError):
                    Region().id = value

    def test_update_settings(self):
        region = Region.from_string('id:fred width:40% scroll:down')
        region.width = '50%'
        region.scroll = 'up'
        region.lines = None
        region.regionanchor = '0%,100%'
        self.assertListEqual(
            list(region),
            ['id:fred', 'width:50%', 'scroll:up', 'regionanchor:0%,100%']
            )

    def test_accept_comments(self):
        region = Region(id='fred')
        region.comments.append('One comment')
        self.assertListEqual(region.comments, ['One comment'])

    def test_equality(self):
        region = Region.from_string('id:fred width:40%')
        other = Region(id='fred', width='40%')
        other.comments.append('Comments are not compared')
        self.assertEqual(region, other)
        self.assertNotEqual(region, Region(id='fred'))
        self.assertNotEqual(
            Region.from_string('id:fred'),
            CueSettings.from_string('id:fred')
            )

    def test_repr(self):
        self.assertEqual(
            repr(Region(id='fred', width='40%')),
            "<Region text='id:fred width:40%'>"
            )


class TestDeepCopy(unittest.TestCase):

    def test_deepcopy(self):
        caption = Caption('00:00:01.000', '00:00:02.000', ['a', 'b'],
                          identifier='1', settings='line:0')
        caption.comments.append('note')
        region = Region(id='fred', width='40%')
        region.comments.append('note')
        style = Style('::cue(b) {}')
        style.comments.append('note')

        for value in (Timestamp(1, 2, 3, 4),
                      CueSettings.from_string('line:0 align:start'),
                      caption,
                      style,
                      region,
                      ParseIssue(3, 'Invalid cue block', ['x'])):
            with self.subTest(value=value):
                copied = copy.deepcopy(value)
                self.assertIsNot(copied, value)
                self.assertEqual(copied, value)
                self.assertEqual(vars(copied), vars(value))
