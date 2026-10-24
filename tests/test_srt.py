import unittest
import io
import textwrap

from webvtt import srt
from webvtt.errors import MalformedFileError
from webvtt.models import Caption


class TestSRTCueBlock(unittest.TestCase):

    def test_is_valid(self):
        self.assertTrue(srt.SRTCueBlock.is_valid(textwrap.dedent('''
            1
            00:00:00,500 --> 00:00:07,000
            Caption #1
            ''').strip().split('\n'))
            )

        self.assertTrue(srt.SRTCueBlock.is_valid(textwrap.dedent('''
            1
            00:00:00,500 --> 00:00:07,000
            Caption #1 line 1
            Caption #1 line 2
            ''').strip().split('\n'))
            )

        self.assertFalse(srt.SRTCueBlock.is_valid(textwrap.dedent('''
            00:00:00,500 --> 00:00:07,000
            Caption #1
            ''').strip().split('\n'))
            )

        self.assertTrue(srt.SRTCueBlock.is_valid(textwrap.dedent('''
            1
            00:00:00.500 --> 00:00:07.000
            Caption #1
            ''').strip().split('\n'))
            )

        self.assertTrue(srt.SRTCueBlock.is_valid(textwrap.dedent('''
            1
            00:00:00,500 --> 00:00:07,000
            ''').strip().split('\n'))
            )

        self.assertFalse(srt.SRTCueBlock.is_valid(textwrap.dedent('''
            1
            Caption #1
            ''').strip().split('\n'))
            )

        self.assertFalse(srt.SRTCueBlock.is_valid(textwrap.dedent('''
            Caption #1
            ''').strip().split('\n'))
            )

        self.assertFalse(srt.SRTCueBlock.is_valid(textwrap.dedent('''
            00:00:00,500 --> 00:00:07,000
            ''').strip().split('\n'))
            )

    def test_is_valid_index_with_whitespace(self):
        self.assertTrue(srt.SRTCueBlock.is_valid(
            ['1 ', '00:00:00,500 --> 00:00:07,000', 'Caption #1']
            ))

    def test_is_valid_text_after_end_timestamp(self):
        self.assertTrue(srt.SRTCueBlock.is_valid(
            ['1', '00:00:00,500 --> 00:00:07,000 X1:100 X2:200', 'Caption #1']
            ))

    def test_from_lines(self):
        cue_block = srt.SRTCueBlock.from_lines(textwrap.dedent('''
            1
            00:00:00,500 --> 00:00:07,000
            Caption #1 line 1
            Caption #1 line 2
            ''').strip().split('\n')
            )
        self.assertEqual(cue_block.index, '1')
        self.assertEqual(
            cue_block.start,
            '00:00:00,500'
            )
        self.assertEqual(
            cue_block.end,
            '00:00:07,000'
            )
        self.assertEqual(
            cue_block.payload,
            ['Caption #1 line 1', 'Caption #1 line 2']
            )


