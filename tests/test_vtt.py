import unittest
import textwrap
import io

from webvtt import vtt
from webvtt.errors import MalformedFileError, MalformedCaptionError
from webvtt.models import Caption, Style


class TestWebVTTCueBlock(unittest.TestCase):

    def test_is_valid(self):
        self.assertTrue(
            vtt.WebVTTCueBlock.is_valid(textwrap.dedent('''
            00:00:00.500 --> 00:00:07.000
            Caption #1
            ''').strip().split('\n'))
            )

        self.assertTrue(
            vtt.WebVTTCueBlock.is_valid(textwrap.dedent('''
            00:00:00.500 --> 00:00:07.000
            Caption #1 line 1
            Caption #1 line 2
            ''').strip().split('\n'))
            )

        self.assertTrue(
            vtt.WebVTTCueBlock.is_valid(textwrap.dedent('''
            identifier
            00:00:00.500 --> 00:00:07.000
            Caption #1
            ''').strip().split('\n'))
            )

        self.assertTrue(
            vtt.WebVTTCueBlock.is_valid(textwrap.dedent('''
            identifier
            00:00:00.500 --> 00:00:07.000
            Caption #1 line 1
            Caption #1 line 2
            ''').strip().split('\n'))
            )

        self.assertFalse(
            vtt.WebVTTCueBlock.is_valid(textwrap.dedent('''
            00:00:00.500 00:00:07.000
            Caption #1 line 1
            ''').strip().split('\n'))
            )

        self.assertTrue(
            vtt.WebVTTCueBlock.is_valid(textwrap.dedent('''
            00:00:00.500 --> 00:00:07.000
            ''').strip().split('\n'))
            )

        self.assertTrue(
            vtt.WebVTTCueBlock.is_valid(textwrap.dedent('''
            identifier
            00:00:00.500 --> 00:00:07.000
            ''').strip().split('\n'))
            )

        for timings in (
                '00:00:00,500 --> 00:00:07.000',
                '00:00:00:500 --> 00:00:07.000',
                '00:00:00.-500 --> 00:00:07.000',
                '00:00:00.500 --> 00:00:07,000',
                ):
            self.assertFalse(
                vtt.WebVTTCueBlock.is_valid([timings, 'Caption #1'])
                )

    def test_is_valid_non_padded_timestamps(self):
        lines = ['0:0:13.540 --> 0:0:17.85', 'Caption #1']
        self.assertTrue(vtt.WebVTTCueBlock.is_valid(lines))
        self.assertFalse(vtt.WebVTTCueBlock.is_valid(lines, strict=True))
        self.assertTrue(
            vtt.WebVTTCueBlock.is_valid(
                ['00:13.540 --> 00:00:17.850', 'Caption #1'],
                strict=True
                )
            )

    def test_is_valid_strict_hours(self):
        for timings in (
                '0:00:13.540 --> 00:00:17.850',
                '00:00:13.540 --> 0:00:17.850'
                ):
            self.assertTrue(vtt.WebVTTCueBlock.is_valid([timings]))
            self.assertFalse(
                vtt.WebVTTCueBlock.is_valid([timings], strict=True)
                )
        self.assertTrue(
            vtt.WebVTTCueBlock.is_valid(
                ['100:00:13.540 --> 100:00:17.850'],
                strict=True
                )
            )

    def test_is_valid_strict_end_timestamp_boundary(self):
        for timings in (
                '00:00:13.540 --> 00:00:17.8505',
                '00:00:13.540 --> 00:00:17.850abc'
                ):
            self.assertFalse(
                vtt.WebVTTCueBlock.is_valid([timings], strict=True)
                )
        self.assertTrue(
            vtt.WebVTTCueBlock.is_valid(
                ['00:00:13.540 --> 00:00:17.850 align:start'],
                strict=True
                )
            )

    def test_from_lines(self):
        cue_block = vtt.WebVTTCueBlock.from_lines(textwrap.dedent('''
            identifier
            00:00:00.500 --> 00:00:07.000
            Caption #1 line 1
            Caption #1 line 2
            ''').strip().split('\n')
            )
        self.assertEqual(cue_block.identifier, 'identifier')
        self.assertEqual(cue_block.start, '00:00:00.500')
        self.assertEqual(cue_block.end, '00:00:07.000')
        self.assertListEqual(
            cue_block.payload,
            ['Caption #1 line 1', 'Caption #1 line 2']
            )


