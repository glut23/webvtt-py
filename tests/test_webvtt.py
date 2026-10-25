import datetime
import fractions
import unittest
import os
import io
import textwrap
import warnings
import tempfile
import pathlib

import webvtt
from webvtt.models import Caption, Region, Style, Timestamp
from webvtt.utils import CODEC_BOMS
from webvtt.errors import MalformedFileError, MalformedCaptionError

from .helpers import named_temporary_file

PATH_TO_SAMPLES = pathlib.Path(__file__).resolve().parent / 'samples'


class TestWebVTT(unittest.TestCase):

    def test_from_string(self):
        vtt = webvtt.from_string(textwrap.dedent("""
            WEBVTT

            00:00:00.500 --> 00:00:07.000
            Caption text #1

            00:00:07.000 --> 00:00:11.890
            Caption text #2 line 1
            Caption text #2 line 2

            00:00:11.890 --> 00:00:16.320
            Caption text #3

            00:00:16.320 --> 00:00:21.580
            Caption text #4
            """).strip()
            )
        self.assertEqual(len(vtt), 4)
        self.assertEqual(
            str(vtt[0]),
            '00:00:00.500 00:00:07.000 Caption text #1'
            )
        self.assertEqual(
            str(vtt[1]),
            r'00:00:07.000 00:00:11.890 Caption text #2 line 1\n'
            'Caption text #2 line 2'
            )
        self.assertEqual(
            str(vtt[2]),
            '00:00:11.890 00:00:16.320 Caption text #3'
            )
        self.assertEqual(
            str(vtt[3]),
            '00:00:16.320 00:00:21.580 Caption text #4'
            )

    def test_write_captions(self):
        out = io.StringIO()
        vtt = webvtt.read(PATH_TO_SAMPLES / 'one_caption.vtt')
        new_caption = Caption(start='00:00:07.000',
                              end='00:00:11.890',
                              text=['New caption text line1',
                                    'New caption text line2'
                                    ]
                              )
        vtt.captions.append(new_caption)
        vtt.write(out)

        out.seek(0)

        self.assertEqual(
            out.read(),
            textwrap.dedent('''
                WEBVTT

                00:00:00.500 --> 00:00:07.000
                Caption text #1

                00:00:07.000 --> 00:00:11.890
                New caption text line1
                New caption text line2
            ''').strip() + '\n'
            )

    def test_write_captions_in_srt(self):
        out = io.StringIO()
        vtt = webvtt.read(PATH_TO_SAMPLES / 'one_caption.vtt')
        new_caption = Caption(start='00:00:07.000',
                              end='00:00:11.890',
                              text=['New caption text line1',
                                    'New caption text line2'
                                    ]
                              )
        vtt.captions.append(new_caption)
        vtt.write(out, format='srt')

        out.seek(0)
        self.assertEqual(
            out.read(),
            textwrap.dedent('''
                1
                00:00:00,500 --> 00:00:07,000
                Caption text #1

                2
                00:00:07,000 --> 00:00:11,890
                New caption text line1
                New caption text line2
            ''').strip()
            )

    def test_write_captions_in_srt_no_cuetags(self):
        """https://github.com/glut23/webvtt-py/issues/56"""
        out = io.StringIO()
        vtt = webvtt.read(PATH_TO_SAMPLES / 'cue_tags.vtt')
        vtt.write(out, format='srt')

        out.seek(0)
        self.assertEqual(
            out.read(),
            textwrap.dedent('''
            1
            00:00:16,500 --> 00:00:18,500
            When the moon hits your eye

            2
            00:00:18,500 --> 00:00:20,500
            Like a big-a pizza pie

            3
            00:00:20,500 --> 00:00:21,500
            That's amore
            ''').strip()
            )

    def test_write_captions_in_unsupported_format(self):
        self.assertRaises(
            ValueError,
            webvtt.WebVTT().write,
            io.StringIO(),
            format='ttt'
            )

    def test_save_captions(self):
        with named_temporary_file('w', suffix='.vtt') as f:
            f.write((PATH_TO_SAMPLES / 'one_caption.vtt').read_text())
            f.flush()

            vtt = webvtt.read(f.name)
            new_caption = Caption(start='00:00:07.000',
                                  end='00:00:11.890',
                                  text=['New caption text line1',
                                        'New caption text line2'
                                        ]
                                  )
            vtt.captions.append(new_caption)
            vtt.save()
            f.flush()

            self.assertEqual(
                pathlib.Path(f.name).read_text(),
                textwrap.dedent('''
                    WEBVTT

                    00:00:00.500 --> 00:00:07.000
                    Caption text #1

                    00:00:07.000 --> 00:00:11.890
                    New caption text line1
                    New caption text line2
                    ''').strip() + '\n'
                )

    def test_srt_conversion(self):
        with tempfile.TemporaryDirectory() as td:
            with open(pathlib.Path(td) / 'one_caption.srt', 'w') as f:
                f.write((PATH_TO_SAMPLES / 'one_caption.srt').read_text())

            webvtt.from_srt(
                pathlib.Path(td) / 'one_caption.srt'
                ).save()

            self.assertTrue(
                os.path.exists(pathlib.Path(td) / 'one_caption.vtt')
                )
            self.assertEqual(
                (pathlib.Path(td) / 'one_caption.vtt').read_text(),
                textwrap.dedent('''
                    WEBVTT

                    00:00:00.500 --> 00:00:07.000
                    Caption text #1
                    ''').strip() + '\n'
                )

    def test_sbv_conversion(self):
        with tempfile.TemporaryDirectory() as td:
            with open(pathlib.Path(td) / 'two_captions.sbv', 'w') as f:
                f.write(
                    (PATH_TO_SAMPLES / 'two_captions.sbv').read_text()
                    )

            webvtt.from_sbv(
                pathlib.Path(td) / 'two_captions.sbv'
                ).save()

            self.assertTrue(
                os.path.exists(pathlib.Path(td) / 'two_captions.vtt')
                )
            self.assertEqual(
                (pathlib.Path(td) / 'two_captions.vtt').read_text(),
                textwrap.dedent('''
                    WEBVTT

                    00:00:00.378 --> 00:00:11.378
                    Caption text #1

                    00:00:11.378 --> 00:00:12.305
                    Caption text #2 (line 1)
                    Caption text #2 (line 2)
                    ''').strip() + '\n'
                )

    def test_save_to_other_location(self):
        with tempfile.TemporaryDirectory() as td:
            webvtt.read(
                PATH_TO_SAMPLES / 'one_caption.vtt'
                ).save(td)

            self.assertTrue(
                os.path.exists(pathlib.Path(td) / 'one_caption.vtt')
                )

    def test_save_specific_filename(self):
        with tempfile.TemporaryDirectory() as td:
            webvtt.read(
                PATH_TO_SAMPLES / 'one_caption.vtt'
                ).save(
                    pathlib.Path(td) / 'one_caption_new.vtt'
                )

            self.assertTrue(
                os.path.exists(pathlib.Path(td) / 'one_caption_new.vtt')
                )

    def test_save_specific_filename_no_extension(self):
        with tempfile.TemporaryDirectory() as td:
            webvtt.read(
                PATH_TO_SAMPLES / 'one_caption.vtt'
                ).save(
                    pathlib.Path(td) / 'one_caption_new'
                )

            self.assertTrue(
                os.path.exists(pathlib.Path(td) / 'one_caption_new.vtt')
                )

    def test_from_buffer(self):
        with open(PATH_TO_SAMPLES / 'sample.vtt', 'r', encoding='utf-8') as f:
            vtt = webvtt.from_buffer(f)
            self.assertEqual(len(vtt), 16)
            self.assertEqual(
                str(vtt),
                textwrap.dedent('''
                    00:00:00.500 00:00:07.000 Caption text #1
                    00:00:07.000 00:00:11.890 Caption text #2
                    00:00:11.890 00:00:16.320 Caption text #3
                    00:00:16.320 00:00:21.580 Caption text #4
                    00:00:21.580 00:00:23.880 Caption text #5
                    00:00:23.880 00:00:27.280 Caption text #6
                    00:00:27.280 00:00:30.280 Caption text #7
                    00:00:30.280 00:00:36.510 Caption text #8
                    00:00:36.510 00:00:38.870 Caption text #9
                    00:00:38.870 00:00:45.000 Caption text #10
                    00:00:45.000 00:00:47.000 Caption text #11
                    00:00:47.000 00:00:50.970 Caption text #12
                    00:00:50.970 00:00:54.440 Caption text #13
                    00:00:54.440 00:00:58.600 Caption text #14
                    00:00:58.600 00:01:01.350 Caption text #15
                    00:01:01.350 00:01:04.300 Caption text #16
                    '''
                    ).strip())

    def test_deprecated_read_buffer(self):
        with open(PATH_TO_SAMPLES / 'sample.vtt', 'r', encoding='utf-8') as f:
            with warnings.catch_warnings(record=True) as warns:
                warnings.simplefilter('always')
                vtt = webvtt.read_buffer(f)

                self.assertIsInstance(vtt.captions, list)
                self.assertEqual(
                    'Deprecated: use from_buffer instead.',
                    str(warns[-1].message)
                    )

    def test_read_memory_buffer(self):
        buffer = io.StringIO(
            (PATH_TO_SAMPLES / 'sample.vtt').read_text()
            )

        self.assertIsInstance(
            webvtt.from_buffer(buffer).captions,
            list
            )

    def test_read_memory_buffer_carriage_return(self):
        """https://github.com/glut23/webvtt-py/issues/29"""
        buffer = io.StringIO(textwrap.dedent('''\
            WEBVTT\r
            \r
            00:00:00.500 --> 00:00:07.000\r
            Caption text #1\r
            \r
            00:00:07.000 --> 00:00:11.890\r
            Caption text #2\r
            \r
            00:00:11.890 --> 00:00:16.320\r
            Caption text #3\r
        ''')
        )

        self.assertEqual(
            len(webvtt.from_buffer(buffer).captions),
            3
            )

    def test_read_malformed_buffer(self):
        malformed_payloads = ['', 'MOCK MALFORMED CONTENT']
        for payload in malformed_payloads:
            buffer = io.StringIO(payload)
            with self.assertRaises(MalformedFileError):
                webvtt.from_buffer(buffer)

    def test_from_buffer_strict(self):
        content = textwrap.dedent('''
            WEBVTT

            00:00:00.-004 --> 00:00:04.300
            Caption text #1
            ''').strip()

        self.assertEqual(
            len(webvtt.from_buffer(io.StringIO(content)).captions),
            0
            )
        with self.assertRaises(MalformedCaptionError):
            webvtt.from_buffer(io.StringIO(content), strict=True)

    def test_from_string_strict(self):
        """https://github.com/glut23/webvtt-py/issues/76"""
        content = textwrap.dedent('''
            WEBVTT

            00:00:00.-004 --> 00:00:04.300
            This is a test with a malformed timestamp.
            ''').strip()

        self.assertEqual(len(webvtt.from_string(content).captions), 0)
        with self.assertRaises(MalformedCaptionError):
            webvtt.from_string(content, strict=True)

    def test_from_string_line_breaks(self):
        content = (
            'WEBVTT\r\n'
            '\r\n'
            '00:00:00.500 --> 00:00:07.000\r'
            'line 1\u2028still line 1\x0cand\x85more\r'
            'line 2\n'
            '\n'
            '00:00:07.000 --> 00:00:11.890\n'
            'Caption #2'
            )

        vtt = webvtt.from_string(content)

        self.assertListEqual(
            [caption.lines for caption in vtt.captions],
            [['line 1\u2028still line 1\x0cand\x85more', 'line 2'],
             ['Caption #2']
             ]
            )
        with tempfile.TemporaryDirectory() as td:
            path = os.path.join(td, 'captions.vtt')
            with open(path, 'w', encoding='utf-8', newline='') as f:
                f.write(content)
            self.assertListEqual(
                [caption.lines for caption in webvtt.read(path).captions],
                [caption.lines for caption in vtt.captions]
                )

    def test_read_buffer_for_vtt_content(self):
        buffer = io.StringIO(textwrap.dedent('''\
            WEBVTT\r
            \r
            00:00:00.500 --> 00:00:07.000\r
            Caption text #1\r
            \r
            00:00:07.000 --> 00:00:11.890\r
            Caption text #2\r
            \r
            00:00:11.890 --> 00:00:16.320\r
            Caption text #3\r
            ''')
            )
        vtt = webvtt.from_buffer(buffer, format='vtt')
        self.assertEqual(len(vtt), 3)

        self.assertEqual(
            str(vtt[0]),
            '00:00:00.500 00:00:07.000 Caption text #1'
            )
        self.assertEqual(
            str(vtt[1]),
            '00:00:07.000 00:00:11.890 Caption text #2'
            )
        self.assertEqual(
            str(vtt[2]),
            '00:00:11.890 00:00:16.320 Caption text #3'
            )

    def test_read_buffer_for_srt_content(self):
        buffer = io.StringIO(textwrap.dedent('''\
            0\r
            00:00:00,500 --> 00:00:07,000\r
            Caption text #1\r
            \r
            1\r
            00:00:07,000 --> 00:00:11,890\r
            Caption text #2\r
            \r
            2\r
            00:00:11,890 --> 00:00:16,320\r
            Caption text #3\r
            ''')
            )
        vtt = webvtt.from_buffer(buffer, format='srt')
        self.assertEqual(len(vtt), 3)

        self.assertEqual(
            str(vtt[0]),
            '00:00:00.500 00:00:07.000 Caption text #1'
            )
        self.assertEqual(
            str(vtt[1]),
            '00:00:07.000 00:00:11.890 Caption text #2'
            )
        self.assertEqual(
            str(vtt[2]),
            '00:00:11.890 00:00:16.320 Caption text #3'
            )

    def test_read_buffer_for_sbv_content_with_long_hours(self):
        buffer = io.StringIO('100:00:00.000,100:00:05.000\nCaption text\n')
        vtt = webvtt.from_buffer(buffer, format='sbv')
        self.assertEqual(len(vtt), 1)
        self.assertEqual(vtt[0].start_time.hours, 100)
        self.assertEqual(vtt[0].end, '100:00:05.000')

    def test_read_buffer_for_sbv_content(self):
        buffer = io.StringIO(textwrap.dedent('''\
            00:00:00.500,00:00:07.000\r
            Caption text #1\r
            \r
            00:00:07.000,00:00:11.890\r
            Caption text #2\r
            \r
            00:00:11.890,00:00:16.320\r
            Caption text #3\r
            ''')
            )
        vtt = webvtt.from_buffer(buffer, format='sbv')
        self.assertEqual(len(vtt), 3)

        self.assertEqual(
            str(vtt[0]),
            '00:00:00.500 00:00:07.000 Caption text #1'
            )
        self.assertEqual(
            str(vtt[1]),
            '00:00:07.000 00:00:11.890 Caption text #2'
            )
        self.assertEqual(
            str(vtt[2]),
            '00:00:11.890 00:00:16.320 Caption text #3'
            )

    def test_read_buffer_with_bom(self):
        for format in ('vtt', 'srt', 'sbv'):
            source = (PATH_TO_SAMPLES / ('sample.' + format)).read_text()
            expected = webvtt.from_buffer(io.StringIO(source), format=format)
            for buffer in (
                    io.StringIO('\ufeff' + source),
                    io.BytesIO(('\ufeff' + source).encode('utf-8')),
                    iter(('\ufeff' + source).splitlines())
                    ):
                with self.subTest(format=format, buffer=type(buffer)):
                    actual = webvtt.from_buffer(buffer, format=format)
                    self.assertEqual(
                        [(c.start, c.end, c.text) for c in actual],
                        [(c.start, c.end, c.text) for c in expected]
                        )

    def test_get_lines_preserves_bom_in_caption_text(self):
        self.assertEqual(
            webvtt.WebVTT._get_lines(iter(['\ufeffWEBVTT\r\n',
                                           '\ufeffcaption\n'])),
            ['WEBVTT', '\ufeffcaption']
            )

    def test_read_buffer_unsupported_format(self):
        self.assertRaises(
            ValueError,
            webvtt.from_buffer,
            io.StringIO(),
            format='ttt'
            )

    def test_read_bytesio_buffer_line_breaks(self):
        sources = {
            'vtt': 'WEBVTT\r\r00:00:00.500 --> 00:00:07.000\r'
                   'line 1\u2028still line 1\r\nline 2\n',
            'srt': '1\r00:00:00,500 --> 00:00:07,000\r'
                   'line 1\u2028still line 1\r\nline 2\n',
            'sbv': '0:00:00.500,0:00:07.000\r'
                   'line 1\u2028still line 1\r\nline 2\n',
            }
        for format, source in sources.items():
            with self.subTest(format=format):
                buffer = io.BytesIO(source.encode('utf-8'))
                vtt = webvtt.from_buffer(buffer, format=format)
                self.assertEqual(len(vtt), 1)
                self.assertListEqual(
                    vtt[0].lines,
                    ['line 1\u2028still line 1', 'line 2']
                    )
                self.assertFalse(buffer.closed)

    def test_read_buffer_line_breaks(self):
        content = (
            'WEBVTT\r\r00:00:00.500 --> 00:00:07.000\r'
            'line 1\u2028still line 1\r\nline 2\r\r\n'
            '00:00:07.000 --> 00:00:11.890\nCaption #2\n'
            )
        vtt = webvtt.from_buffer(io.StringIO(content))
        self.assertListEqual(
            [caption.lines for caption in vtt.captions],
            [['line 1\u2028still line 1', 'line 2'], ['Caption #2']]
            )

    def test_save_as_srt_keeps_unicode_line_separators(self):
        vtt = webvtt.from_string(textwrap.dedent('''
            WEBVTT

            00:00:00.500 --> 00:00:07.000
            line 1\u2028still line 1
            line 2
            ''').lstrip()
            )
        out = io.StringIO()
        vtt.write(out, format='srt')
        self.assertEqual(
            out.getvalue(),
            '1\n00:00:00,500 --> 00:00:07,000\n'
            'line 1\u2028still line 1\nline 2'
            )

    def test_read_bytesio_buffer_for_srt_content(self):
        buffer = io.BytesIO(textwrap.dedent('''\
            0\r
            00:00:00,500 --> 00:00:07,000\r
            Caption text #1\r
            \r
            1\r
            00:00:07,000 --> 00:00:11,890\r
            Caption text #2\r
            \r
            2\r
            00:00:11,890 --> 00:00:16,320\r
            Caption text #3\r
            ''').encode('utf-8')
            )
        vtt = webvtt.from_buffer(buffer, format='srt')
        self.assertEqual(len(vtt), 3)

        self.assertEqual(
            str(vtt[0]),
            '00:00:00.500 00:00:07.000 Caption text #1'
            )
        self.assertEqual(
            str(vtt[1]),
            '00:00:07.000 00:00:11.890 Caption text #2'
            )
        self.assertEqual(
            str(vtt[2]),
            '00:00:11.890 00:00:16.320 Caption text #3'
            )

    def test_captions(self):
        captions = webvtt.read(PATH_TO_SAMPLES / 'sample.vtt').captions
        self.assertIsInstance(
            captions,
            list
            )
        self.assertEqual(len(captions), 16)

    def test_sequence_iteration(self):
        vtt = webvtt.read(PATH_TO_SAMPLES / 'sample.vtt')
        self.assertIsInstance(vtt[0], Caption)
        self.assertEqual(len(vtt), len(vtt.captions))

    def test_save_no_filename(self):
        self.assertRaises(
            webvtt.errors.MissingFilenameError,
            webvtt.WebVTT().save
            )

    def test_positional_arguments(self):
        with tempfile.TemporaryDirectory() as td:
            vtt_file = os.path.join(td, 'captions.vtt')
            content = (PATH_TO_SAMPLES / 'one_caption.vtt').read_text()
            pathlib.Path(vtt_file).write_text(content)

            with self.assertRaises(TypeError) as cm:
                webvtt.WebVTT(vtt_file)

            self.assertIn('use webvtt.read()', str(cm.exception))
            self.assertEqual(pathlib.Path(vtt_file).read_text(), content)

    def test_deprecated_file_argument(self):
        with warnings.catch_warnings(record=True) as warns:
            warnings.simplefilter('always')
            vtt = webvtt.WebVTT(file='captions.vtt')

        self.assertEqual(vtt.file, 'captions.vtt')
        self.assertEqual(len(warns), 1)
        self.assertIs(warns[0].category, DeprecationWarning)
        self.assertIn('The file argument of WebVTT() is deprecated',
                      str(warns[0].message))
        # the warning points to the code creating the instance
        self.assertEqual(os.path.basename(warns[0].filename),
                         os.path.basename(__file__))

    def test_readers_set_file_without_warnings(self):
        sample = str(PATH_TO_SAMPLES / 'sample.vtt')
        with warnings.catch_warnings():
            warnings.simplefilter('error')
            with open(sample, encoding='utf-8') as f:
                from_open_file = webvtt.from_buffer(f)

            for vtt, expected in (
                    (webvtt.read(sample), sample),
                    (webvtt.from_srt(str(PATH_TO_SAMPLES / 'sample.srt')),
                     str(PATH_TO_SAMPLES / 'sample.srt')),
                    (webvtt.from_sbv(str(PATH_TO_SAMPLES / 'sample.sbv')),
                     str(PATH_TO_SAMPLES / 'sample.sbv')),
                    (from_open_file, sample),
                    (webvtt.from_buffer(
                        io.BytesIO(pathlib.Path(sample).read_bytes())
                        ), None),
                    (webvtt.from_string(pathlib.Path(sample).read_text()),
                     None)):
                with self.subTest(expected=expected):
                    self.assertEqual(vtt.file, expected)

    def test_save_to_file_attribute(self):
        with tempfile.TemporaryDirectory() as td:
            vtt = webvtt.WebVTT(
                captions=[Caption('00:00:00.500', '00:00:07.000',
                                  'Caption text #1')]
                )
            vtt.file = os.path.join(td, 'captions.vtt')
            vtt.save()

            self.assertEqual(
                pathlib.Path(td, 'captions.vtt').read_text(),
                'WEBVTT\n\n00:00:00.500 --> 00:00:07.000\nCaption text #1\n'
                )

    def test_save_with_path_to_dir_no_filename(self):
        with tempfile.TemporaryDirectory() as td:
            self.assertRaises(
                webvtt.errors.MissingFilenameError,
                webvtt.WebVTT().save,
                td
                )

    def test_set_styles_from_text(self):
        style = Style('::cue(b) {\n  color: peachpuff;\n}')
        self.assertListEqual(
            style.lines,
            ['::cue(b) {', '  color: peachpuff;', '}']
            )

    def test_save_identifiers(self):
        with named_temporary_file('w', suffix='.vtt') as f:
            webvtt.read(
                PATH_TO_SAMPLES / 'using_identifiers.vtt'
                ).save(
                    f.name
                    )

            self.assertListEqual(
                pathlib.Path(f.name).read_text().splitlines(),
                [
                    'WEBVTT',
                    '',
                    '00:00:00.500 --> 00:00:07.000',
                    'Caption text #1',
                    '',
                    'second caption',
                    '00:00:07.000 --> 00:00:11.890',
                    'Caption text #2',
                    '',
                    '00:00:11.890 --> 00:00:16.320',
                    'Caption text #3',
                    '',
                    '4',
                    '00:00:16.320 --> 00:00:21.580',
                    'Caption text #4',
                    '',
                    '00:00:21.580 --> 00:00:23.880',
                    'Caption text #5',
                    '',
                    '00:00:23.880 --> 00:00:27.280',
                    'Caption text #6'
                    ]
                )

    def test_save_cue_settings(self):
        with named_temporary_file('w', suffix='.vtt') as f:
            vtt = webvtt.read(PATH_TO_SAMPLES / 'netflix_chicas_del_cable.vtt')
            vtt.save(f.name)

            lines = pathlib.Path(f.name).read_text(
                encoding='utf-8'
                ).splitlines()
            self.assertIn(
                '00:00:07.960 --> 00:00:09.480 position:50.00%,middle '
                'align:middle size:80.00% line:84.67%',
                lines
                )

    def test_save_updated_cue_settings(self):
        vtt = webvtt.read(PATH_TO_SAMPLES / 'youtube_dl.vtt')
        vtt.captions[0].settings.line = '0'
        vtt.captions[1].settings = None

        lines = vtt.content.splitlines()
        self.assertIn(
            '00:04:46.070 --> 00:04:46.470 align:start position:0% line:0',
            lines
            )
        self.assertIn('00:04:46.470 --> 00:05:04.080', lines)

    def test_shift_keeps_cue_settings(self):
        vtt = webvtt.from_string(
            'WEBVTT\n\n00:00:01.000 --> 00:00:03.000 line:0 align:start\n'
            'Top left\n'
            )
        vtt.shift(2)
        self.assertEqual(
            vtt.content,
            'WEBVTT\n\n00:00:03.000 --> 00:00:05.000 line:0 align:start\n'
            'Top left\n'
            )

    def test_save_as_srt_without_cue_settings(self):
        vtt = webvtt.from_string(
            'WEBVTT\n\n00:00:01.000 --> 00:00:03.000 line:0 align:start\n'
            'Top left\n'
            )
        output = io.StringIO()
        vtt.write(output, format='srt')
        self.assertEqual(
            output.getvalue(),
            '1\n00:00:01,000 --> 00:00:03,000\nTop left'
            )

    def test_save_as_srt_keeping_formatting(self):
        vtt = webvtt.from_string(textwrap.dedent('''
            WEBVTT

            STYLE
            ::cue(.yellow) {
              color: yellow;
            }

            00:00:01.000 --> 00:00:03.000
            <c.yellow>Hello <b>world</b></c>
            ''').lstrip()
            )
        output = io.StringIO()
        vtt.write(output, format='srt', keep_formatting=True)
        self.assertEqual(
            output.getvalue(),
            '1\n00:00:01,000 --> 00:00:03,000\n'
            '<font color="yellow">Hello <b>world</b></font>'
            )

    def test_save_as_srt_keeping_formatting_ignored_for_vtt(self):
        vtt = webvtt.read(PATH_TO_SAMPLES / 'styles_colours.vtt')
        output = io.StringIO()
        vtt.write(output, keep_formatting=True)
        self.assertEqual(
            output.getvalue(),
            (PATH_TO_SAMPLES / 'styles_colours.vtt').read_text(
                encoding='utf-8'
                )
            )

    def test_save_updated_identifiers(self):
        vtt = webvtt.read(PATH_TO_SAMPLES / 'using_identifiers.vtt')
        vtt.captions[0].identifier = 'first caption'
        vtt.captions[1].identifier = None
        vtt.captions[3].identifier = '44'
        last_caption = Caption(start='00:00:27.280',
                               end='00:00:29.200',
                               text='Caption text #7'
                               )
        last_caption.identifier = 'last caption'
        vtt.captions.append(last_caption)

        with named_temporary_file('w', suffix='.vtt') as f:
            vtt.save(f.name)

            self.assertListEqual(
                pathlib.Path(f.name).read_text().splitlines(),
                [
                    'WEBVTT',
                    '',
                    'first caption',
                    '00:00:00.500 --> 00:00:07.000',
                    'Caption text #1',
                    '',
                    '00:00:07.000 --> 00:00:11.890',
                    'Caption text #2',
                    '',
                    '00:00:11.890 --> 00:00:16.320',
                    'Caption text #3',
                    '',
                    '44',
                    '00:00:16.320 --> 00:00:21.580',
                    'Caption text #4',
                    '',
                    '00:00:21.580 --> 00:00:23.880',
                    'Caption text #5',
                    '',
                    '00:00:23.880 --> 00:00:27.280',
                    'Caption text #6',
                    '',
                    'last caption',
                    '00:00:27.280 --> 00:00:29.200',
                    'Caption text #7'
                    ]
                )

    def test_content_formatting(self):
        """
        Verify that content property returns the correctly formatted webvtt.
        """
        captions = [
            Caption(start='00:00:00.500',
                    end='00:00:07.000',
                    text=['Caption test line 1', 'Caption test line 2']
                    ),
            Caption(start='00:00:08.000',
                    end='00:00:15.000',
                    text=['Caption test line 3', 'Caption test line 4']
                    ),
            ]

        self.assertEqual(
            webvtt.WebVTT(captions=captions).content,
            textwrap.dedent("""
                    WEBVTT

                    00:00:00.500 --> 00:00:07.000
                    Caption test line 1
                    Caption test line 2

                    00:00:08.000 --> 00:00:15.000
                    Caption test line 3
                    Caption test line 4
                    """).strip() + '\n'
            )

    def test_repr(self):
        test_file = PATH_TO_SAMPLES / 'sample.vtt'
        self.assertEqual(
            repr(webvtt.read(test_file)),
            f"<WebVTT file={str(test_file)!r} encoding='utf-8'>"
            )

    def test_str(self):
        self.assertEqual(
            str(webvtt.read(PATH_TO_SAMPLES / 'sample.vtt')),
            textwrap.dedent("""
                00:00:00.500 00:00:07.000 Caption text #1
                00:00:07.000 00:00:11.890 Caption text #2
                00:00:11.890 00:00:16.320 Caption text #3
                00:00:16.320 00:00:21.580 Caption text #4
                00:00:21.580 00:00:23.880 Caption text #5
                00:00:23.880 00:00:27.280 Caption text #6
                00:00:27.280 00:00:30.280 Caption text #7
                00:00:30.280 00:00:36.510 Caption text #8
                00:00:36.510 00:00:38.870 Caption text #9
                00:00:38.870 00:00:45.000 Caption text #10
                00:00:45.000 00:00:47.000 Caption text #11
                00:00:47.000 00:00:50.970 Caption text #12
                00:00:50.970 00:00:54.440 Caption text #13
                00:00:54.440 00:00:58.600 Caption text #14
                00:00:58.600 00:01:01.350 Caption text #15
                00:01:01.350 00:01:04.300 Caption text #16
            """).strip()
            )

    def test_parse_invalid_file(self):
        self.assertRaises(
            MalformedFileError,
            webvtt.read,
            PATH_TO_SAMPLES / 'invalid.vtt'
            )

    def test_file_not_found(self):
        self.assertRaises(
            FileNotFoundError,
            webvtt.read,
            'nowhere'
            )

    def test_total_length(self):
        self.assertEqual(
            webvtt.read(PATH_TO_SAMPLES / 'sample.vtt').total_length,
            64
            )

    def test_total_length_no_captions(self):
        self.assertEqual(
            webvtt.WebVTT().total_length,
            0
            )

    def test_shift(self):
        vtt = webvtt.read(PATH_TO_SAMPLES / 'sample.vtt')
        durations = [
            c.end_time.in_milliseconds() - c.start_time.in_milliseconds()
            for c in vtt
            ]

        vtt.shift(1.25)

        self.assertEqual(vtt[0].start, '00:00:01.750')
        self.assertEqual(vtt[0].end, '00:00:08.250')
        self.assertEqual(vtt[-1].start, '00:01:02.600')
        self.assertEqual(vtt[-1].end, '00:01:05.550')
        self.assertEqual(
            [c.end_time.in_milliseconds() - c.start_time.in_milliseconds()
             for c in vtt],
            durations
            )

    def test_shift_negative_clamps_to_zero(self):
        vtt = webvtt.from_string(textwrap.dedent('''
            WEBVTT

            00:00:00.500 --> 00:00:01.000
            Credits

            00:00:01.500 --> 00:00:04.000
            Caption #1

            00:00:04.000 --> 00:00:07.000
            Caption #2
            ''').strip())

        vtt.shift(-2)

        self.assertEqual(
            [(c.start, c.end) for c in vtt],
            [('00:00:00.000', '00:00:00.000'),
             ('00:00:00.000', '00:00:02.000'),
             ('00:00:02.000', '00:00:05.000')]
            )
        self.assertEqual(len(vtt), 3)
        self.assertEqual(vtt[0].text, 'Credits')

    def test_shift_timedelta(self):
        vtt = webvtt.read(PATH_TO_SAMPLES / 'sample.vtt')
        vtt.shift(datetime.timedelta(minutes=-1, seconds=30))
        self.assertEqual(vtt[0].start, '00:00:00.000')
        self.assertEqual(vtt[0].end, '00:00:00.000')
        self.assertEqual(vtt[-1].start, '00:00:31.350')
        self.assertEqual(vtt[-1].end, '00:00:34.300')

    def test_shift_from_start(self):
        vtt = webvtt.read(PATH_TO_SAMPLES / 'sample.vtt')
        before = [(c.start, c.end) for c in vtt]

        vtt.shift(3, start='00:00:47.000')

        after = [(c.start, c.end) for c in vtt]
        self.assertEqual(after[:11], before[:11])
        self.assertEqual(after[11], ('00:00:50.000', '00:00:53.970'))
        self.assertEqual(after[-1], ('00:01:04.350', '00:01:07.300'))

    def test_shift_from_start_invalid(self):
        vtt = webvtt.read(PATH_TO_SAMPLES / 'sample.vtt')
        before = [(c.start, c.end) for c in vtt]

        with self.assertRaises(MalformedCaptionError):
            vtt.shift(3, start='47 seconds')

        self.assertEqual([(c.start, c.end) for c in vtt], before)

    def test_shift_invalid_offset(self):
        for value in ('1.5', None, True):
            with self.subTest(value=value):
                with self.assertRaises(TypeError):
                    webvtt.WebVTT().shift(value)

        with self.assertRaises(ValueError):
            webvtt.WebVTT().shift(float('nan'))

    def test_shift_invalid_offset_unchanged(self):
        vtt = webvtt.read(PATH_TO_SAMPLES / 'sample.vtt')
        before = [(c.start, c.end) for c in vtt]

        with self.assertRaises(TypeError):
            vtt.shift('1.5')

        self.assertEqual([(c.start, c.end) for c in vtt], before)

    SYNC_CAPTIONS = textwrap.dedent('''
        WEBVTT

        00:00:01.000 --> 00:00:02.000
        Caption #1

        00:00:10.000 --> 00:00:12.500
        Caption #2

        00:01:40.000 --> 00:01:41.000
        Caption #3
        ''').strip()

    def timings(self, vtt):
        return [(c.start, c.end) for c in vtt]

    def test_sync(self):
        vtt = webvtt.from_string(self.SYNC_CAPTIONS)
        vtt.sync(('00:00:01.000', '00:00:02.000'),
                 ('00:01:40.000', '00:02:00.000'))

        self.assertEqual(
            self.timings(vtt),
            [('00:00:02.000', '00:00:03.192'),
             ('00:00:12.727', '00:00:15.707'),
             ('00:02:00.000', '00:02:01.192')]
            )
        self.assertEqual([c.text for c in vtt],
                         ['Caption #1', 'Caption #2', 'Caption #3'])

    def test_sync_point_types_and_order(self):
        vtt = webvtt.from_string(self.SYNC_CAPTIONS)
        vtt.sync((datetime.timedelta(seconds=100), 120.0),
                 (Timestamp(seconds=1), 2))

        self.assertEqual(
            self.timings(vtt),
            [('00:00:02.000', '00:00:03.192'),
             ('00:00:12.727', '00:00:15.707'),
             ('00:02:00.000', '00:02:01.192')]
            )

    def test_sync_identity(self):
        vtt = webvtt.from_string(self.SYNC_CAPTIONS)
        before = self.timings(vtt)

        vtt.sync(('00:00:05.000', '00:00:05.000'), [50, 50])

        self.assertEqual(self.timings(vtt), before)

    def test_sync_multiple_points(self):
        vtt = webvtt.from_string(self.SYNC_CAPTIONS)
        vtt.sync((0, 0), (10, 10), (100, 190))

        self.assertEqual(
            self.timings(vtt),
            [('00:00:01.000', '00:00:02.000'),
             ('00:00:10.000', '00:00:15.000'),
             ('00:03:10.000', '00:03:12.000')]
            )

    def test_sync_extrapolates_and_clamps_to_zero(self):
        vtt = webvtt.from_string(self.SYNC_CAPTIONS)
        vtt.sync((10, 5), (20, 15))

        self.assertEqual(
            self.timings(vtt),
            [('00:00:00.000', '00:00:00.000'),
             ('00:00:05.000', '00:00:07.500'),
             ('00:01:35.000', '00:01:36.000')]
            )
        self.assertEqual(len(vtt), 3)

    def test_sync_rounds_halves_away_from_zero(self):
        vtt = webvtt.from_string(textwrap.dedent('''
            WEBVTT

            00:00:00.001 --> 00:00:00.003
            Caption
            ''').strip())

        vtt.sync((0, 0), (2, 3))

        self.assertEqual(self.timings(vtt),
                         [('00:00:00.002', '00:00:00.005')])

    def test_sync_rounds_times_before_the_first_point(self):
        vtt = webvtt.from_string(textwrap.dedent('''
            WEBVTT

            00:00:00.009 --> 00:00:00.011
            Caption
            ''').strip())

        # 9 ms is mapped to 8.5 ms and 11 ms to 11.5 ms
        vtt.sync((0.010, 0.010), (0.012, 0.013))

        self.assertEqual(self.timings(vtt),
                         [('00:00:00.009', '00:00:00.012')])

    def test_sync_invalid_points(self):
        for points, error in (
                ((), ValueError),
                (((1, 2),), ValueError),
                (((1, 2), (1, 3)), ValueError),
                (((1, 5), (2, 4)), ValueError),
                (((1, 5), (2, 5)), ValueError),
                (((1, 2), (3, -4)), ValueError),
                (((1, 2), (3, float('nan'))), ValueError),
                (((1, 2), (3,)), TypeError),
                (((1, 2), '34'), TypeError),
                (((1, 2), (3, None)), TypeError),
                (((1, 2), (3, True)), TypeError),
                (((1, 2), ('00:03', 4)), MalformedCaptionError)):
            with self.subTest(points=points):
                vtt = webvtt.from_string(self.SYNC_CAPTIONS)
                before = self.timings(vtt)

                with self.assertRaises(error):
                    vtt.sync(*points)

                self.assertEqual(self.timings(vtt), before)

    def test_sync_no_captions(self):
        vtt = webvtt.WebVTT()
        vtt.sync((1, 2), (3, 4))
        self.assertEqual(vtt.captions, [])

        with self.assertRaises(ValueError):
            vtt.sync((1, 2))

    def test_change_framerate(self):
        vtt = webvtt.from_string(self.SYNC_CAPTIONS)
        vtt.change_framerate(25, 23.976)

        self.assertEqual(
            self.timings(vtt),
            [('00:00:01.043', '00:00:02.085'),
             ('00:00:10.427', '00:00:13.034'),
             ('00:01:44.271', '00:01:45.314')]
            )

        vtt = webvtt.from_string(self.SYNC_CAPTIONS)
        vtt.change_framerate(23.976, 25)

        self.assertEqual(
            self.timings(vtt),
            [('00:00:00.959', '00:00:01.918'),
             ('00:00:09.590', '00:00:11.988'),
             ('00:01:35.904', '00:01:36.863')]
            )

    def test_change_framerate_exact(self):
        captions = textwrap.dedent('''
            WEBVTT

            01:30:00.000 --> 01:30:01.000
            Caption
            ''').strip()

        vtt = webvtt.from_string(captions)
        vtt.change_framerate(25, fractions.Fraction(24000, 1001))
        self.assertEqual(self.timings(vtt),
                         [('01:33:50.625', '01:33:51.668')])

        vtt = webvtt.from_string(captions)
        vtt.change_framerate(25, 23.976)
        self.assertEqual(self.timings(vtt),
                         [('01:33:50.631', '01:33:51.673')])

    def test_change_framerate_same(self):
        vtt = webvtt.from_string(self.SYNC_CAPTIONS)
        before = self.timings(vtt)

        vtt.change_framerate(29.97, 29.97)

        self.assertEqual(self.timings(vtt), before)

    def test_change_framerate_larger_than_a_float(self):
        for fps in (10 ** 400, fractions.Fraction(10 ** 400)):
            with self.subTest(fps=type(fps).__name__):
                vtt = webvtt.from_string(self.SYNC_CAPTIONS)
                before = self.timings(vtt)

                vtt.change_framerate(fps, fps)

                self.assertEqual(self.timings(vtt), before)

    def test_retime_after_largest_timestamp(self):
        # only the end of the last caption is moved after the largest
        # timestamp, 9999999999:59:59.999
        offset = datetime.timedelta(milliseconds=35999999999899000)
        for name, retime in (
                ('shift', lambda vtt: vtt.shift(offset)),
                ('sync', lambda vtt: vtt.sync((0, 0), (1, 10 ** 12))),
                ('change_framerate',
                 lambda vtt: vtt.change_framerate(10 ** 12, 1))):
            with self.subTest(method=name):
                vtt = webvtt.from_string(self.SYNC_CAPTIONS)
                before = self.timings(vtt)

                with self.assertRaises(ValueError):
                    retime(vtt)

                self.assertEqual(self.timings(vtt), before)

    def test_sync_point_after_largest_timestamp(self):
        vtt = webvtt.from_string(self.SYNC_CAPTIONS)
        with self.assertRaises(ValueError):
            vtt.sync((0, 0), (1, 36000000000000))

    def test_change_framerate_invalid(self):
        for fps, error in ((0, ValueError),
                           (-25, ValueError),
                           (fractions.Fraction(0), ValueError),
                           (fractions.Fraction(-24000, 1001), ValueError),
                           (float('nan'), ValueError),
                           (float('inf'), ValueError),
                           ('25', TypeError),
                           (None, TypeError),
                           (True, TypeError)):
            with self.subTest(fps=fps):
                vtt = webvtt.from_string(self.SYNC_CAPTIONS)
                before = self.timings(vtt)

                with self.assertRaises(error):
                    vtt.change_framerate(25, fps)
                with self.assertRaises(error):
                    vtt.change_framerate(fps, 25)

                self.assertEqual(self.timings(vtt), before)

    def test_parse_empty_file(self):
        self.assertRaises(
            MalformedFileError,
            webvtt.read,
            PATH_TO_SAMPLES / 'empty.vtt'
            )

    def test_parse_invalid_timeframe_line(self):
        good_captions = len(
            webvtt.read(PATH_TO_SAMPLES / 'invalid_timeframe.vtt').captions
            )
        self.assertEqual(good_captions, 6)

    def test_parse_cue_timings_in_cue_text_start_new_cue(self):
        vtt = webvtt.read(
            PATH_TO_SAMPLES / 'invalid_timeframe_in_cue_text.vtt'
            )
        self.assertEqual(4, len(vtt.captions))
        self.assertEqual('', vtt.captions[1].text)
        self.assertEqual('00:00:07.000', vtt.captions[2].start)
        self.assertEqual('Caption text #2', vtt.captions[2].text)
        self.assertEqual('Caption text #3', vtt.captions[3].text)

    def test_parse_invalid_timeframe_line_strict(self):
        self.assertRaises(
            MalformedCaptionError,
            webvtt.read,
            PATH_TO_SAMPLES / 'invalid_timeframe.vtt',
            strict=True
            )

    def test_parse_invalid_timeframe_in_cue_text_strict(self):
        self.assertRaises(
            MalformedCaptionError,
            webvtt.read,
            PATH_TO_SAMPLES / 'invalid_timeframe_in_cue_text.vtt',
            strict=True
            )

    def test_parse_valid_file_strict(self):
        vtt = webvtt.read(PATH_TO_SAMPLES / 'sample.vtt', strict=True)
        self.assertEqual(len(vtt.captions), 16)

    def test_parse_non_padded_timestamps(self):
        """https://github.com/glut23/webvtt-py/issues/44"""
        vtt = webvtt.read(PATH_TO_SAMPLES / 'non_padded_timestamps.vtt')
        self.assertEqual(len(vtt.captions), 3)
        self.assertEqual(
            [(caption.start, caption.end) for caption in vtt.captions],
            [('00:00:00.000', '00:00:03.540'),
             ('00:00:03.540', '00:00:07.230'),
             ('00:01:05.200', '01:02:07.950')]
            )
        self.assertEqual(vtt.captions[1].voice, 'John Smith')
        self.assertEqual(vtt.captions[1].text, "Morning, let's get started.")
        self.assertEqual(vtt.captions[2].end_in_seconds, 3727)
        self.assertIn(
            '00:01:05.200 --> 01:02:07.950\n<v Jane Doe>Thanks for joining.',
            vtt.content
            )

    def test_parse_non_padded_timestamps_strict(self):
        self.assertRaises(
            MalformedCaptionError,
            webvtt.read,
            PATH_TO_SAMPLES / 'non_padded_timestamps.vtt',
            strict=True
            )

    def test_parse_get_caption_data(self):
        vtt = webvtt.read(PATH_TO_SAMPLES / 'one_caption.vtt')
        self.assertEqual(vtt.captions[0].start_in_seconds, 0)
        self.assertEqual(vtt.captions[0].start, '00:00:00.500')
        self.assertEqual(vtt.captions[0].end_in_seconds, 7)
        self.assertEqual(vtt.captions[0].end, '00:00:07.000')
        self.assertEqual(vtt.captions[0].lines[0], 'Caption text #1')
        self.assertEqual(len(vtt.captions[0].lines), 1)

    def test_caption_without_timeframe(self):
        vtt = webvtt.read(PATH_TO_SAMPLES / 'missing_timeframe.vtt')
        self.assertEqual(len(vtt.captions), 6)

    def test_caption_without_cue_text(self):
        vtt = webvtt.read(PATH_TO_SAMPLES / 'missing_caption_text.vtt')
        self.assertEqual(len(vtt.captions), 5)
        self.assertEqual(vtt.captions[1].start, '00:00:07.000')
        self.assertEqual(vtt.captions[1].text, '')

    def test_timestamps_format(self):
        vtt = webvtt.read(PATH_TO_SAMPLES / 'sample.vtt')
        self.assertEqual(vtt.captions[2].start, '00:00:11.890')
        self.assertEqual(vtt.captions[2].end, '00:00:16.320')

    def test_parse_timestamp(self):
        self.assertEqual(
            Caption(start='02:03:11.890').start_in_seconds,
            7391
            )

    def test_captions_attribute(self):
        self.assertListEqual(webvtt.WebVTT().captions, [])

    def test_metadata_headers(self):
        vtt = webvtt.read(PATH_TO_SAMPLES / 'metadata_headers.vtt')
        self.assertEqual(len(vtt.captions), 2)

    def test_metadata_headers_multiline(self):
        vtt = webvtt.read(PATH_TO_SAMPLES / 'metadata_headers_multiline.vtt')
        self.assertEqual(len(vtt.captions), 2)
        self.assertListEqual(
            vtt.metadata,
            ['Kind: captions',
             'Language: en',
             'Style:',
             '::cue(c.colorCCCCCC) { color: rgb(204, 204, 204);',
             '}',
             '##'
             ]
            )

    def test_metadata_headers_preserved_on_save(self):
        vtt = webvtt.read(PATH_TO_SAMPLES / 'metadata_headers.vtt')
        self.assertEqual(vtt.header_text, '')
        self.assertListEqual(vtt.metadata, ['Kind: captions', 'Language: en'])

        vtt.shift(1)
        with tempfile.TemporaryDirectory() as td:
            output = os.path.join(td, 'captions.vtt')
            vtt.save(output)

            with open(output, encoding='utf-8') as f:
                self.assertEqual(
                    f.read(),
                    textwrap.dedent('''
                        WEBVTT
                        Kind: captions
                        Language: en

                        00:00:01.500 --> 00:00:08.000
                        Caption text #1

                        00:00:08.000 --> 00:00:12.890
                        Caption text #2
                        ''').lstrip()
                    )

    def test_header_round_trip(self):
        content = textwrap.dedent('''
            WEBVTT - Sample title
            X-TIMESTAMP-MAP=LOCAL:00:00:00.000,MPEGTS:126000

            00:00:00.000 --> 00:00:02.000
             Hello there
            ''').lstrip()

        vtt = webvtt.from_string(content)
        self.assertEqual(vtt.header_text, '- Sample title')
        self.assertListEqual(
            vtt.metadata,
            ['X-TIMESTAMP-MAP=LOCAL:00:00:00.000,MPEGTS:126000']
            )
        self.assertEqual(vtt.content, content)

        vtt = webvtt.from_buffer(io.StringIO(content))
        self.assertEqual(vtt.header_text, '- Sample title')
        out = io.StringIO()
        vtt.write(out)
        self.assertEqual(out.getvalue(), content)

    def test_header_in_new_file(self):
        vtt = webvtt.WebVTT(
            captions=[
                Caption(start='00:00:00.500',
                        end='00:00:07.000',
                        text='Caption #1'
                        )
                ],
            header_text='Sample title'
            )
        vtt.metadata.append('Language: en')

        self.assertEqual(
            vtt.content,
            textwrap.dedent('''
                WEBVTT Sample title
                Language: en

                00:00:00.500 --> 00:00:07.000
                Caption #1
                ''').lstrip()
            )

    def test_save_header_with_other_unicode_line_separators(self):
        content = (
            'WEBVTT title\u2028more\n'
            'Kind: a\x0cb\n'
            '\n'
            '00:00:00.500 --> 00:00:07.000\n'
            'Caption #1\n'
            )
        with tempfile.TemporaryDirectory() as td:
            source = os.path.join(td, 'source.vtt')
            with open(source, 'w', encoding='utf-8', newline='') as f:
                f.write(content)

            vtt = webvtt.read(source)
            self.assertEqual(vtt.header_text, 'title\u2028more')
            self.assertListEqual(vtt.metadata, ['Kind: a\x0cb'])

            output = os.path.join(td, 'output.vtt')
            vtt.save(output)
            with open(output, encoding='utf-8', newline='') as f:
                # lines end with the line separator of the platform
                self.assertEqual(f.read(), content.replace('\n', os.linesep))

    def test_save_error_keeps_file(self):
        with tempfile.TemporaryDirectory() as td:
            vtt_file = os.path.join(td, 'captions.vtt')
            srt_file = os.path.join(td, 'captions.srt')
            vtt_content = textwrap.dedent('''
                WEBVTT

                00:00:00.500 --> 00:00:07.000
                Café
                ''').lstrip()
            pathlib.Path(vtt_file).write_text(vtt_content, encoding='utf-8')
            pathlib.Path(srt_file).write_text('old', encoding='utf-8')
            vtt = webvtt.read(vtt_file)

            for save in (lambda: vtt.save(encoding='ascii'),
                         lambda: vtt.save_as_srt(srt_file, encoding='ascii')):
                with self.assertRaises(UnicodeEncodeError):
                    save()

            self.assertEqual(
                pathlib.Path(vtt_file).read_text(encoding='utf-8'),
                vtt_content
                )
            self.assertEqual(pathlib.Path(srt_file).read_text(), 'old')
            self.assertEqual(sorted(os.listdir(td)),
                             ['captions.srt', 'captions.vtt'])
            self.assertEqual(vtt.file, vtt_file)

    def test_save_text_not_read_back_keeps_file(self):
        with tempfile.TemporaryDirectory() as td:
            vtt_file = os.path.join(td, 'captions.vtt')
            pathlib.Path(vtt_file).write_text(
                (PATH_TO_SAMPLES / 'one_caption.vtt').read_text()
                )
            vtt = webvtt.read(vtt_file)
            vtt.captions[0].text = 'line 1\n\nline 2'

            with self.assertRaises(ValueError):
                vtt.save()

            self.assertEqual(
                pathlib.Path(vtt_file).read_text(),
                (PATH_TO_SAMPLES / 'one_caption.vtt').read_text()
                )
            self.assertEqual(vtt.file, vtt_file)

    def test_save_invalid_metadata(self):
        vtt = webvtt.WebVTT(metadata=['Kind: captions', ''])
        with tempfile.TemporaryDirectory() as td:
            output = os.path.join(td, 'captions.vtt')
            with self.assertRaises(ValueError):
                vtt.save(output)
            self.assertFalse(os.path.exists(output))
            self.assertIsNone(vtt.file)

    def test_header_not_in_srt(self):
        vtt = webvtt.from_string(
            textwrap.dedent('''
                WEBVTT - Sample title
                Language: en

                00:00:00.500 --> 00:00:07.000
                Caption #1
                ''').lstrip()
            )
        out = io.StringIO()
        vtt.write(out, format='srt')
        self.assertEqual(
            out.getvalue(),
            '1\n00:00:00,500 --> 00:00:07,000\nCaption #1'
            )

    def test_parse_identifiers(self):
        vtt = webvtt.read(PATH_TO_SAMPLES / 'using_identifiers.vtt')
        self.assertEqual(len(vtt.captions), 6)

        self.assertEqual(vtt.captions[1].identifier, 'second caption')
        self.assertEqual(vtt.captions[2].identifier, None)
        self.assertEqual(vtt.captions[3].identifier, '4')

    def test_parse_comments(self):
        vtt = webvtt.read(PATH_TO_SAMPLES / 'comments.vtt')
        self.assertEqual(len(vtt.captions), 3)
        self.assertListEqual(
            vtt.captions[0].lines,
            ['- Ta en kopp varmt te.',
             '- Det är inte varmt.']
            )
        self.assertListEqual(
            vtt.captions[0].comments,
            []
            )
        self.assertListEqual(
            vtt.captions[1].comments,
            []
            )
        self.assertEqual(
            vtt.captions[2].text,
            '- Ta en kopp'
            )
        self.assertListEqual(
            vtt.captions[2].comments,
            ['This last line may not translate well.']
            )
        self.assertListEqual(
            vtt.header_comments,
            ['This translation was done by Kyle so that\n'
             'some friends can watch it with their parents.'
             ]
            )
        self.assertListEqual(
            vtt.footer_comments,
            ['end of file']
            )

    def test_parse_styles(self):
        vtt = webvtt.read(PATH_TO_SAMPLES / 'styles.vtt')
        self.assertEqual(len(vtt.captions), 1)
        self.assertEqual(
            vtt.styles[0].text,
            '::cue {\n  background-image: linear-gradient(to bottom, '
            'dimgray, lightgray);\n  color: papayawhip;\n}'
            )

    def test_parse_regions(self):
        vtt = webvtt.read(PATH_TO_SAMPLES / 'regions.vtt')
        self.assertEqual(len(vtt.regions), 2)
        self.assertEqual(vtt.regions[0].id, 'fred')
        self.assertEqual(vtt.regions[1].regionanchor, '100%,100%')
        self.assertEqual(len(vtt.captions), 2)
        self.assertEqual(vtt.captions[1].settings.region, 'bill')

    def test_parse_regions_strict(self):
        vtt = webvtt.read(PATH_TO_SAMPLES / 'regions.vtt', strict=True)
        self.assertEqual(len(vtt.regions), 2)

    def test_save_regions(self):
        with named_temporary_file('w', suffix='.vtt') as f:
            webvtt.read(PATH_TO_SAMPLES / 'regions.vtt').save(f.name)
            self.assertEqual(
                pathlib.Path(f.name).read_text(encoding='utf-8'),
                (PATH_TO_SAMPLES / 'regions.vtt').read_text(encoding='utf-8')
                )

    def test_regions_from_buffer(self):
        with open(PATH_TO_SAMPLES / 'regions.vtt', encoding='utf-8') as f:
            vtt = webvtt.from_buffer(f)
        self.assertListEqual(
            [region.id for region in vtt.regions],
            ['fred', 'bill']
            )

    def test_regions_from_string(self):
        vtt = webvtt.from_string(
            'WEBVTT\n\nREGION\nid:fred\n\n'
            '00:00:00.500 --> 00:00:04.300 region:fred\nCaption text\n'
            )
        self.assertEqual(vtt.regions[0].id, 'fred')

    def test_without_regions(self):
        self.assertListEqual(webvtt.WebVTT().regions, [])
        vtt = webvtt.read(PATH_TO_SAMPLES / 'sample.vtt')
        self.assertListEqual(vtt.regions, [])

    def test_create_regions(self):
        vtt = webvtt.WebVTT(
            captions=[
                Caption('00:00:00.500', '00:00:04.300', 'Caption text',
                        settings='region:fred')
                ],
            regions=[Region(id='fred', width='40%')]
            )
        vtt.regions.append(Region(id='bill'))
        self.assertEqual(
            vtt.content,
            'WEBVTT\n\nREGION\nid:fred\nwidth:40%\n\nREGION\nid:bill\n\n'
            '00:00:00.500 --> 00:00:04.300 region:fred\nCaption text\n'
            )

    def test_write_regions(self):
        output = io.StringIO()
        webvtt.read(PATH_TO_SAMPLES / 'regions.vtt').write(output)
        self.assertIn('REGION\nid:bill\n', output.getvalue())

    def test_save_as_srt_without_regions(self):
        output = io.StringIO()
        webvtt.read(PATH_TO_SAMPLES / 'regions.vtt').write(output, 'srt')
        self.assertNotIn('REGION', output.getvalue())
        self.assertNotIn('region', output.getvalue())

    def test_parse_styles_with_comments(self):
        vtt = webvtt.read(PATH_TO_SAMPLES / 'styles_with_comments.vtt')
        self.assertEqual(len(vtt.captions), 1)
        self.assertEqual(len(vtt.styles), 2)
        self.assertEqual(
            vtt.styles[0].comments,
            []
            )
        self.assertEqual(
            vtt.styles[0].text,
            '::cue {\n'
            '  background-image: linear-gradient(to bottom, dimgray, '
            'lightgray);\n'
            '  color: papayawhip;\n'
            '}'
            )
        self.assertEqual(
            vtt.styles[1].comments,
            ['This is the second block of styles',
             'Multiline comment for the same\nsecond block of styles'
             ]
            )
        self.assertEqual(
            vtt.styles[1].text,
            '::cue(b) {\n'
            '  color: peachpuff;\n'
            '}'
            )
        self.assertListEqual(
            vtt.header_comments,
            ['Sample of comments with styles']
            )
        self.assertListEqual(
            vtt.footer_comments,
            []
            )

    def test_multiple_comments_everywhere(self):
        vtt = webvtt.WebVTT.from_string(textwrap.dedent("""
            WEBVTT

            NOTE Test file

            NOTE this file is testing multiple comments
            in different places

            STYLE
            ::cue {
              background-image: linear-gradient(to bottom, dimgray, lightgray);
              color: papayawhip;
            }

            NOTE this style uses nice color

            NOTE check how it looks before proceeding

            STYLE
            ::cue(b) {
              color: peachpuff;
            }

            00:00:00.500 --> 00:00:07.000
            Caption text #1

            NOTE next caption has two lines

            NOTE needs review

            00:00:07.000 --> 00:00:11.890
            Caption text #2 line 1
            Caption text #2 line 2

            00:00:11.890 --> 00:00:16.320
            Caption text #3

            00:00:16.320 --> 00:00:21.580
            Caption text #4

            NOTE Copyright 2024

            NOTE this is the end of the file
            """).strip()
            )

        self.assertListEqual(
            vtt.header_comments,
            ['Test file',
             'this file is testing multiple comments\nin different places'
             ]
            )
        self.assertListEqual(
            vtt.footer_comments,
            ['Copyright 2024',
             'this is the end of the file'
             ]
            )
        self.assertListEqual(
            vtt.captions[0].comments,
            []
            )
        self.assertListEqual(
            vtt.captions[1].comments,
            ['next caption has two lines',
             'needs review'
             ]
            )
        self.assertListEqual(
            vtt.captions[2].comments,
            []
            )
        self.assertListEqual(
            vtt.captions[3].comments,
            []
            )
        self.assertListEqual(
            vtt.styles[0].comments,
            []
            )
        self.assertListEqual(
            vtt.styles[1].comments,
            ['this style uses nice color',
             'check how it looks before proceeding'
             ]
            )

    def test_comments_in_new_file(self):
        with named_temporary_file('r', suffix='.vtt', encoding='utf-8') as f:
            vtt = webvtt.WebVTT()
            vtt.header_comments.append('This is a header comment')
            vtt.header_comments.append(
                'where we can see a\ntwo line comment'
                )
            vtt.styles.append(
                Style('::cue(b) {\n  color: peachpuff;\n}')
                )
            style = Style('::cue {\n  color: papayawhip;\n}')
            style.comments.append('Another style to test\nthe look and feel')
            style.comments.append('Please check')
            vtt.styles.append(style)
            vtt.captions.append(
                Caption(start='00:00:00.500',
                        end='00:00:07.000',
                        text='Caption #1',
                        )
                )
            caption = Caption(start='00:00:07.000',
                              end='00:00:11.890',
                              text='Caption #2'
                              )
            caption.comments.append(
                'Second caption may be a bit off\nand needs checking'
                )
            caption.comments.append('Confirm if it displays correctly')
            vtt.captions.append(caption)
            vtt.footer_comments.append('This is a footer comment')
            vtt.footer_comments.append(
                'where we can also see a\ntwo line comment'
                )

            vtt.save(f.name)
            self.assertEqual(
                f.read(),
                textwrap.dedent('''
                    WEBVTT

                    NOTE This is a header comment

                    NOTE
                    where we can see a
                    two line comment

                    STYLE
                    ::cue(b) {
                      color: peachpuff;
                    }

                    NOTE
                    Another style to test
                    the look and feel

                    NOTE Please check

                    STYLE
                    ::cue {
                      color: papayawhip;
                    }

                    00:00:00.500 --> 00:00:07.000
                    Caption #1

                    NOTE
                    Second caption may be a bit off
                    and needs checking

                    NOTE Confirm if it displays correctly

                    00:00:07.000 --> 00:00:11.890
                    Caption #2

                    NOTE This is a footer comment

                    NOTE
                    where we can also see a
                    two line comment
                    ''').strip()
                )

    def test_clean_cue_tags(self):
        vtt = webvtt.read(PATH_TO_SAMPLES / 'cue_tags.vtt')
        self.assertEqual(
            vtt.captions[1].text,
            'Like a big-a pizza pie'
            )
        self.assertEqual(
            vtt.captions[2].text,
            'That\'s amore'
            )

    def test_parse_captions_with_bom(self):
        vtt = webvtt.read(PATH_TO_SAMPLES / 'captions_with_bom.vtt')
        self.assertEqual(len(vtt.captions), 4)

    def test_empty_lines_are_not_included_in_result(self):
        vtt = webvtt.read(PATH_TO_SAMPLES / 'netflix_chicas_del_cable.vtt')
        self.assertEqual(vtt.captions[0].text, "[Alba] En 1928,")
        self.assertEqual(
            vtt.captions[-2].text,
            "Diez años no son suficientes\npara olvidarte..."
            )

    def test_can_parse_youtube_dl_files(self):
        vtt = webvtt.read(PATH_TO_SAMPLES / 'youtube_dl.vtt')
        self.assertEqual(len(vtt.captions), 4)
        self.assertEqual('00:04:46.470', vtt.captions[1].start)
        self.assertEqual('yeah\nwhat', vtt.captions[1].text)
        self.assertEqual(
            "this will happen is I'm telling",
            vtt.captions[2].text
            )
        self.assertEqual(
            "this will happen is I'm telling\n ",
            vtt.captions[3].text
            )

    def test_parse_voice_spans(self):
        vtt = webvtt.from_string(textwrap.dedent("""
            WEBVTT

            00:00:00.000 --> 00:00:00.800
            <v.quiet.slow Lisa Simpson>Knock knock</v>

            00:00:02.100 --> 00:00:06.500
            <v Homer Simpson>Who's there?</v>

            00:00:10.530 --> 00:00:11.090
            <v.loud Lisa Simpson>Atish</v>
            """).strip()
            )
        self.assertEqual(len(vtt), 3)
        self.assertEqual(
            str(vtt[0]),
            '00:00:00.000 00:00:00.800 Knock knock'
            )
        self.assertEqual(
            vtt[0].voice,
            'Lisa Simpson'
            )
        self.assertEqual(
            str(vtt[1]),
            '00:00:02.100 00:00:06.500 Who\'s there?'
            )
        self.assertEqual(
            vtt[1].voice,
            'Homer Simpson'
            )
        self.assertEqual(
            str(vtt[2]),
            '00:00:10.530 00:00:11.090 Atish'
            )
        self.assertEqual(
            vtt[2].voice,
            'Lisa Simpson'
            )

    def test_parse_caption_not_a_voice_span(self):
        vtt = webvtt.from_string(textwrap.dedent("""
            WEBVTT

            00:00:00.000 --> 00:00:00.800
            <v Not an actual voice span here
            """).strip()
            )
        self.assertEqual(len(vtt), 1)
        self.assertEqual(
            str(vtt[0]),
            '00:00:00.000 00:00:00.800 <v Not an actual voice span here'
            )
        self.assertIsNone(vtt[0].voice)


