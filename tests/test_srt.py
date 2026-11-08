import unittest
import io
import textwrap

from webvtt import srt
from webvtt.errors import MalformedFileError
from webvtt.models import Caption, Style


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

        # a cue without an index
        self.assertTrue(srt.SRTCueBlock.is_valid(textwrap.dedent('''
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

        self.assertTrue(srt.SRTCueBlock.is_valid(textwrap.dedent('''
            00:00:00,500 --> 00:00:07,000
            ''').strip().split('\n'))
            )

    def test_is_valid_index_with_whitespace(self):
        self.assertTrue(srt.SRTCueBlock.is_valid(
            ['1 ', '00:00:00,500 --> 00:00:07,000', 'Caption #1']
            ))

    def test_is_valid_non_ascii_digits(self):
        for index, timings in (
                ('\u0661', '00:00:00,500 --> 00:00:07,000'),
                ('\u00b2', '00:00:00,500 --> 00:00:07,000'),
                ('1', '00:00:00,\u0665\u0660\u0660 --> 00:00:07,000'),
                ):
            with self.subTest(index=index, timings=timings):
                self.assertFalse(srt.SRTCueBlock.is_valid(
                    [index, timings, 'Caption #1']
                    ))

    def test_is_valid_text_after_end_timestamp(self):
        self.assertTrue(srt.SRTCueBlock.is_valid(
            ['1', '00:00:00,500 --> 00:00:07,000 X1:100 X2:200', 'Caption #1']
            ))

    def test_from_lines_without_index(self):
        cue_block = srt.SRTCueBlock.from_lines(
            ['00:00:00,500 --> 00:00:07,000', 'Caption #1 line 1',
             'Caption #1 line 2']
            )
        self.assertIsNone(cue_block.index)
        self.assertEqual(cue_block.start, '00:00:00,500')
        self.assertEqual(cue_block.end, '00:00:07,000')
        self.assertEqual(
            cue_block.payload,
            ['Caption #1 line 1', 'Caption #1 line 2']
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

    def test_parse_timestamps(self):
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
            captions = srt.parse(['1', f'{value} --> {value}', 'Caption'])
            self.assertEqual(captions[0].start, expected)

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

    def test_parse_invalid_format_first_line_not_an_index(self):
        self.assertRaises(
            MalformedFileError,
            srt.parse,
            ['Caption #1', '00:00:00,500 --> 00:00:07,000', 'Caption #2']
            )

    def test_parse_invalid_format_only_blank_lines(self):
        for lines in ([], [''], ['', ' ', '']):
            with self.subTest(lines=lines):
                with self.assertRaises(MalformedFileError):
                    srt.parse(lines)

    def test_parse_leading_blank_lines(self):
        for blank_lines in ([''], ['', ''], [' ', '\t']):
            with self.subTest(blank_lines=blank_lines):
                captions = srt.parse(
                    blank_lines +
                    ['1', '00:00:01,000 --> 00:00:02,000', 'Caption #1']
                    )

                self.assertEqual(
                    [(c.start, c.text) for c in captions],
                    [('00:00:01.000', 'Caption #1')]
                    )

    def test_parse_cue_without_text(self):
        self.assertEqual(
            srt.parse(['1', '00:00:01,000 --> 00:00:02,000']),
            []
            )

    def test_parse_first_cue_without_text(self):
        captions = srt.parse(
            textwrap.dedent('''
            1
            00:00:01,000 --> 00:00:02,000

            2
            00:00:03,000 --> 00:00:04,000
            Caption #2
            ''').strip().split('\n')
            )

        self.assertEqual(
            [(c.start, c.text) for c in captions],
            [('00:00:03.000', 'Caption #2')]
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

    def test_parse_captions_with_digits_only_line_after_empty_line(self):
        captions = srt.parse(
            textwrap.dedent('''
            1
            00:00:00,500 --> 00:00:07,000
            The year was

            1984

            and then

            2
            00:00:07,000 --> 00:00:11,890
            Caption #2
            ''').strip().split('\n')
            )
        self.assertEqual(len(captions), 2)
        self.assertEqual(captions[0].lines,
                         ['The year was', '1984', 'and then'])
        self.assertEqual(captions[1].lines, ['Caption #2'])

    def test_parse_captions_with_digits_only_line_starting_a_block(self):
        captions = srt.parse(
            textwrap.dedent('''
            1
            00:00:00,500 --> 00:00:07,000
            Countdown

            3
            2
            1

            2
            00:00:07,000 --> 00:00:11,890
            Caption #2
            ''').strip().split('\n')
            )
        self.assertEqual(len(captions), 2)
        self.assertEqual(captions[0].lines, ['Countdown', '3', '2', '1'])
        self.assertEqual(captions[1].lines, ['Caption #2'])

    def test_parse_captions_with_empty_line_after_index(self):
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
        self.assertEqual(captions[1].start, '00:00:07.000')

    def test_parse_captions_with_digits_only_line_at_the_end(self):
        # a number at the end is more likely to be text, such as a year,
        # than the index of a cue that is not there
        captions = srt.parse(
            textwrap.dedent('''
            1
            00:00:00,500 --> 00:00:07,000
            Copyright

            2024
            ''').strip().split('\n')
            )
        self.assertEqual(len(captions), 1)
        self.assertEqual(captions[0].lines, ['Copyright', '2024'])

    def test_parse_captions_with_digits_only_line_followed_by_text(self):
        captions = srt.parse(
            textwrap.dedent('''
            1
            00:00:00,500 --> 00:00:07,000
            Caption #1

            2
            More text

            3
            00:00:07,000 --> 00:00:11,890
            Caption #3
            ''').strip().split('\n')
            )
        self.assertEqual(len(captions), 2)
        self.assertEqual(captions[0].lines,
                         ['Caption #1', '2', 'More text'])
        self.assertEqual(captions[1].lines, ['Caption #3'])

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

    def test_parse_captions_with_whitespace_around_first_index(self):
        captions = srt.parse(
            [' 1 ',
             '00:00:00,500 --> 00:00:07,000',
             'Caption #1',
             '',
             '2',
             '00:00:07,000 --> 00:00:11,890',
             'Caption #2'
             ]
            )
        self.assertEqual(len(captions), 2)
        self.assertEqual(captions[0].lines, ['Caption #1'])
        self.assertEqual(captions[1].lines, ['Caption #2'])

    def test_parse_cue_without_index(self):
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
        self.assertEqual(
            [caption.lines for caption in captions],
            [['Caption #1'], ['Caption #2'], ['Caption #3']]
            )
        self.assertEqual(captions[1].start, '00:00:07.000')

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
                        '00:00:00 --> 00:00:07'):
            self.assertEqual(
                srt.parse(['1', timings, 'Caption #1']),
                []
                )

    def test_parse_cue_with_too_many_digits(self):
        captions = srt.parse(
            ['1', '00:00:00,500 --> 00:00:07,000', 'Caption #1', '',
             '2', '00:00:07,000 --> 00:00:11,' + '9' * 5000, 'Caption #2']
            )
        self.assertEqual(len(captions), 1)
        self.assertEqual(captions[0].text, 'Caption #1')

    def test_parse_timings_with_leading_zeros(self):
        captions = srt.parse(
            ['1', '00:00:00,' + '0' * 30 + '500 --> 00:00:07,000',
             'Caption #1']
            )
        self.assertEqual(len(captions), 1)
        self.assertEqual(captions[0].start, '00:00:00.500')

    def test_parse_skips_cue_with_too_many_digits_hours(self):
        captions = srt.parse(
            ['1', '00:00:00,500 --> 00:00:07,000', 'Caption #1', '',
             '2', '99999999999:00:07,000 --> 99999999999:00:11,890',
             'Caption #2']
            )
        self.assertEqual(len(captions), 1)
        self.assertEqual(captions[0].text, 'Caption #1')

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
            ''').strip() + '\n'
            )

    def test_write_no_captions(self):
        out = io.StringIO()

        srt.write(out, [])

        self.assertEqual(out.getvalue(), '')

    def test_write_keeps_trailing_spaces_of_the_last_caption(self):
        out = io.StringIO()
        captions = [
            Caption(start='00:00:01.000', end='00:00:02.000', text='a  '),
            Caption(start='00:00:02.000', end='00:00:03.000', text='b  ')
            ]

        srt.write(out, captions)

        self.assertEqual(
            out.getvalue(),
            '1\n00:00:01,000 --> 00:00:02,000\na  \n\n'
            '2\n00:00:02,000 --> 00:00:03,000\nb  \n'
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
            ''').strip() + '\n'
            )

    def test_write_leaves_out_captions_without_text(self):
        captions = [
            Caption('00:00:00.000', '00:00:01.000', ' '),
            Caption('00:00:01.000', '00:00:02.000', 'b'),
            Caption('00:00:02.000', '00:00:03.000', ''),
            Caption('00:00:03.000', '00:00:04.000', ['', '  ']),
            Caption('00:00:04.000', '00:00:05.000', 'c'),
            Caption('00:00:05.000', '00:00:06.000', '<v Bob></v>'),
            Caption('00:00:06.000', '00:00:07.000', ['<i> </i>', '<b></b>']),
            Caption('00:00:07.000', '00:00:08.000', '<c.red> </c>'),
            ]

        for styles in (None, [], [Style('::cue(.red) { color: red; }')]):
            with self.subTest(styles=styles):
                out = io.StringIO()

                srt.write(out, captions, styles)

                self.assertEqual(
                    out.getvalue(),
                    '1\n00:00:01,000 --> 00:00:02,000\nb\n\n'
                    '2\n00:00:04,000 --> 00:00:05,000\nc\n'
                    )

    def test_write_only_captions_without_text(self):
        out = io.StringIO()

        srt.write(out, [Caption('00:00:00.000', '00:00:01.000', ' ')])

        self.assertEqual(out.getvalue(), '')

    def test_write_without_styles_removes_cue_tags(self):
        out = io.StringIO()
        captions = [
            Caption(start='00:00:00.500',
                    end='00:00:07.000',
                    text='<c.yellow><b>Caption</b> #1</c>'
                    )
            ]

        srt.write(out, captions)

        self.assertEqual(
            out.getvalue(),
            '1\n00:00:00,500 --> 00:00:07,000\nCaption #1\n'
            )

    def test_write_with_styles_keeps_formatting(self):
        out = io.StringIO()
        captions = [
            Caption(start='00:00:00.500',
                    end='00:00:07.000',
                    text=['<c.yellow><b>Caption</b> #1',
                          'line 2</c>'
                          ]
                    ),
            Caption(start='00:00:07.000',
                    end='00:00:11.890',
                    text='<v Roger>Caption #2'
                    )
            ]
        styles = [Style('::cue(.yellow) {\n  color: yellow;\n}')]

        srt.write(out, captions, styles)

        self.assertEqual(
            out.getvalue(),
            textwrap.dedent('''
                1
                00:00:00,500 --> 00:00:07,000
                <font color="yellow"><b>Caption</b> #1
                line 2</font>

                2
                00:00:07,000 --> 00:00:11,890
                Caption #2
            ''').strip() + '\n'
            )

    def test_write_with_empty_styles_keeps_bold_italic_underline(self):
        out = io.StringIO()
        captions = [
            Caption(start='00:00:00.500',
                    end='00:00:07.000',
                    text='<b>bold</b> <i>italic</i> <u>underline</u>'
                    )
            ]

        srt.write(out, captions, [])

        self.assertEqual(
            out.getvalue(),
            '1\n00:00:00,500 --> 00:00:07,000\n'
            '<b>bold</b> <i>italic</i> <u>underline</u>\n'
            )


class TestCueColours(unittest.TestCase):

    def colours(self, styles):
        return [(rule.name, set(rule.classes), rule.priority, rule.colour)
                for rule in srt._cue_colours(styles)]

    def test_cue_colours(self):
        styles = [
            Style(textwrap.dedent('''
                ::cue {
                  color: papayawhip;
                }
                ::cue(.magenta) {
                  color: #ff00ff;
                }
                ::cue(.bg_black) {
                  background-color: black;
                }
                ::cue(b) {
                  color: peachpuff;
                }
                ''').strip()),
            Style('::cue(.blue), ::cue(.navy) { color: #0000ff; }')
            ]

        self.assertEqual(
            self.colours(styles),
            [(None, {'magenta'}, (1, 0, 2), '#ff00ff'),
             ('b', set(), (0, 1, 3), 'peachpuff'),
             (None, {'blue'}, (1, 0, 4), '#0000ff'),
             (None, {'navy'}, (1, 0, 4), '#0000ff')]
            )

    def test_cue_colours_ignores_comments(self):
        styles = [
            Style(textwrap.dedent('''
                /* ::cue(.red) { color: red; } */
                ::cue(.green) {
                  /* color: lime; */
                  color: green;
                }
                ''').strip())
            ]

        self.assertEqual(self.colours(styles),
                         [(None, {'green'}, (1, 0, 1), 'green')])

    def test_cue_colours_later_rule_overrides(self):
        styles = [
            Style('::cue(.title) { color: red; }'),
            Style('::cue(.title) { color: blue; }')
            ]

        self.assertEqual(
            [rule[3] for rule in self.colours(styles)], ['red', 'blue']
            )
        self.assertEqual(
            srt._format_cue_text('<c.title>x</c>', srt._cue_colours(styles)),
            '<font color="blue">x</font>'
            )

    def test_cue_colours_last_declaration_applies(self):
        styles = [Style('::cue(.title) { color: red; COLOR : blue }')]

        self.assertEqual(self.colours(styles),
                         [(None, {'title'}, (1, 0, 1), 'blue')])

    def test_cue_colours_removes_important(self):
        styles = [Style('::cue(.title) { color: red !important; }')]

        self.assertEqual(self.colours(styles),
                         [(None, {'title'}, (1, 0, 1), 'red')])

    def test_cue_colours_ignores_values_not_valid_in_font_tag(self):
        styles = [
            Style('::cue(.a) { color: red; color: "blue" }'),
            Style('::cue(.b) { color: <x> }')
            ]

        self.assertEqual(self.colours(styles),
                         [(None, {'a'}, (1, 0, 1), 'red')])

    def test_cue_colours_without_styles(self):
        self.assertEqual(srt._cue_colours([]), [])


class TestFormatCueText(unittest.TestCase):

    COLOURS = srt._cue_colours([Style(
        '::cue(.magenta) { color: #ff00ff; } ::cue(.blue) { color: #0000ff; }'
        )])

    def test_text_without_tags(self):
        self.assertEqual(
            srt._format_cue_text('2 &lt; 3', self.COLOURS),
            '2 &lt; 3'
            )

    def test_nested_tags_with_colours(self):
        self.assertEqual(
            srt._format_cue_text(
                '<c.magenta.bg_black><i.blue>Some italic</i> and normal</c>',
                self.COLOURS
                ),
            '<font color="#ff00ff"><i><font color="#0000ff">Some italic'
            '</font></i> and normal</font>'
            )

    def test_class_of_later_rule_applies(self):
        self.assertEqual(
            srt._format_cue_text('<c.blue.magenta>text</c>', self.COLOURS),
            '<font color="#0000ff">text</font>'
            )

    def test_removes_tags_not_supported_by_srt(self):
        self.assertEqual(
            srt._format_cue_text(
                '<v.loud Esme>Hi <lang en>there</lang>, '
                '<ruby>漢<rt>kan</rt></ruby> <c.unknown>you</c></v>',
                self.COLOURS
                ),
            'Hi there, 漢kan you'
            )

    def test_removes_timestamp_tags(self):
        self.assertEqual(
            srt._format_cue_text(
                'Like a <00:19.000>big-a <00:00:19.500><b>pizza</b>',
                self.COLOURS
                ),
            'Like a big-a <b>pizza</b>'
            )

    def test_closes_tags_left_open(self):
        self.assertEqual(
            srt._format_cue_text('<c.magenta><b>open', self.COLOURS),
            '<font color="#ff00ff"><b>open</b></font>'
            )

    def test_end_tag_closes_inner_tags(self):
        self.assertEqual(
            srt._format_cue_text('<u><i>both</u> neither</i>', self.COLOURS),
            '<u><i>both</i></u> neither'
            )

    def test_ignores_end_tag_without_start_tag(self):
        self.assertEqual(
            srt._format_cue_text('<b>bold</i></b>', self.COLOURS),
            '<b>bold</b>'
            )

    def test_tags_across_lines(self):
        self.assertEqual(
            srt._format_cue_text('<i.blue>line 1\nline 2</i>', self.COLOURS),
            '<i><font color="#0000ff">line 1\nline 2</font></i>'
            )

    def test_tags_are_found_in_each_line(self):
        self.assertEqual(
            srt._format_cue_text('if a < b\nthen b > a', self.COLOURS),
            'if a < b\nthen b > a'
            )

    def test_keeps_font_tags(self):
        self.assertEqual(
            srt._format_cue_text(
                '<font color="red">x</font> <b>y</b> <font color=blue>z',
                self.COLOURS
                ),
            '<font color="red">x</font> <b>y</b> <font color=blue>z</font>'
            )

    def test_less_than_without_greater_than_is_text(self):
        self.assertEqual(
            srt._format_cue_text('<b>bold</b> 2 < 3 <i', self.COLOURS),
            '<b>bold</b> 2 < 3 <i'
            )


class TestStripCSSComments(unittest.TestCase):

    def test_strip_css_comments(self):
        self.assertEqual(
            srt._strip_css_comments('a /* one */b/**/ c /* two\n*/'),
            'a b c '
            )

    def test_comment_without_end_runs_to_the_end(self):
        self.assertEqual(
            srt._strip_css_comments('a /* b */ c /* d'),
            'a  c '
            )

    def test_comment_end_is_not_in_comment_start(self):
        self.assertEqual(srt._strip_css_comments('a /*/ b */ c'), 'a  c')


class TestReadMarkup(unittest.TestCase):

    def parse(self, *texts):
        lines = []
        for index, text in enumerate(texts, 1):
            lines.extend([str(index),
                          f'00:00:0{index},000 --> 00:00:0{index},500',
                          *text.split('\n'),
                          ''])
        issues = []
        styles = []
        captions = srt.parse(lines, issues, styles)
        return captions, styles, issues

    def test_font_colour_to_class(self):
        captions, styles, _ = self.parse(
            '<font color="#FF0000">red</font> <font color=\'blue\'>blue</font>',
            '<FONT COLOR=#ff0000>red <b>again</b></FONT>'
            )

        self.assertEqual(
            [c.raw_text for c in captions],
            ['<c.color-ff0000>red</c> <c.color-blue>blue</c>',
             '<c.color-ff0000>red <b>again</b></c>']
            )
        self.assertEqual(styles, [Style([
            '::cue(.color-ff0000) {', '  color: #ff0000;', '}',
            '::cue(.color-blue) {', '  color: blue;', '}'
            ])])

    def test_no_style_without_colours(self):
        captions, styles, _ = self.parse('<b>bold</b>', '<font face="x">y')

        self.assertEqual([c.raw_text for c in captions], ['<b>bold</b>', 'y'])
        self.assertEqual(styles, [])

    def test_styles_none(self):
        captions = srt.parse(
            ['1', '00:00:01,000 --> 00:00:02,000', '<font color=red>x</font>']
            )

        self.assertEqual(captions[0].raw_text, '<c.color-red>x</c>')

    def test_other_fonts_and_attributes_removed(self):
        captions, _, _ = self.parse(
            '<font face="Arial" size="20">a</font> '
            '<font face="Arial" color="red" size=2>b</font>'
            )

        self.assertEqual(captions[0].raw_text, 'a <c.color-red>b</c>')

    def test_nested_fonts(self):
        captions, _, _ = self.parse(
            '<font color=red>a <font size=2>b <font color=blue>c</font> d'
            '</font> e</font> f</font>'
            )

        self.assertEqual(
            captions[0].raw_text,
            '<c.color-red>a b <c.color-blue>c</c> d e</c> f'
            )

    def test_font_across_lines(self):
        captions, _, _ = self.parse('<font color=red>line 1\nline 2</font>')

        self.assertEqual(captions[0].lines,
                         ['<c.color-red>line 1', 'line 2</c>'])

    def test_colours_not_written_in_style(self):
        captions, styles, _ = self.parse(
            '<font color="red;}x{">a</font> <font color="">b</font> '
            '<font color="#">c</font> <font color="a<b">d</font>'
            )

        self.assertEqual(captions[0].raw_text, 'a b c d')
        self.assertEqual(styles, [])

    def test_colour_functions(self):
        captions, styles, _ = self.parse(
            '<font color="rgb(255, 0, 0)">a</font>'
            )

        self.assertEqual(captions[0].raw_text,
                         '<c.color-rgb-255-0-0>a</c>')
        self.assertEqual(styles[0].lines[1], '  color: rgb(255, 0, 0);')

    def test_class_names_of_colours_kept_apart(self):
        captions, styles, _ = self.parse(
            '<font color="#ff0000">a</font> <font color="ff0000">b</font>'
            )

        self.assertEqual(
            captions[0].raw_text,
            '<c.color-ff0000>a</c> <c.color-ff0000-2>b</c>'
            )
        self.assertEqual(len(styles[0].lines), 6)

    def test_font_word_in_text_or_other_tags(self):
        captions, _, _ = self.parse('<fontx>a</fontx> font color=red 2 < 3')

        self.assertEqual(captions[0].raw_text,
                         '<fontx>a</fontx> font color=red 2 < 3')

    def test_bgcolor_is_not_color(self):
        captions, _, _ = self.parse('<font bgcolor="red">a</font>')

        self.assertEqual(captions[0].raw_text, 'a')

    def test_position_tags(self):
        expected = {
            1: 'align:left', 2: '', 3: 'align:right',
            4: 'line:50%,center align:left', 5: 'line:50%,center',
            6: 'line:50%,center align:right',
            7: 'line:0 align:left', 8: 'line:0', 9: 'line:0 align:right',
            }
        for number in range(1, 10):
            with self.subTest(number=number):
                captions, _, _ = self.parse(f'{{\\an{number}}}Text')

                self.assertEqual(captions[0].raw_text, 'Text')
                self.assertEqual(str(captions[0].settings),
                                 expected[number])

    def test_first_position_tag_applies(self):
        captions, _, _ = self.parse('{\\an8}a {\\an1}b\nc{\\an3}')

        self.assertEqual(captions[0].lines, ['a b', 'c'])
        self.assertEqual(captions[0].settings.line, '0')
        self.assertIsNone(captions[0].settings.align)

    def test_other_tags_in_braces_kept(self):
        captions, _, _ = self.parse('{\\an0}a {\\i1}b {\\an10}')

        self.assertEqual(captions[0].raw_text, '{\\an0}a {\\i1}b {\\an10}')
        self.assertEqual(str(captions[0].settings), '')

    def test_lines_left_empty_removed(self):
        captions, _, _ = self.parse(
            '{\\an8}\n<font color=red>\ntext\n </font>\n</font>'
            )

        # the unmatched end tag leaves its line empty
        self.assertEqual(captions[0].lines,
                         ['<c.color-red>', 'text', ' </c>'])

    def test_cue_left_without_text_skipped(self):
        captions, _, issues = self.parse('{\\an8}', 'text')

        self.assertEqual([c.text for c in captions], ['text'])
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].line, 1)
        self.assertTrue(issues[0].message.startswith('Cue without text'))


class TestWritePosition(unittest.TestCase):

    def write(self, settings):
        output = io.StringIO()
        srt.write(output, [Caption('00:00:01.000', '00:00:02.000', 'Text',
                                   settings=settings)])
        return output.getvalue().split('\n')[2]

    def test_positions(self):
        for settings, line in (
                ('', 'Text'),
                ('line:-1', 'Text'),
                ('align:center', 'Text'),
                ('align:left', '{\\an1}Text'),
                ('align:right', '{\\an3}Text'),
                ('line:50%,center align:left', '{\\an4}Text'),
                ('line:50%', '{\\an5}Text'),
                ('line:60% align:right', '{\\an6}Text'),
                ('line:0 align:left', '{\\an7}Text'),
                ('line:0', '{\\an8}Text'),
                ('line:3', '{\\an8}Text'),
                ('line:10%', '{\\an8}Text'),
                ('line:0 align:right', '{\\an9}Text'),
                ('line:90%', 'Text'),
                ('line:-2 align:right', '{\\an3}Text'),
                ('align:start', 'Text'),
                ('line:0 align:end', '{\\an8}Text'),
                ('line:0 vertical:rl', 'Text'),
                ('position:10% size:50%', 'Text')):
            with self.subTest(settings=settings):
                self.assertEqual(self.write(settings), line)

    def test_position_with_formatting(self):
        output = io.StringIO()
        srt.write(output,
                  [Caption('00:00:01.000', '00:00:02.000',
                           '\n<b>bold</b>\nline 2', settings='line:0')],
                  styles=[])

        self.assertEqual(output.getvalue().split('\n')[2:4],
                         ['{\\an8}<b>bold</b>', 'line 2'])

    def test_round_trip(self):
        for number in range(1, 10):
            with self.subTest(number=number):
                tag = f'{{\\an{number}}}' if number != 2 else ''
                content = f'1\n00:00:01,000 --> 00:00:02,000\n{tag}Text\n'
                output = io.StringIO()
                srt.write(output, srt.parse(content.split('\n')))

                self.assertEqual(output.getvalue(), content)


class TestMarkupReviewCases(unittest.TestCase):

    def test_colours_with_unbalanced_parentheses_dropped(self):
        styles = []
        captions = srt.parse(
            ['1', '00:00:01,000 --> 00:00:02,000',
             '<font color="rgb(1, 2">a</font> <font color="red)">b</font> '
             '<font color="dark red">c</font> '
             '<font color="rgba(1 2 3 / 50%)">d</font>'],
            styles=styles
            )

        self.assertEqual(captions[0].raw_text,
                         'a b c <c.color-rgba-1-2-3-50>d</c>')
        self.assertEqual(styles[0].lines[1], '  color: rgba(1 2 3 / 50%);')

    def test_text_with_position_tag_not_written_twice(self):
        output = io.StringIO()
        srt.write(output, [Caption('00:00:01.000', '00:00:02.000',
                                   '{\\an8}Text', settings='line:0')])

        self.assertEqual(output.getvalue().split('\n')[2], '{\\an8}Text')


class TestCueSelectors(unittest.TestCase):

    def format(self, css, text):
        return srt._format_cue_text(text, srt._cue_colours([Style(css)]))

    def test_class_names_with_any_character(self):
        css = textwrap.dedent(r'''
            ::cue(.c\+1) { color: red; }
            ::cue(.\31 st) { color: blue; }
            ::cue(.naïve) { color: green; }
            ::cue(.a\.b) { color: gray; }
            ::cue(.x\,y) { color: navy; }
            ::cue(.\1F600) { color: gold; }
            ''')

        for text, colour in (('<c.c+1>t</c>', 'red'),
                             ('<c.1st>t</c>', 'blue'),
                             ('<c.naïve>t</c>', 'green'),
                             ('<c.x,y>t</c>', 'navy'),
                             ('<c.😀>t</c>', 'gold')):
            with self.subTest(text=text):
                self.assertEqual(self.format(css, text),
                                 f'<font color="{colour}">t</font>')

        # a class cannot have a dot, which separates classes in cue tags
        self.assertEqual(self.format(css, '<c.a.b>t</c>'), 't')

    def test_invalid_escapes_replaced(self):
        self.assertEqual(srt._css_unescape(r'\0 a\D800 b\110000 c'),
                         '�a�b�c')

    def test_type_and_compound_selectors(self):
        css = textwrap.dedent('''
            ::cue(.a.b) { color: red; }
            ::cue(c.g) { color: green; }
            ::cue(B) { color: blue; }
            ::cue(v.loud) { color: purple; }
            ''')

        for text, expected in (
                ('<c.a>t</c>', 't'),
                ('<c.b.a.z>t</c>', '<font color="red">t</font>'),
                ('<c.g>t</c>', '<font color="green">t</font>'),
                ('<i.g>t</i>', '<i>t</i>'),
                ('<b>t</b>', '<b><font color="blue">t</font></b>'),
                ('<v.loud Joe>t</v>', '<font color="purple">t</font>'),
                ('<v Joe>t</v>', 't')):
            with self.subTest(text=text):
                self.assertEqual(self.format(css, text), expected)

    def test_selectors_not_read(self):
        css = textwrap.dedent('''
            ::cue { color: red; }
            ::cue(#id) { color: red; }
            ::cue(c > b) { color: red; }
            ::cue([voice="Joe"]) { color: red; }
            ::cue(.a:past) { color: red; }
            ::cue() { color: red; }
            .a { color: red; }
            ''')

        self.assertEqual(srt._cue_colours([Style(css)]), [])

    def test_specificity(self):
        for css, text, colour in (
                # more classes win over a later rule
                ('::cue(.a.b) { color: red; } ::cue(.a) { color: blue; }',
                 '<c.a.b>t</c>', 'red'),
                # a class wins over a type
                ('::cue(.a) { color: red; } ::cue(c) { color: blue; }',
                 '<c.a>t</c>', 'red'),
                # a type with the class wins over the class
                ('::cue(c.a) { color: red; } ::cue(.a) { color: blue; }',
                 '<c.a>t</c>', 'red'),
                # with the same specificity, the later rule applies
                ('::cue(.a) { color: red; } ::cue(.b) { color: blue; }',
                 '<c.b.a>t</c>', 'blue')):
            with self.subTest(css=css):
                self.assertEqual(self.format(css, text),
                                 f'<font color="{colour}">t</font>')

    def test_selector_lists_with_spaces(self):
        self.assertEqual(
            self.format('::cue( .a ) , ::cue(i) { color: red; }',
                        '<c.a>x</c> <i>y</i>'),
            '<font color="red">x</font> <i><font color="red">y</font></i>'
            )

    def test_selector_not_matching_fails_fast(self):
        # each character matched one way, or this backtracks for hours
        for selector in ('::cue(.' + 'é' * 200 + ' x)',
                         '::cue(.' + '\\11' * 200 + '!)',
                         '::cue(.' + 'a' * 200 + '\\'):
            with self.subTest(selector=selector[:12]):
                self.assertEqual(
                    srt._cue_colours([Style(selector + ' { color: red }')]),
                    []
                    )

    def test_hex_escape_takes_six_digits(self):
        self.assertEqual(
            self.format(r'::cue(.\00004111) { color: red; }', '<c.A11>t</c>'),
            '<font color="red">t</font>'
            )