class TestWebVTTCommentBlock(unittest.TestCase):

    def test_is_valid(self):
        self.assertTrue(
            vtt.WebVTTCommentBlock.is_valid(textwrap.dedent('''
            NOTE This is a one line comment
            ''').strip().split('\n'))
            )

        self.assertTrue(
            vtt.WebVTTCommentBlock.is_valid(textwrap.dedent('''
            NOTE
            This is a another one line comment
            ''').strip().split('\n'))
            )

        self.assertTrue(
            vtt.WebVTTCommentBlock.is_valid(textwrap.dedent('''
            NOTE
            This is a multi-line comment
            taking two lines
            ''').strip().split('\n'))
            )

        self.assertFalse(
            vtt.WebVTTCommentBlock.is_valid(textwrap.dedent('''
            This is not a comment
            ''').strip().split('\n'))
            )

        self.assertFalse(
            vtt.WebVTTCommentBlock.is_valid(textwrap.dedent('''
            # This is not a comment
            ''').strip().split('\n'))
            )

        self.assertFalse(
            vtt.WebVTTCommentBlock.is_valid(textwrap.dedent('''
            // This is not a comment
            ''').strip().split('\n'))
            )

    def test_from_lines(self):
        comment = vtt.WebVTTCommentBlock.from_lines(textwrap.dedent('''
            NOTE This is a one line comment
            ''').strip().split('\n')
            )
        self.assertEqual(comment.text, 'This is a one line comment')

        comment = vtt.WebVTTCommentBlock.from_lines(textwrap.dedent('''
            NOTE
            This is a multi-line comment
            taking two lines
            ''').strip().split('\n')
            )
        self.assertEqual(
            comment.text,
            'This is a multi-line comment\ntaking two lines'
            )


    def test_format_lines(self):
        for text, lines in (
            ('', ['NOTE ']),
            ('comment', ['NOTE comment']),
            ('comment\n', ['NOTE comment']),
            ('comment\u2028still comment',
             ['NOTE comment\u2028still comment']),
            ('line 1\rline 2\r\nline 3',
             ['NOTE', 'line 1', 'line 2', 'line 3']),
        ):
            with self.subTest(text=text):
                self.assertListEqual(
                    vtt.WebVTTCommentBlock.format_lines(text),
                    lines
                    )


class TestWebVTTStyleBlock(unittest.TestCase):

    def test_is_valid(self):
        self.assertTrue(
            vtt.WebVTTStyleBlock.is_valid(textwrap.dedent('''
            STYLE
            ::cue {
              background-image: linear-gradient(to bottom, dimgray, lightgray);
              color: papayawhip;
            }
            ''').strip().split('\n'))
            )

        self.assertTrue(
            vtt.WebVTTStyleBlock.is_valid(textwrap.dedent('''
            STYLE
            ::cue {
              background-image: linear-gradient(to bottom, dimgray, lightgray);
              color: papayawhip;
            }
            ::cue(b) {
              color: peachpuff;
            }
            ''').strip().split('\n'))
            )

        self.assertFalse(
            vtt.WebVTTStyleBlock.is_valid(textwrap.dedent('''
            STYLE
            ::cue {
              background-image: linear-gradient(to bottom, dimgray, lightgray);
              color: papayawhip;
            }

            ::cue(b) {
              color: peachpuff;
            }
            ''').strip().split('\n'))
            )

        self.assertFalse(
            vtt.WebVTTStyleBlock.is_valid(textwrap.dedent('''
            STYLE
            ::cue--> {
              background-image: linear-gradient(to bottom, dimgray, lightgray);
              color: papayawhip;
            }
            ''').strip().split('\n'))
            )

        self.assertFalse(
            vtt.WebVTTStyleBlock.is_valid(textwrap.dedent('''
            ::cue {
              background-image: linear-gradient(to bottom, dimgray, lightgray);
              color: papayawhip;
            }
            ''').strip().split('\n'))
            )

    def test_from_lines(self):
        style = vtt.WebVTTStyleBlock.from_lines(textwrap.dedent('''
            STYLE
            ::cue {
              background-image: linear-gradient(to bottom, dimgray, lightgray);
              color: papayawhip;
            }
            ::cue(b) {
              color: peachpuff;
            }
            ''').strip().split('\n')
            )
        self.assertEqual(
            style.text,
            textwrap.dedent('''
            ::cue {
              background-image: linear-gradient(to bottom, dimgray, lightgray);
              color: papayawhip;
            }
            ::cue(b) {
              color: peachpuff;
            }
            ''').strip()
            )


