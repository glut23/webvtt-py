import datetime
import re
import time
import unittest

from webvtt.models import Timestamp, Caption, Style
from webvtt.errors import MalformedCaptionError


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

    def test_from_string_wrong_minutes(self):
        with self.assertRaises(MalformedCaptionError):
            Timestamp.from_string('01:76:11.670')

    def test_from_string_wrong_seconds(self):
        with self.assertRaises(MalformedCaptionError):
            Timestamp.from_string('01:24:87.670')

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
                                (0.0004999, '00:00:00.000')):
            with self.subTest(value=value):
                self.assertEqual(str(Timestamp.from_seconds(value)), expected)

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
                start=1234,
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
            start=1234,
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
            end=1234,
            text='Hello Test!'
            )

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
            "text='Hello test!' identifier='A test caption'>"
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

    def test_update_text_wrong_type(self):
        c = Caption(text='Caption line #1')

        self.assertRaises(
            AttributeError,
            setattr,
            c,
            'text',
            123
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

    def test_text_unclosed_tags_are_linear(self):
        # re.sub('<.*?>', ...) took about 10 seconds on this input
        caption = Caption(text='<' * 64000)
        start = time.perf_counter()
        self.assertEqual(caption.text, '<' * 64000)
        self.assertLess(time.perf_counter() - start, 1)


class TestStyle(unittest.TestCase):

    def test_instantiation(self):
        style = Style(text='::cue(b) {\ncolor: peachpuff;\n}')
        self.assertEqual(style.text, '::cue(b) {\ncolor: peachpuff;\n}')
        self.assertListEqual(
            style.lines,
            ['::cue(b) {', 'color: peachpuff;', '}']
            )

    def test_text_accept_list_of_strings(self):
        style = Style(text=['::cue(b) {', 'color: peachpuff;', '}'])
        self.assertEqual(style.text, '::cue(b) {\ncolor: peachpuff;\n}')
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