class TestSRTModule(unittest.TestCase):

    def test_parse_timestamp(self):
        for value, expected in (('00:00:07,500', '00:00:07.500'),
                                ('00:00:07.500', '00:00:07.500'),
                                ('0:0:7,500', '00:00:07.500'),
                                ('00:00:07,5', '00:00:07.005'),
                                ('00:00:07,50', '00:00:07.050'),
                                ('00:00:07,0005', '00:00:07.005'),
                                ('00:00:07,1500', '00:00:08.500'),
                                ('00:00:61,000', '00:01:01.000'),
                                ('00:61:01,000', '01:01:01.000'),
                                ('100:00:07,000', '100:00:07.000')):
            self.assertEqual(str(srt.parse_timestamp(value)), expected)

    def test_parse_invalid_format(self):
        self.assertRaises(
            MalformedFileError,
            srt.parse,
            textwrap.dedent('''
                00:00:00,500 --> 00:00:07,000
                Caption text #1

                00:00:07,000 --> 00:00:11,890
                Caption text #2
                ''').strip().split('\n')
            )

    def test_parse_captions(self):
        captions = srt.parse(
            textwrap.dedent('''
            1
            00:00:00,500 --> 00:00:07,000
            Caption #1

            2
            00:00:07,000 --> 00:00:11,890
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

    def test_parse_captions_with_empty_lines_in_text(self):
        captions = srt.parse(
            textwrap.dedent('''
            1
            00:02:05,988 --> 00:02:10,987
            CHAPITRE 12

            BAPTÊME ET PARADIS DES DIEUX

            2
            00:02:13,278 --> 00:02:14,367
            Je vois…
            ''').strip().split('\n')
            )
        self.assertEqual(len(captions), 2)
        self.assertEqual(
            captions[0].lines,
            ['CHAPITRE 12', 'BAPTÊME ET PARADIS DES DIEUX']
            )
        self.assertEqual(captions[1].lines, ['Je vois…'])

    def test_parse_captions_with_empty_line_after_cue_timings(self):
        captions = srt.parse(
            textwrap.dedent('''
            1
            00:00:00,500 --> 00:00:07,000

            Caption #1

            2
            00:00:07,000 --> 00:00:11,890

            Caption #2 line 1

            Caption #2 line 2

            3
            00:00:11,890 --> 00:00:16,320
            Caption #3
            ''').strip().split('\n')
            )
        self.assertEqual(len(captions), 3)
        self.assertEqual(
            str(captions[0]),
            '00:00:00.500 00:00:07.000 Caption #1'
            )
        self.assertEqual(
            str(captions[1]),
            r'00:00:07.000 00:00:11.890 Caption #2 line 1\n'
            'Caption #2 line 2'
            )
        self.assertEqual(
            str(captions[2]),
            '00:00:11.890 00:00:16.320 Caption #3'
            )

    def test_parse_captions_with_whitespace_lines_in_text(self):
        captions = srt.parse(
            ['1',
             '00:00:00,500 --> 00:00:07,000',
             'Caption #1 line 1',
             '  ',
             'Caption #1 line 2'
             ]
            )
        self.assertEqual(len(captions), 1)
        self.assertEqual(
            captions[0].lines,
            ['Caption #1 line 1', 'Caption #1 line 2']
            )

    def test_parse_skips_text_of_cue_with_invalid_timings(self):
        captions = srt.parse(
            textwrap.dedent('''
            1
            00:00:00,500 --> 00:00:07,000
            Caption #1

            2
            00:00:07,000 --> 00:00:11:890
            Caption #2

            More text of caption #2

            3
            00:00:11,890 --> 00:00:16,320
            Caption #3
            ''').strip().split('\n')
            )
        self.assertEqual(len(captions), 2)
        self.assertEqual(captions[0].lines, ['Caption #1'])
        self.assertEqual(captions[1].lines, ['Caption #3'])

    def test_parse_captions_without_empty_line_between_cues(self):
        captions = srt.parse(
            textwrap.dedent('''
            1
            00:00:00,500 --> 00:00:07,000
            Caption #1
            2
            00:00:07,000 --> 00:00:11,890
            Caption #2
            ''').strip().split('\n')
            )
        self.assertEqual(len(captions), 2)
        self.assertEqual(captions[0].lines, ['Caption #1'])
        self.assertEqual(captions[1].lines, ['Caption #2'])

    def test_parse_captions_with_empty_line_in_text_and_next_cue(self):
        captions = srt.parse(
            textwrap.dedent('''
            1
            00:00:00,500 --> 00:00:07,000
            Caption #1 line 1

            Caption #1 line 2
            2
            00:00:07,000 --> 00:00:11,890
            Caption #2
            ''').strip().split('\n')
            )
        self.assertEqual(len(captions), 2)
        self.assertEqual(
            captions[0].lines,
            ['Caption #1 line 1', 'Caption #1 line 2']
            )
        self.assertEqual(captions[1].lines, ['Caption #2'])

    def test_parse_captions_with_whitespace_around_index(self):
        captions = srt.parse(
            ['1',
             '00:00:00,500 --> 00:00:07,000',
             'Caption #1',
             '',
             ' 2 ',
             '00:00:07,000 --> 00:00:11,890',
             'Caption #2'
             ]
            )
        self.assertEqual(len(captions), 2)
        self.assertEqual(captions[0].lines, ['Caption #1'])
        self.assertEqual(captions[1].lines, ['Caption #2'])

    def test_parse_skips_cue_without_index(self):
        captions = srt.parse(
            textwrap.dedent('''
            1
            00:00:00,500 --> 00:00:07,000
            Caption #1

            00:00:07,000 --> 00:00:11,890
            Caption #2

            3
            00:00:11,890 --> 00:00:16,320
            Caption #3
            ''').strip().split('\n')
            )
        self.assertEqual(len(captions), 2)
        self.assertEqual(captions[0].lines, ['Caption #1'])
        self.assertEqual(captions[1].lines, ['Caption #3'])

    def test_parse_ignores_text_attached_to_end_timestamp(self):
        captions = srt.parse(
            ['1', '00:00:00,500 --> 00:00:07,000xyz', 'Caption #1']
            )
        self.assertEqual(len(captions), 1)
        self.assertEqual(captions[0].end, '00:00:07.000')

    def test_parse_timings_variants(self):
        for timings, start, end in (
                ('00:00:00.500 --> 00:00:07.000',
                 '00:00:00.500', '00:00:07.000'),
                ('00:00:00.500 --> 00:00:07,000',
                 '00:00:00.500', '00:00:07.000'),
                ('0:0:0,500 --> 0:0:7,000',
                 '00:00:00.500', '00:00:07.000'),
                ('100:00:00,500 --> 100:00:07,000',
                 '100:00:00.500', '100:00:07.000'),
                ('00:61:00,500 --> 00:61:07,000',
                 '01:01:00.500', '01:01:07.000'),
                ):
            captions = srt.parse(['1', timings, 'Caption #1'])
            self.assertEqual(len(captions), 1)
            self.assertEqual(captions[0].start, start)
            self.assertEqual(captions[0].end, end)

    def test_parse_skips_cue_with_incomplete_timings(self):
        for timings in ('00:00,500 --> 00:07,000',
                        '00:00:00 --> 00:00:07',
                        '00:00:00,500 --> 00:00:07,' + '9' * 5000):
            self.assertEqual(
                srt.parse(['1', timings, 'Caption #1']),
                []
                )

    def test_parse_skips_cues_without_text(self):
        captions = srt.parse(
            textwrap.dedent('''
            1
            00:00:00,500 --> 00:00:07,000

            2
            00:00:07,000 --> 00:00:11,890
            Caption #2
            ''').strip().split('\n')
            )
        self.assertEqual(len(captions), 1)
        self.assertEqual(captions[0].lines, ['Caption #2'])

    def test_write(self):
        out = io.StringIO()
        captions = [
            Caption(start='00:00:00.500',
                    end='00:00:07.000',
                    text='Caption #1'
                    ),
            Caption(start='00:00:07.000',
                    end='00:00:11.890',
                    text=['Caption #2 line 1',
                          'Caption #2 line 2'
                          ]
                    )
            ]
        captions[0].comments.append('Comment for the first caption')
        captions[1].comments.append('Comment for the second caption')

        srt.write(out, captions)

        out.seek(0)

        self.assertEqual(
            out.read(),
            textwrap.dedent('''
                1
                00:00:00,500 --> 00:00:07,000
                Caption #1

                2
                00:00:07,000 --> 00:00:11,890
                Caption #2 line 1
                Caption #2 line 2
            ''').strip()
            )

    def test_write_skips_whitespace_lines(self):
        out = io.StringIO()
        captions = [
            Caption(start='00:00:01.879',
                    end='00:00:05.660',
                    text=[' ', 'Caption #1']
                    ),
            Caption(start='00:00:05.660',
                    end='00:00:05.670',
                    text=['Caption #1', ' ']
                    )
            ]

        srt.write(out, captions)

        out.seek(0)

        self.assertEqual(
            out.read(),
            textwrap.dedent('''
                1
                00:00:01,879 --> 00:00:05,660
                Caption #1

                2
                00:00:05,660 --> 00:00:05,670
                Caption #1
            ''').strip()
            )
