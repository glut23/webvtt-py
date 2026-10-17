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

        self.assertFalse(srt.SRTCueBlock.is_valid(textwrap.dedent('''
            1
            00:00:00.500 --> 00:00:07.000
            Caption #1
            ''').strip().split('\n'))
            )

        self.assertFalse(srt.SRTCueBlock.is_valid(textwrap.dedent('''
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
