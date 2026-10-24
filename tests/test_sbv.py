import unittest
import textwrap

from webvtt import sbv
from webvtt.errors import MalformedFileError
from webvtt.models import Caption


class TestSBVCueBlock(unittest.TestCase):

    def test_is_valid(self):
        self.assertTrue(sbv.SBVCueBlock.is_valid(textwrap.dedent('''
            00:00:00.500,00:00:07.000
            Caption #1
            ''').strip().split('\n'))
            )

        self.assertTrue(sbv.SBVCueBlock.is_valid(textwrap.dedent('''
            0:0:0.500,0:0:7.000
            Caption #1
            ''').strip().split('\n'))
            )

        self.assertTrue(sbv.SBVCueBlock.is_valid(textwrap.dedent('''
            00:00:00.500,00:00:07.000
            Caption #1 line 1
            Caption #1 line 2
            ''').strip().split('\n'))
            )

        self.assertFalse(sbv.SBVCueBlock.is_valid(textwrap.dedent('''
            00:00:00.500 --> 00:00:07.000
            Caption #1
            ''').strip().split('\n'))
            )

        self.assertFalse(sbv.SBVCueBlock.is_valid(textwrap.dedent('''
            1
            00:00:00.500,00:00:07.000
            Caption #1
            ''').strip().split('\n'))
            )

        self.assertFalse(sbv.SBVCueBlock.is_valid(textwrap.dedent('''
            1
            00:00:00.500,00:00:07.000
            ''').strip().split('\n'))
            )

        self.assertFalse(sbv.SBVCueBlock.is_valid(textwrap.dedent('''
            1
            Caption #1
            ''').strip().split('\n'))
            )

        self.assertFalse(sbv.SBVCueBlock.is_valid(textwrap.dedent('''
            Caption #1
            ''').strip().split('\n'))
            )

        self.assertFalse(sbv.SBVCueBlock.is_valid(textwrap.dedent('''
            00:00:00.500,00:00:07.000
            ''').strip().split('\n'))
            )

    def test_from_lines(self):
        cue_block = sbv.SBVCueBlock.from_lines(textwrap.dedent('''
                    00:00:00.500,00:00:07.000
                    Caption #1 line 1
                    Caption #1 line 2
                    ''').strip().split('\n')
                    )
        self.assertEqual(
            cue_block.start,
            '00:00:00.500'
            )
        self.assertEqual(
            cue_block.end,
            '00:00:07.000'
            )
        self.assertEqual(
            cue_block.payload,
            ['Caption #1 line 1', 'Caption #1 line 2']
            )

    def test_from_lines_shorter_timestamps(self):
        cue_block = sbv.SBVCueBlock.from_lines(textwrap.dedent('''
                    0:1:2.500,0:1:03.800
                    Caption #1 line 1
                    Caption #1 line 2
                    ''').strip().split('\n')
                    )
        self.assertEqual(
            cue_block.start,
            '0:1:2.500'
            )
        self.assertEqual(
            cue_block.end,
            '0:1:03.800'
            )

    def test_from_lines_hours_with_more_than_two_digits(self):
        cue_block = sbv.SBVCueBlock.from_lines(textwrap.dedent('''
                    100:00:00.000,100:00:05.000
                    Caption #1
                    ''').strip().split('\n')
                    )
        self.assertEqual(
            cue_block.start,
            '100:00:00.000'
            )
        self.assertEqual(
            cue_block.end,
            '100:00:05.000'
            )

    def test_is_valid_requires_dot_before_milliseconds(self):
        self.assertFalse(sbv.SBVCueBlock.is_valid(textwrap.dedent('''
                    0:00:01x000,0:00:02.000
                    Caption #1
                    ''').strip().split('\n')
                    ))
        self.assertFalse(sbv.SBVCueBlock.is_valid(textwrap.dedent('''
                    0:00:01.000,0:00:02x000
                    Caption #1
                    ''').strip().split('\n')
                    ))


class TestSBVModule(unittest.TestCase):

    def test_parse_invalid_format(self):
        self.assertRaises(
            MalformedFileError,
            sbv.parse,
            textwrap.dedent('''
                1
                00:00:00.500,00:00:07.000
                Caption text #1

                00:00:07.000,00:00:11.890
                Caption text #2
                ''').strip().split('\n')
                )

    def test_parse_captions(self):
        captions = sbv.parse(
            textwrap.dedent('''
            00:00:00.500,00:00:07.000
            Caption #1

            00:00:07.000,00:00:11.890
            Caption #2 line 1
            Caption #2 line 2
            ''').strip().split('\n')
            )
        self.assertEqual(len(captions), 2)
        self.assertIsInstance(captions[0], Caption)
        self.assertIsInstance(captions[1], Caption)
        self.assertEqual(
            str(captions[0]),
            '00:00:00.500 00:00:07.000 Caption #1'
            )
        self.assertEqual(
            str(captions[1]),
            r'00:00:07.000 00:00:11.890 Caption #2 line 1\n'
            'Caption #2 line 2'
            )

    def test_parse_skips_cue_with_malformed_timings(self):
        captions = sbv.parse(
            textwrap.dedent('''
            00:00:00.500,00:00:07.000
            Caption #1

            00:00:07x000,00:00:11.890
            Caption #2

            00:00:11.890,00:00:16.320
            Caption #3
            ''').strip().split('\n')
            )
        self.assertEqual(
            [caption.text for caption in captions],
            ['Caption #1', 'Caption #3']
            )

    def test_parse_ignores_text_attached_to_end_timestamp(self):
        for timings in ('0:00:01.000,0:00:02.0005',
                        '0:00:01.000,0:00:02.000xyz'):
            captions = sbv.parse([timings, 'Caption #1'])
            self.assertEqual(len(captions), 1)
            self.assertEqual(captions[0].end, '00:00:02.000')

    def test_parse_timings_over_range(self):
        captions = sbv.parse(['0:59:61.000,0:61:00.500', 'Caption #1'])
        self.assertEqual(len(captions), 1)
        self.assertEqual(captions[0].start, '01:00:01.000')
        self.assertEqual(captions[0].end, '01:01:00.500')

    def test_parse_cue_with_too_many_digits(self):
        captions = sbv.parse(
            ['0:00:01.000,0:00:02.000', 'Caption #1', '',
             '9' * 5000 + ':00:03.000,0:00:04.000', 'Caption #2']
            )
        self.assertEqual(len(captions), 1)
        self.assertEqual(captions[0].text, 'Caption #1')

    def test_parse_skips_cue_with_too_many_digits_hours(self):
        captions = sbv.parse(
            ['0:00:01.000,0:00:02.000', 'Caption #1', '',
             '99999999999:00:03.000,99999999999:00:04.000', 'Caption #2']
            )
        self.assertEqual(len(captions), 1)
        self.assertEqual(captions[0].text, 'Caption #1')