class TestVTTModule(unittest.TestCase):

    def test_parse_invalid_format(self):
        self.assertRaises(
            MalformedFileError,
            vtt.parse,
            textwrap.dedent('''
                00:00:00.500 --> 00:00:07.000
                Caption text #1

                00:00:07.000 --> 00:00:11.890
                Caption text #2
                ''').strip().split('\n')
            )

    def test_parse_captions(self):
        output = vtt.parse(
            textwrap.dedent('''
            WEBVTT

            00:00:00.500 --> 00:00:07.000
            Caption text #1

            00:00:07.000 --> 00:00:11.890
            Caption text #2 line 1
            Caption text #2 line 2
            ''').strip().split('\n')
            )
        captions = output.captions
        styles = output.styles
        self.assertEqual(len(captions), 2)
        self.assertEqual(len(styles), 0)
        self.assertIsInstance(captions[0], Caption)
        self.assertIsInstance(captions[1], Caption)
        self.assertEqual(
            str(captions[0]),
            '00:00:00.500 00:00:07.000 Caption text #1'
            )
        self.assertEqual(
            str(captions[1]),
            r'00:00:07.000 00:00:11.890 Caption text #2 line 1\n'
            'Caption text #2 line 2'
            )

    def test_parse_styles(self):
        output = vtt.parse(
            textwrap.dedent('''
            WEBVTT

            STYLE
            ::cue {
              color: white;
            }

            STYLE
            ::cue(.important) {
              color: red;
              font-weight: bold;
            }

            00:00:00.500 --> 00:00:07.000
            Caption text #1
            ''').strip().split('\n')
            )
        captions = output.captions
        styles = output.styles
        self.assertEqual(len(captions), 1)
        self.assertEqual(len(styles), 2)
        self.assertIsInstance(styles[0], Style)
        self.assertIsInstance(styles[1], Style)
        self.assertEqual(
            str(styles[0].text),
            textwrap.dedent('''
                ::cue {
                  color: white;
                }
                ''').strip()
            )
        self.assertEqual(
            str(styles[1].text),
            textwrap.dedent('''
                ::cue(.important) {
                  color: red;
                  font-weight: bold;
                }
                ''').strip(),
            )

    def test_parse_content(self):
        output = vtt.parse(
            textwrap.dedent('''
            WEBVTT

            NOTE This is a testing sample

            NOTE We can see two header comments, a style
            comment and finally a footer comments

            STYLE
            ::cue {
              background-image: linear-gradient(to bottom, dimgray);
              color: papayawhip;
            }

            NOTE the following style needs review

            STYLE
            ::cue {
              color: white;
            }

            NOTE Comment for the first caption

            00:00:00.500 --> 00:00:07.000
            Caption text #1

            NOTE
            Comment for the second caption
            that is very long

            00:00:07.000 --> 00:00:11.890
            Caption text #2 line 1
            Caption text #2 line 2

            NOTE Copyright 2024

            NOTE end of file
            ''').strip().split('\n')
            )
        captions = output.captions
        styles = output.styles
        self.assertEqual(len(captions), 2)
        self.assertEqual(len(styles), 2)
        self.assertIsInstance(captions[0], Caption)
        self.assertIsInstance(captions[1], Caption)
        self.assertIsInstance(styles[0], Style)
        self.assertIsInstance(styles[1], Style)
        self.assertEqual(
            str(captions[0]),
            '00:00:00.500 00:00:07.000 Caption text #1'
            )
        self.assertEqual(
            str(captions[1]),
            r'00:00:07.000 00:00:11.890 Caption text #2 line 1\n'
            'Caption text #2 line 2'
            )
        self.assertEqual(
            str(styles[0].text),
            textwrap.dedent('''
                ::cue {
                  background-image: linear-gradient(to bottom, dimgray);
                  color: papayawhip;
                }
                ''').strip()
            )
        self.assertEqual(
            str(styles[1].text),
            textwrap.dedent('''
                ::cue {
                  color: white;
                }
                ''').strip()
            )
        self.assertEqual(
            styles[0].comments,
            []
            )
        self.assertEqual(
            styles[1].comments,
            ['the following style needs review']
            )
        self.assertEqual(
            captions[0].comments,
            ['Comment for the first caption']
            )
        self.assertEqual(
            captions[1].comments,
            ['Comment for the second caption\nthat is very long']
            )
        self.assertListEqual(output.header_comments,
                             ['This is a testing sample',
                              'We can see two header comments, a style\n'
                              'comment and finally a footer comments'
                              ]
                             )
        self.assertListEqual(output.footer_comments,
                             ['Copyright 2024',
                              'end of file'
                              ]
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
        styles = [
            Style('::cue(b) {\n  color: peachpuff;\n}'),
            Style('::cue {\n  color: papayawhip;\n}')
            ]
        captions[0].comments.append('Comment for the first caption')
        captions[1].comments.append('Comment for the second caption')
        styles[1].comments.append(
            'Comment for the second style\nwith two lines'
            )
        header_comments = ['header comment', 'begin of the file']
        footer_comments = ['footer comment', 'end of file']

        vtt.write(
            out,
            captions,
            styles,
            header_comments,
            footer_comments
            )

        out.seek(0)

        self.assertEqual(
            out.read(),
            textwrap.dedent('''
                WEBVTT

                NOTE header comment

                NOTE begin of the file

                STYLE
                ::cue(b) {
                  color: peachpuff;
                }

                NOTE
                Comment for the second style
                with two lines

                STYLE
                ::cue {
                  color: papayawhip;
                }

                NOTE Comment for the first caption

                00:00:00.500 --> 00:00:07.000
                Caption #1

                NOTE Comment for the second caption

                00:00:07.000 --> 00:00:11.890
                Caption #2 line 1
                Caption #2 line 2

                NOTE footer comment

                NOTE end of file
            ''').strip()
            )

    def test_to_str(self):
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
        styles = [
            Style('::cue(b) {\n  color: peachpuff;\n}'),
            Style('::cue {\n  color: papayawhip;\n}')
            ]
        captions[0].comments.append('Comment for the first caption')
        captions[1].comments.append('Comment for the second caption')
        styles[1].comments.append(
            'Comment for the second style\nwith two lines'
            )
        header_comments = ['header comment', 'begin of the file']
        footer_comments = ['footer comment', 'end of file']

        self.assertEqual(
            vtt.to_str(
                captions,
                styles,
                header_comments,
                footer_comments
                ),
            textwrap.dedent('''
                WEBVTT

                NOTE header comment

                NOTE begin of the file

                STYLE
                ::cue(b) {
                  color: peachpuff;
                }

                NOTE
                Comment for the second style
                with two lines

                STYLE
                ::cue {
                  color: papayawhip;
                }

                NOTE Comment for the first caption

                00:00:00.500 --> 00:00:07.000
                Caption #1

                NOTE Comment for the second caption

                00:00:07.000 --> 00:00:11.890
                Caption #2 line 1
                Caption #2 line 2

                NOTE footer comment

                NOTE end of file
            ''').strip()
            )

    def test_parse_ignores_malformed_cue_block(self):
        output = vtt.parse(
            textwrap.dedent('''
            WEBVTT

            00:00:00.-004 --> 00:00:04.300
            Caption text #1

            00:00:04.300 --> 00:00:07.000
            Caption text #2
            ''').strip().split('\n')
            )
        self.assertEqual(len(output.captions), 1)
        self.assertEqual(output.captions[0].text, 'Caption text #2')

    def test_parse_non_padded_timestamps(self):
        output = vtt.parse(
            textwrap.dedent('''
            WEBVTT

            0:0:0.0 --> 0:0:3.540
            Caption text #1

            0:0:3.540 --> 0:1:5.2
            Caption text #2
            ''').strip().split('\n')
            )
        self.assertEqual(len(output.captions), 2)
        self.assertEqual(output.captions[0].start, '00:00:00.000')
        self.assertEqual(output.captions[0].end, '00:00:03.540')
        self.assertEqual(output.captions[1].start, '00:00:03.540')
        self.assertEqual(output.captions[1].end, '00:01:05.200')

    def test_parse_strict_non_padded_timestamps(self):
        with self.assertRaises(MalformedCaptionError) as cm:
            vtt.parse(
                textwrap.dedent('''
                WEBVTT

                00:00:00.000 --> 00:00:03.540
                Caption text #1

                0:0:3.540 --> 0:0:7.230
                Caption text #2
                ''').strip().split('\n'),
                strict=True
                )
        self.assertIn('0:0:3.540 --> 0:0:7.230', str(cm.exception))

    def test_parse_ignores_out_of_range_timestamp(self):
        output = vtt.parse(
            textwrap.dedent('''
            WEBVTT

            00:00:61.000 --> 00:00:62.000
            Caption text #1

            00:00:04.300 --> 00:00:07.000
            Caption text #2
            ''').strip().split('\n')
            )
        self.assertEqual(len(output.captions), 1)
        self.assertEqual(output.captions[0].text, 'Caption text #2')

    def test_parse_strict_out_of_range_timestamp(self):
        with self.assertRaises(MalformedCaptionError) as cm:
            vtt.parse(
                textwrap.dedent('''
                WEBVTT

                00:00:61.000 --> 00:00:62.000
                Caption text #1
                ''').strip().split('\n'),
                strict=True
                )
        self.assertIn('00:00:61.000', str(cm.exception))

    def test_parse_strict_malformed_cue_block(self):
        with self.assertRaises(MalformedCaptionError) as cm:
            vtt.parse(
                textwrap.dedent('''
                WEBVTT

                00:00:00.500 --> 00:00:04.300
                Caption text #1

                00:00:04.300 --> 00:00:07.-004
                Caption text #2
                ''').strip().split('\n'),
                strict=True
                )
        self.assertIn('00:00:04.300 --> 00:00:07.-004', str(cm.exception))

    def test_parse_strict_valid_content(self):
        output = vtt.parse(
            textwrap.dedent('''
            WEBVTT

            NOTE a comment

            STYLE
            ::cue {
              color: papayawhip;
            }

            00:00:00.500 --> 00:00:07.000
            Caption text #1
            ''').strip().split('\n'),
            strict=True
            )
        self.assertEqual(len(output.captions), 1)
        self.assertEqual(len(output.styles), 1)

    def test_parse_whitespace_line_is_cue_text(self):
        output = vtt.parse([
            'WEBVTT',
            '',
            '00:00:01.879 --> 00:00:05.660 align:start position:0%',
            ' ',
            'are you done with your chunk yet almost',
            '',
            '00:00:05.660 --> 00:00:05.670 align:start position:0%',
            'are you done with your chunk yet almost',
            ' ',
            ])
        self.assertEqual(len(output.captions), 2)
        self.assertEqual(output.captions[0].start, '00:00:01.879')
        self.assertListEqual(
            output.captions[0].lines,
            [' ', 'are you done with your chunk yet almost']
            )
        self.assertListEqual(
            output.captions[1].lines,
            ['are you done with your chunk yet almost', ' ']
            )

    def test_parse_empty_line_ends_cue(self):
        output = vtt.parse(
            textwrap.dedent('''
            WEBVTT

            00:02:36.420 --> 00:02:42.699

            congratulations
            ''').strip().split('\n')
            )
        self.assertEqual(len(output.captions), 1)
        self.assertEqual(output.captions[0].start, '00:02:36.420')
        self.assertEqual(output.captions[0].text, '')

    def test_parse_cue_without_text(self):
        output = vtt.parse(
            textwrap.dedent('''
            WEBVTT

            identifier
            00:00:00.500 --> 00:00:04.300

            00:00:04.300 --> 00:00:07.000
            Caption text #2
            ''').strip().split('\n'),
            strict=True
            )
        self.assertEqual(len(output.captions), 2)
        self.assertEqual(output.captions[0].identifier, 'identifier')
        self.assertEqual(output.captions[0].text, '')
        self.assertEqual(output.captions[1].text, 'Caption text #2')

    def test_parse_cue_timings_line_starts_new_block(self):
        output = vtt.parse(
            textwrap.dedent('''
            WEBVTT
            00:00:00.500 --> 00:00:04.300
            Caption text #1
            00:00:04.300 --> 00:00:07.000
            Caption text #2
            ''').strip().split('\n')
            )
        self.assertEqual(len(output.captions), 2)
        self.assertIsNone(output.captions[0].identifier)
        self.assertEqual(output.captions[0].end, '00:00:04.300')
        self.assertEqual(output.captions[0].text, 'Caption text #1')
        self.assertEqual(output.captions[1].start, '00:00:04.300')
        self.assertEqual(output.captions[1].text, 'Caption text #2')

    def test_parse_cue_without_text_followed_by_cue_timings_line(self):
        output = vtt.parse(
            textwrap.dedent('''
            WEBVTT

            00:22:21.320 --> 00:22:26.520
            00:21:13.720 --> 00:21:15.360 line:90% position:50% align:middle
            Caption text #2
            ''').strip().split('\n')
            )
        self.assertEqual(len(output.captions), 2)
        self.assertEqual(output.captions[0].start, '00:22:21.320')
        self.assertEqual(output.captions[0].text, '')
        self.assertEqual(output.captions[1].start, '00:21:13.720')
        self.assertEqual(output.captions[1].end, '00:21:15.360')
        self.assertEqual(output.captions[1].text, 'Caption text #2')

    def test_parse_strict_cue_without_text_followed_by_cue_timings_line(self):
        with self.assertRaises(MalformedCaptionError) as cm:
            vtt.parse(
                textwrap.dedent('''
                WEBVTT

                00:22:21.320 --> 00:22:26.520
                00:21:13.720 --> 00:21:15.360
                Caption text #2
                ''').strip().split('\n'),
                strict=True
                )
        self.assertIn('00:21:13.720 --> 00:21:15.360', str(cm.exception))

    def test_parse_consecutive_cues_without_text(self):
        output = vtt.parse(
            textwrap.dedent('''
            WEBVTT

            00:00:00.500 --> 00:00:04.300
            00:00:04.300 --> 00:00:07.000
            00:00:07.000 --> 00:00:09.000
            Caption text #3
            ''').strip().split('\n')
            )
        self.assertEqual(len(output.captions), 3)
        self.assertListEqual(
            [caption.text for caption in output.captions],
            ['', '', 'Caption text #3']
            )

    def test_parse_cue_settings(self):
        output = vtt.parse(
            textwrap.dedent('''
            WEBVTT

            00:00:00.500 --> 00:00:04.300 line:0 align:start
            Caption text #1

            identifier
            00:00:04.300 --> 00:00:07.000\tposition:10%,line-left  size:50%
            Caption text #2

            00:00:07.000 --> 00:00:09.000
            Caption text #3
            ''').strip().split('\n')
            )
        self.assertEqual(len(output.captions), 3)
        self.assertEqual(output.captions[0].settings.line, '0')
        self.assertEqual(output.captions[0].settings.align, 'start')
        self.assertEqual(output.captions[0].text, 'Caption text #1')
        self.assertEqual(output.captions[1].identifier, 'identifier')
        self.assertEqual(
            str(output.captions[1].settings),
            'position:10%,line-left size:50%'
            )
        self.assertFalse(output.captions[2].settings)

    def test_parse_keeps_invalid_and_unknown_cue_settings(self):
        output = vtt.parse(
            textwrap.dedent('''
            WEBVTT

            00:21:13.720 --> 00:21:15.360 line:90% position:50% align:middle
            Caption text #1

            00:21:15.360 --> 00:21:17.000 foo:bar line:0 line:-1
            Caption text #2
            ''').strip().split('\n')
            )
        self.assertEqual(
            str(output.captions[0].settings),
            'line:90% position:50% align:middle'
            )
        self.assertIsNone(output.captions[0].settings.align)
        self.assertEqual(
            str(output.captions[1].settings),
            'foo:bar line:0 line:-1'
            )
        self.assertEqual(output.captions[1].settings.line, '-1')

    def test_parse_ignores_text_attached_to_end_timestamp(self):
        output = vtt.parse(
            textwrap.dedent('''
            WEBVTT

            00:00:00.500 --> 00:00:04.3001 line:0
            Caption text #1
            ''').strip().split('\n')
            )
        self.assertEqual(output.captions[0].end, '00:00:04.300')
        self.assertFalse(output.captions[0].settings)

    def test_parse_cue_settings_without_space(self):
        output = vtt.parse([
            'WEBVTT',
            '',
            '00:00:00.500 --> 00:00:04.300line:0',
            'Caption text #1',
            ])
        self.assertEqual(output.captions[0].end, '00:00:04.300')
        self.assertEqual(str(output.captions[0].settings), 'line:0')

    def test_parse_cue_settings_after_non_ascii_space(self):
        output = vtt.parse([
            'WEBVTT',
            '',
            '00:00:00.500 --> 00:00:04.300\xa0align:start',
            'Caption text #1',
            ])
        self.assertIsNone(output.captions[0].settings.align)
        self.assertEqual(
            str(output.captions[0].settings),
            '\xa0align:start'
            )

    def test_parse_strict_cue_settings_after_non_ascii_space(self):
        with self.assertRaises(MalformedCaptionError):
            vtt.parse(
                [
                    'WEBVTT',
                    '',
                    '00:00:00.500 --> 00:00:04.300\xa0align:start',
                    'Caption text #1',
                    ],
                strict=True
                )

    def test_parse_strict_cue_settings(self):
        output = vtt.parse(
            textwrap.dedent('''
            WEBVTT

            00:00:00.500 --> 00:00:04.300 line:0 align:start
            Caption text #1
            ''').strip().split('\n'),
            strict=True
            )
        self.assertEqual(
            str(output.captions[0].settings),
            'line:0 align:start'
            )

    def test_parse_strict_invalid_cue_settings(self):
        for settings in ('align:middle', 'foo:bar', 'line:0 line:1'):
            with self.subTest(settings=settings):
                with self.assertRaises(MalformedCaptionError):
                    vtt.parse(
                        [
                            'WEBVTT',
                            '',
                            f'00:00:00.500 --> 00:00:04.300 {settings}',
                            'Caption text #1',
                            ],
                        strict=True
                        )

    def test_format_timings(self):
        caption = Caption('00:00:00.500', '00:00:04.300', 'Caption text')
        self.assertEqual(
            vtt.format_timings(caption),
            '00:00:00.500 --> 00:00:04.300'
            )
        caption.settings.line = '0'
        caption.settings.align = 'start'
        self.assertEqual(
            vtt.format_timings(caption),
            '00:00:00.500 --> 00:00:04.300 line:0 align:start'
            )

    def test_cue_settings_round_trip(self):
        content = textwrap.dedent('''
            WEBVTT

            00:21:13.720 --> 00:21:15.360 line:90% position:50% align:middle
            Caption text #1

            identifier
            00:21:15.360 --> 00:21:17.000 foo:bar line:0
            Caption text #2

            00:21:17.000 --> 00:21:19.000
            Caption text #3
            ''').lstrip()
        output = vtt.parse(content.splitlines())
        self.assertEqual(
            vtt.to_str(
                output.captions,
                output.styles,
                output.header_comments,
                output.footer_comments
                ),
            content
            )

    def test_parse_whitespace_lines_between_cues(self):
        output = vtt.parse([
            'WEBVTT',
            '',
            '00:00:00.500 --> 00:00:04.300',
            'Caption text #1',
            '  ',
            '00:00:04.300 --> 00:00:07.000',
            'Caption text #2',
            ])
        self.assertEqual(len(output.captions), 2)
        self.assertListEqual(
            output.captions[0].lines,
            ['Caption text #1', '  ']
            )
        self.assertEqual(output.captions[1].start, '00:00:04.300')
        self.assertEqual(output.captions[1].text, 'Caption text #2')

    def test_parse_strict_cue_timings_line_without_empty_line(self):
        with self.assertRaises(MalformedCaptionError) as cm:
            vtt.parse(
                textwrap.dedent('''
                WEBVTT

                00:00:00.500 --> 00:00:04.300
                Caption text #1
                00:00:04.300 --> 00:00:07.000
                Caption text #2
                ''').strip().split('\n'),
                strict=True
                )
        self.assertIn('00:00:04.300 --> 00:00:07.000', str(cm.exception))

    def test_parse_style_with_whitespace_line(self):
        output = vtt.parse([
            'WEBVTT',
            '',
            'STYLE',
            '::cue {',
            '  color: papayawhip;',
            '}',
            ' ',
            '::cue(b) {',
            '  color: peachpuff;',
            '}',
            '',
            '00:00:00.500 --> 00:00:07.000',
            'Caption text #1',
            ])
        self.assertEqual(len(output.styles), 1)
        self.assertIn('peachpuff', output.styles[0].text)

    def test_parse_header(self):
        output = vtt.parse(
            textwrap.dedent('''
            WEBVTT - Sample title
            X-TIMESTAMP-MAP=LOCAL:00:00:00.000,MPEGTS:126000
            Kind: captions

            NOTE header comment

            00:00:00.500 --> 00:00:07.000
            Caption text #1
            ''').strip().split('\n')
            )
        self.assertEqual(output.header_text, '- Sample title')
        self.assertListEqual(
            output.metadata,
            ['X-TIMESTAMP-MAP=LOCAL:00:00:00.000,MPEGTS:126000',
             'Kind: captions'
             ]
            )
        self.assertListEqual(output.header_comments, ['header comment'])
        self.assertEqual(len(output.captions), 1)

    def test_parse_no_header(self):
        output = vtt.parse(
            textwrap.dedent('''
            WEBVTT

            00:00:00.500 --> 00:00:07.000
            Caption text #1
            ''').strip().split('\n')
            )
        self.assertEqual(output.header_text, '')
        self.assertListEqual(output.metadata, [])

    def test_parse_header_text_separated_by_tab(self):
        output = vtt.parse(['WEBVTT\t Sample title'])
        self.assertEqual(output.header_text, ' Sample title')

    def test_parse_metadata_followed_by_cue(self):
        output = vtt.parse(
            textwrap.dedent('''
            WEBVTT
            X-TIMESTAMP-MAP=LOCAL:00:00:00.000,MPEGTS:126000
            00:00:00.500 --> 00:00:07.000
            Caption text #1
            ''').strip().split('\n'),
            strict=True
            )
        self.assertListEqual(
            output.metadata,
            ['X-TIMESTAMP-MAP=LOCAL:00:00:00.000,MPEGTS:126000']
            )
        self.assertEqual(len(output.captions), 1)

    def test_write_header(self):
        out = io.StringIO()
        captions = [
            Caption(start='00:00:00.500',
                    end='00:00:07.000',
                    text='Caption #1'
                    )
            ]

        vtt.write(
            out,
            captions,
            [],
            ['header comment'],
            [],
            '- Sample title',
            ['X-TIMESTAMP-MAP=LOCAL:00:00:00.000,MPEGTS:126000',
             'Kind: captions'
             ]
            )

        out.seek(0)

        self.assertEqual(
            out.read(),
            textwrap.dedent('''
                WEBVTT - Sample title
                X-TIMESTAMP-MAP=LOCAL:00:00:00.000,MPEGTS:126000
                Kind: captions

                NOTE header comment

                00:00:00.500 --> 00:00:07.000
                Caption #1
            ''').lstrip()
            )

    def test_to_str_header_round_trip(self):
        lines = textwrap.dedent('''
            WEBVTT\tSample title
            X-TIMESTAMP-MAP=LOCAL:00:00:00.000,MPEGTS:126000
              indented line

            00:00:00.500 --> 00:00:07.000
            Caption text #1
            ''').lstrip().split('\n')
        output = vtt.parse(lines)

        content = vtt.to_str(
            output.captions,
            output.styles,
            output.header_comments,
            output.footer_comments,
            output.header_text,
            output.metadata
            )

        self.assertEqual(content, '\n'.join(lines).replace('\t', ' '))
        self.assertEqual(vtt.parse(content.split('\n')), output)

    def test_to_str_invalid_header_text(self):
        for header_text in ('title\nmore', 'title\r', 'title\r\nmore'):
            with self.subTest(header_text=header_text):
                with self.assertRaises(ValueError):
                    vtt.to_str([], [], [], [], header_text)

    def test_to_str_header_with_other_unicode_line_separators(self):
        content = vtt.to_str(
            [], [], [], [], 'title\u2028more', ['Kind: a\x0cb', 'Lang\x85en']
            )
        self.assertEqual(
            content,
            'WEBVTT title\u2028more\nKind: a\x0cb\nLang\x85en\n'
            )

    def test_parse_items_without_header(self):
        output = vtt.parse_items(['00:00:00.500 --> 00:00:07.000',
                                  'Caption text #1'
                                  ])
        self.assertEqual(output.header_text, '')
        self.assertListEqual(output.metadata, [])
        self.assertEqual(len(output.captions), 1)

    def test_to_str_invalid_metadata(self):
        for line in ('',
                     'Kind: captions\nLanguage: en',
                     'Language: en\r',
                     'X-TIMESTAMP-MAP --> 0',
                     ):
            with self.subTest(line=line):
                with self.assertRaises(ValueError) as cm:
                    vtt.to_str([], [], [], [], '', ['Kind: captions', line])
                self.assertIn(repr(line), str(cm.exception))