class TestParseSRT(unittest.TestCase):

    def test_parse_empty_file(self):
        self.assertRaises(
            webvtt.errors.MalformedFileError,
            webvtt.from_srt,
            # We reuse this file as it is empty and serves the purpose.
            PATH_TO_SAMPLES / 'empty.vtt'
            )

    def test_invalid_format(self):
        for i in range(1, 5):
            self.assertRaises(
                MalformedFileError,
                webvtt.from_srt,
                PATH_TO_SAMPLES / f'invalid_format{i}.srt'
                )

    def test_total_length(self):
        self.assertEqual(
            webvtt.from_srt(PATH_TO_SAMPLES / 'sample.srt').total_length,
            23
            )

    def test_parse_captions(self):
        self.assertTrue(
            webvtt.from_srt(PATH_TO_SAMPLES / 'sample.srt').captions
            )

    def test_missing_timeframe_line(self):
        self.assertEqual(
            len(webvtt.from_srt(
                PATH_TO_SAMPLES / 'missing_timeframe.srt').captions
                ),
            4
            )

    def test_empty_caption_text(self):
        self.assertTrue(
            webvtt.from_srt(
                PATH_TO_SAMPLES / 'missing_caption_text.srt').captions
            )

    def test_empty_gets_removed(self):
        captions = webvtt.from_srt(
            PATH_TO_SAMPLES / 'missing_caption_text.srt'
            ).captions
        self.assertEqual(len(captions), 4)

    def test_invalid_timestamp(self):
        self.assertEqual(
            len(webvtt.from_srt(
                PATH_TO_SAMPLES / 'invalid_timeframe.srt'
                ).captions),
            4
            )

    def test_timestamps_format(self):
        vtt = webvtt.from_srt(PATH_TO_SAMPLES / 'sample.srt')
        self.assertEqual(vtt.captions[2].start, '00:00:11.890')
        self.assertEqual(vtt.captions[2].end, '00:00:16.320')

    def test_parse_get_caption_data(self):
        vtt = webvtt.from_srt(PATH_TO_SAMPLES / 'one_caption.srt')
        self.assertEqual(vtt.captions[0].start_in_seconds, 0)
        self.assertEqual(vtt.captions[0].start, '00:00:00.500')
        self.assertEqual(vtt.captions[0].end_in_seconds, 7)
        self.assertEqual(vtt.captions[0].end, '00:00:07.000')
        self.assertEqual(vtt.captions[0].lines[0], 'Caption text #1')
        self.assertEqual(len(vtt.captions[0].lines), 1)


