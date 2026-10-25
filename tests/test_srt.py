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
            '1\n00:00:00,500 --> 00:00:07,000\nCaption #1'
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
            ''').strip()
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
            '<b>bold</b> <i>italic</i> <u>underline</u>'
            )


class TestCueColours(unittest.TestCase):

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
            srt._cue_colours(styles),
            {'magenta': (2, '#ff00ff'),
             'blue': (4, '#0000ff'),
             'navy': (4, '#0000ff')
             }
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

        self.assertEqual(srt._cue_colours(styles), {'green': (1, 'green')})

    def test_cue_colours_later_rule_overrides(self):
        styles = [
            Style('::cue(.title) { color: red; }'),
            Style('::cue(.title) { color: blue; }')
            ]

        self.assertEqual(srt._cue_colours(styles), {'title': (2, 'blue')})

    def test_cue_colours_last_declaration_applies(self):
        styles = [Style('::cue(.title) { color: red; COLOR : blue }')]

        self.assertEqual(srt._cue_colours(styles), {'title': (1, 'blue')})

    def test_cue_colours_removes_important(self):
        styles = [Style('::cue(.title) { color: red !important; }')]

        self.assertEqual(srt._cue_colours(styles), {'title': (1, 'red')})

    def test_cue_colours_ignores_values_not_valid_in_font_tag(self):
        styles = [
            Style('::cue(.a) { color: red; color: "blue" }'),
            Style('::cue(.b) { color: <x> }')
            ]

        self.assertEqual(srt._cue_colours(styles), {'a': (1, 'red')})

    def test_cue_colours_without_styles(self):
        self.assertEqual(srt._cue_colours([]), {})


class TestFormatCueText(unittest.TestCase):

    COLOURS = {
        'magenta': (1, '#ff00ff'),
        'blue': (2, '#0000ff')
        }

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
