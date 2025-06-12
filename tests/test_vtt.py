import unittest
import textwrap
import io

from webvtt import vtt
from webvtt.errors import MalformedFileError
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

        self.assertFalse(
            vtt.WebVTTCueBlock.is_valid(textwrap.dedent('''
            00:00:00.500 --> 00:00:07.000
            ''').strip().split('\n'))
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

    def test_parse_caption_with_blank_line_after_timing(self):
        output = vtt.parse(
            textwrap.dedent('''
            WEBVTT

            00:00:00.500 --> 00:00:05.000

            Caption text #1
            ''').strip().split('\n')
            )

        self.assertEqual(len(output.captions), 1)
        self.assertEqual(
            str(output.captions[0]),
            '00:00:00.500 00:00:05.000 Caption text #1',
            )

    def test_parse_caption_with_multiple_blank_lines_after_timing(self):
        output = vtt.parse(
            textwrap.dedent('''
            WEBVTT

            00:00:00.500 --> 00:00:05.000


            Caption text #1
            ''').strip().split('\n')
            )

        self.assertEqual(len(output.captions), 1)
        self.assertEqual(
            str(output.captions[0]),
            '00:00:00.500 00:00:05.000 Caption text #1',
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
