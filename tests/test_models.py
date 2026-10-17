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