class TestParseSBV(unittest.TestCase):

    def test_parse_empty_file(self):
        self.assertRaises(
            MalformedFileError,
            webvtt.from_sbv,
            # We reuse this file as it is empty and serves the purpose.
            PATH_TO_SAMPLES / 'empty.vtt'
            )

    def test_invalid_format(self):
        self.assertRaises(
            MalformedFileError,
            webvtt.from_sbv,
            PATH_TO_SAMPLES / 'invalid_format.sbv'
            )

    def test_total_length(self):
        self.assertEqual(
            webvtt.from_sbv(PATH_TO_SAMPLES / 'sample.sbv').total_length,
            16
            )

    def test_parse_captions(self):
        self.assertEqual(
            len(webvtt.from_sbv(PATH_TO_SAMPLES / 'sample.sbv').captions),
            5
            )

    def test_missing_timeframe_line(self):
        self.assertEqual(
            len(webvtt.from_sbv(
                PATH_TO_SAMPLES / 'missing_timeframe.sbv'
                ).captions),
            4
            )

    def test_missing_caption_text(self):
        self.assertTrue(
            webvtt.from_sbv(
                PATH_TO_SAMPLES / 'missing_caption_text.sbv'
                ).captions
            )

    def test_invalid_timestamp(self):
        self.assertEqual(
            len(webvtt.from_sbv(
                PATH_TO_SAMPLES / 'invalid_timeframe.sbv'
                ).captions),
            4
            )

    def test_timestamps_format(self):
        vtt = webvtt.from_sbv(PATH_TO_SAMPLES / 'sample.sbv')
        self.assertEqual(vtt.captions[1].start, '00:00:11.378')
        self.assertEqual(vtt.captions[1].end, '00:00:12.305')

    def test_timestamps_in_seconds(self):
        vtt = webvtt.from_sbv(PATH_TO_SAMPLES / 'sample.sbv')
        self.assertEqual(vtt.captions[1].start_in_seconds, 11)
        self.assertEqual(vtt.captions[1].end_in_seconds, 12)

    def test_get_caption_text(self):
        vtt = webvtt.from_sbv(PATH_TO_SAMPLES / 'sample.sbv')
        self.assertEqual(vtt.captions[1].text, 'Caption text #2')

    def test_get_caption_text_multiline(self):
        vtt = webvtt.from_sbv(PATH_TO_SAMPLES / 'sample.sbv')
        self.assertEqual(
            vtt.captions[2].text,
            'Caption text #3 (line 1)\nCaption text #3 (line 2)'
            )
        self.assertListEqual(
            vtt.captions[2].lines,
            ['Caption text #3 (line 1)', 'Caption text #3 (line 2)']
            )

    def test_convert_from_srt_to_vtt_and_back_gives_same_file(self):
        with named_temporary_file('w', suffix='.srt') as f:
            webvtt.from_srt(
                PATH_TO_SAMPLES / 'sample.srt'
                ).save_as_srt(f.name)

            self.assertEqual(
                pathlib.Path(PATH_TO_SAMPLES / 'sample.srt').read_text(),
                pathlib.Path(f.name).read_text()
                )

    def test_convert_to_srt_keeping_formatting(self):
        with named_temporary_file('w', suffix='.srt') as f:
            webvtt.read(
                PATH_TO_SAMPLES / 'styles_colours.vtt'
                ).save_as_srt(f.name, keep_formatting=True)

            self.assertEqual(
                (PATH_TO_SAMPLES / 'styles_colours.srt').read_text(),
                pathlib.Path(f.name).read_text()
                )

    def test_save_file_with_bom(self):
        with named_temporary_file('r', suffix='.vtt', encoding='utf-8') as f:
            webvtt.read(
                PATH_TO_SAMPLES / 'one_caption.vtt'
                ).save(f.name, add_bom=True)
            self.assertEqual(
                f.read(),
                textwrap.dedent(f'''
                    {CODEC_BOMS['utf-8'].decode()}WEBVTT

                    00:00:00.500 --> 00:00:07.000
                    Caption text #1
                    ''').strip() + '\n'
                )

    def test_save_file_with_bom_keeps_bom(self):
        with named_temporary_file('r', suffix='.vtt', encoding='utf-8') as f:
            webvtt.read(
                PATH_TO_SAMPLES / 'captions_with_bom.vtt'
            ).save(f.name)
            self.assertEqual(
                f.read(),
                textwrap.dedent(f'''
                    {CODEC_BOMS['utf-8'].decode()}WEBVTT

                    00:00:00.500 --> 00:00:07.000
                    Caption text #1

                    00:00:07.000 --> 00:00:11.890
                    Caption text #2

                    00:00:11.890 --> 00:00:16.320
                    Caption text #3

                    00:00:16.320 --> 00:00:21.580
                    Caption text #4
                    ''').strip() + '\n'
                )

    def test_save_file_with_bom_removes_bom_if_requested(self):
        with named_temporary_file('r', suffix='.vtt', encoding='utf-8') as f:
            webvtt.read(
                PATH_TO_SAMPLES / 'captions_with_bom.vtt'
            ).save(f.name, add_bom=False)
            self.assertEqual(
                f.read(),
                textwrap.dedent(f'''
                    WEBVTT

                    00:00:00.500 --> 00:00:07.000
                    Caption text #1

                    00:00:07.000 --> 00:00:11.890
                    Caption text #2

                    00:00:11.890 --> 00:00:16.320
                    Caption text #3

                    00:00:16.320 --> 00:00:21.580
                    Caption text #4
                    ''').strip() + '\n'
                )

    def test_save_file_with_encoding(self):
        with named_temporary_file('rb', suffix='.vtt') as f:
            webvtt.read(
                PATH_TO_SAMPLES / 'one_caption.vtt'
            ).save(f.name,
                   encoding='utf-32-le'
                   )
            # lines end with the line separator of the platform
            self.assertEqual(
                f.read().decode('utf-32-le'),
                (textwrap.dedent('''
                    WEBVTT

                    00:00:00.500 --> 00:00:07.000
                    Caption text #1
                    ''').strip() + '\n').replace('\n', os.linesep)
                )

    def test_save_file_with_encoding_and_bom(self):
        with named_temporary_file('rb', suffix='.vtt') as f:
            webvtt.read(
                PATH_TO_SAMPLES / 'one_caption.vtt'
            ).save(f.name,
                   encoding='utf-32-le',
                   add_bom=True
                   )
            # lines end with the line separator of the platform
            self.assertEqual(
                f.read().decode('utf-32-le'),
                (textwrap.dedent(f'''
                    {CODEC_BOMS['utf-32-le'].decode('utf-32-le')}WEBVTT

                    00:00:00.500 --> 00:00:07.000
                    Caption text #1
                    ''').strip() + '\n').replace('\n', os.linesep)
                )

    def test_save_new_file_utf_8_default_encoding_no_bom(self):
        with named_temporary_file('r', suffix='.vtt', encoding='utf-8') as f:
            vtt = webvtt.WebVTT()
            vtt.captions.append(
                Caption(start='00:00:00.500',
                        end='00:00:07.000',
                        text='Caption text #1'
                        )
                )
            vtt.save(f.name)
            self.assertEqual(vtt.encoding, 'utf-8')
            self.assertEqual(
                f.read(),
                textwrap.dedent(f'''
                    WEBVTT

                    00:00:00.500 --> 00:00:07.000
                    Caption text #1
                    ''').strip() + '\n'
                )

    def test_save_new_file_utf_8_default_encoding_with_bom(self):
        with named_temporary_file('r', suffix='.vtt', encoding='utf-8') as f:
            vtt = webvtt.WebVTT()
            vtt.captions.append(
                Caption(start='00:00:00.500',
                        end='00:00:07.000',
                        text='Caption text #1'
                        )
                )
            vtt.save(f.name,
                     add_bom=True
                     )
            self.assertEqual(vtt.encoding, 'utf-8')
            self.assertEqual(
                f.read(),
                textwrap.dedent(f'''
                    {CODEC_BOMS['utf-8'].decode()}WEBVTT

                    00:00:00.500 --> 00:00:07.000
                    Caption text #1
                    ''').strip() + '\n'
                )

    def test_iter_slice(self):
        vtt = webvtt.read(
                PATH_TO_SAMPLES / 'sample.vtt'
                )
        slice_of_captions = vtt.iter_slice(start='00:00:11.000',
                                           end='00:00:27.000'
                                           )
        for expected_caption in (vtt.captions[2],
                                 vtt.captions[3],
                                 vtt.captions[4]
                                 ):
            self.assertIs(expected_caption, next(slice_of_captions))

        with self.assertRaises(StopIteration):
            next(slice_of_captions)

    def test_iter_slice_no_start_time(self):
        vtt = webvtt.read(
                PATH_TO_SAMPLES / 'sample.vtt'
                )
        slice_of_captions = vtt.iter_slice(end='00:00:27.000')
        for expected_caption in (vtt.captions[0],
                                 vtt.captions[1],
                                 vtt.captions[2],
                                 vtt.captions[3],
                                 vtt.captions[4]
                                 ):
            self.assertIs(expected_caption, next(slice_of_captions))

        with self.assertRaises(StopIteration):
            next(slice_of_captions)

    def test_iter_slice_no_end_time(self):
        vtt = webvtt.read(
                PATH_TO_SAMPLES / 'sample.vtt'
                )
        slice_of_captions = vtt.iter_slice(start='00:00:47.000')
        for expected_caption in (vtt.captions[11],
                                 vtt.captions[12],
                                 vtt.captions[13],
                                 vtt.captions[14],
                                 vtt.captions[15]
                                 ):
            self.assertIs(expected_caption, next(slice_of_captions))

        with self.assertRaises(StopIteration):
            next(slice_of_captions)
