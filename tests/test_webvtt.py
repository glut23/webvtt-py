import codecs
import datetime
import fractions
import unittest
import os
import io
import textwrap
import warnings
import tempfile
import shutil
import pathlib

import webvtt
from webvtt.models import Caption, Region, Style, Timestamp
from webvtt.utils import CODEC_BOMS
from webvtt.errors import (
    MalformedFileError, MalformedCaptionError, MissingFilenameError
    )

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
            ''').strip() + '\n'
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
            ''').strip() + '\n'
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

    def test_save_specific_filename_other_extension(self):
        vtt = webvtt.read(PATH_TO_SAMPLES / 'one_caption.vtt')
        for name in ('captions.webvtt', 'captions.txt', 'captions.VTT'):
            with self.subTest(name=name), \
                    tempfile.TemporaryDirectory() as td:
                output = pathlib.Path(td) / name
                vtt.save(output)

                self.assertEqual(os.listdir(td), [name])
                self.assertEqual(vtt.file, str(output))

    def test_save_as_srt_extension(self):
        vtt = webvtt.read(PATH_TO_SAMPLES / 'one_caption.vtt')
        for name, saved in (('captions', 'captions.srt'),
                            ('captions.txt', 'captions.txt')):
            with self.subTest(name=name), \
                    tempfile.TemporaryDirectory() as td:
                vtt.save_as_srt(pathlib.Path(td) / name)

                self.assertEqual(os.listdir(td), [saved])

    def test_save_without_output_keeps_format_extension(self):
        content = (PATH_TO_SAMPLES / 'one_caption.vtt').read_text()
        for name in ('captions.vtt', 'captions.webvtt', 'captions.VTT'):
            with self.subTest(name=name), \
                    tempfile.TemporaryDirectory() as td:
                path = os.path.join(td, name)
                pathlib.Path(path).write_text(content)
                vtt = webvtt.read(path)
                vtt.save()

                self.assertEqual(os.listdir(td), [name])
                self.assertEqual(vtt.file, path)

    def test_save_without_output_converted_file(self):
        for sample, name, read, saved in (
                ('sample.srt', 'in.srt', webvtt.from_srt, 'in.vtt'),
                ('sample.sbv', 'in.sbv', webvtt.from_sbv, 'in.vtt'),
                ('sample.vtt', 'in.txt', webvtt.read, 'in.vtt')):
            with self.subTest(name=name), \
                    tempfile.TemporaryDirectory() as td:
                path = os.path.join(td, name)
                shutil.copy(PATH_TO_SAMPLES / sample, path)
                vtt = read(path)
                vtt.save()

                self.assertEqual(sorted(os.listdir(td)), sorted({name, saved}))
                self.assertEqual(vtt.file, os.path.join(td, saved))

    def test_save_as_srt_keeps_srt_encoding(self):
        srt = '1\n00:00:00,500 --> 00:00:07,000\nCafé\n'
        with tempfile.TemporaryDirectory() as td:
            path = pathlib.Path(td, 'captions.srt')
            path.write_bytes(srt.encode('cp1252'))
            for vtt in (webvtt.from_srt(path, encoding='cp1252'),
                        webvtt.from_buffer(
                            io.BytesIO(srt.encode('cp1252')),
                            format='srt',
                            encoding='cp1252'
                            )):
                with self.subTest(file=vtt.file):
                    output = pathlib.Path(td, 'output.srt')
                    vtt.save_as_srt(output)
                    self.assertIn('Café'.encode('cp1252'),
                                  output.read_bytes())

                    # an encoding given when saving is used instead
                    vtt.save_as_srt(output, encoding='utf-8')
                    self.assertIn('Café'.encode('utf-8'), output.read_bytes())

                    # WebVTT is saved in UTF-8
                    vtt.save(pathlib.Path(td, 'output.vtt'))
                    self.assertIn(
                        'Café'.encode('utf-8'),
                        pathlib.Path(td, 'output.vtt').read_bytes()
                        )

    def test_save_as_srt_default_encoding(self):
        srt = '1\n00:00:00,500 --> 00:00:07,000\nCafé\n'
        sbv = '0:00:00.500,0:00:07.000\nCafé\n'
        vtt = 'WEBVTT\n\n00:00:00.500 --> 00:00:07.000\nCafé\n'
        with tempfile.TemporaryDirectory() as td:
            def write(name, data):
                path = pathlib.Path(td, name)
                path.write_bytes(data)
                return path

            for captions in (
                    webvtt.read(
                        write('latin-1.vtt', vtt.encode('latin-1')),
                        encoding='latin-1'
                        ),
                    webvtt.from_sbv(
                        write('latin-1.sbv', sbv.encode('latin-1')),
                        encoding='latin-1'
                        ),
                    # the Byte Order Mark is used instead of the encoding
                    webvtt.from_srt(
                        write('bom.srt', codecs.BOM_UTF8 + srt.encode()),
                        encoding='latin-1'
                        ),
                    # text is already decoded
                    webvtt.from_buffer(io.StringIO(srt), format='srt',
                                       encoding='latin-1'),
                    webvtt.from_srt(write('utf-8.srt', srt.encode()))):
                with self.subTest(file=captions.file):
                    output = pathlib.Path(td, 'output.srt')
                    captions.save_as_srt(output)

                    self.assertIn('Café'.encode('utf-8'), output.read_bytes())

    def test_save_without_encoding_after_reading_with_encoding(self):
        with tempfile.TemporaryDirectory() as td:
            path = pathlib.Path(td, 'captions.vtt')
            path.write_bytes(
                'WEBVTT\n\n00:00:00.500 --> 00:00:07.000\nCafé\n'
                .encode('latin-1')
                )
            vtt = webvtt.read(path, encoding='latin-1')
            vtt.save()

            self.assertIn('Café'.encode('utf-8'), path.read_bytes())

    def test_save_as_srt_captions_without_text_round_trip(self):
        vtt = webvtt.WebVTT(captions=[
            Caption('00:00:00.000', '00:00:01.000', ' '),
            Caption('00:00:01.000', '00:00:02.000', 'b'),
            Caption('00:00:02.000', '00:00:03.000', ['c', 'd']),
            Caption('00:00:03.000', '00:00:04.000', ''),
            ])

        for keep_formatting in (False, True):
            with self.subTest(keep_formatting=keep_formatting), \
                    tempfile.TemporaryDirectory() as td:
                path = os.path.join(td, 'out.srt')
                vtt.save_as_srt(path, keep_formatting=keep_formatting)

                self.assertEqual(
                    [(c.start, c.end, c.lines)
                     for c in webvtt.from_srt(path).captions],
                    [('00:00:01.000', '00:00:02.000', ['b']),
                     ('00:00:02.000', '00:00:03.000', ['c', 'd'])]
                    )
                self.assertTrue(
                    pathlib.Path(path).read_text().startswith('1\n')
                    )

    def test_save_as_srt_without_output(self):
        for sample, name, read, saved in (
                ('sample.vtt', 'in.vtt', webvtt.read, 'in.srt'),
                ('sample.vtt', 'in.webvtt', webvtt.read, 'in.srt'),
                ('sample.srt', 'in.SRT', webvtt.from_srt, 'in.SRT')):
            with self.subTest(name=name), \
                    tempfile.TemporaryDirectory() as td:
                path = os.path.join(td, name)
                shutil.copy(PATH_TO_SAMPLES / sample, path)
                vtt = read(path)
                vtt.save_as_srt()

                self.assertEqual(sorted(os.listdir(td)), sorted({name, saved}))
                self.assertEqual(vtt.file, os.path.join(td, saved))

    def test_save_to_folder_keeps_format_extension(self):
        with tempfile.TemporaryDirectory() as td:
            path = os.path.join(td, 'captions.webvtt')
            shutil.copy(PATH_TO_SAMPLES / 'sample.vtt', path)
            vtt = webvtt.read(path)
            folder = os.path.join(td, 'folder')
            os.mkdir(folder)

            vtt.save(folder)
            vtt.file = path
            vtt.save_as_srt(folder)

            self.assertEqual(sorted(os.listdir(folder)),
                             ['captions.srt', 'captions.webvtt'])

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
                self.assertEqual(len(warns), 1)
                self.assertIs(warns[0].category, DeprecationWarning)
                self.assertEqual(
                    'Deprecated: use from_buffer instead.',
                    str(warns[0].message)
                    )
                # the warning points to the code calling read_buffer
                self.assertEqual(os.path.basename(warns[0].filename),
                                 os.path.basename(__file__))

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

    def test_from_buffer_strict_srt_and_sbv(self):
        for format, sample in (('srt', 'sample.srt'), ('sbv', 'sample.sbv')):
            with self.subTest(format=format), \
                    open(PATH_TO_SAMPLES / sample, encoding='utf-8') as f:
                with self.assertRaises(ValueError) as cm:
                    webvtt.from_buffer(f, format=format, strict=True)

                self.assertEqual(
                    str(cm.exception),
                    f'Strict parsing is not supported for the {format} '
                    'format'
                    )
                # the buffer is not read
                self.assertEqual(f.tell(), 0)
                self.assertTrue(
                    webvtt.from_buffer(f, format=format, strict=False)
                    .captions
                    )

    def test_from_buffer_unsupported_format(self):
        path = PATH_TO_SAMPLES / 'sample.vtt'
        for strict in (False, True):
            with self.subTest(strict=strict), \
                    open(path, encoding='utf-8') as f:
                with self.assertRaises(ValueError) as cm:
                    webvtt.from_buffer(f, format='ass', strict=strict)

                self.assertEqual(str(cm.exception),
                                 'Format ass is not supported.')
                self.assertEqual(f.tell(), 0)

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

    def test_from_string_strict_header_keyword_followed_by_text(self):
        content = 'WEBVTTX\n\n00:00:00.500 --> 00:00:04.300\nCaption text\n'

        self.assertEqual(len(webvtt.from_string(content).captions), 1)
        with self.assertRaises(MalformedFileError):
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

    def test_from_buffer_binary_file(self):
        for format in ('vtt', 'srt', 'sbv'):
            sample = PATH_TO_SAMPLES / ('sample.' + format)
            expected = webvtt.from_buffer(
                io.StringIO(sample.read_text()), format=format
                )
            with self.subTest(format=format), open(sample, 'rb') as f:
                actual = webvtt.from_buffer(f, format=format)

                self.assertEqual(
                    [(c.start, c.end, c.text) for c in actual],
                    [(c.start, c.end, c.text) for c in expected]
                    )
                self.assertEqual(actual.file, str(sample))
                self.assertFalse(f.closed)

    def test_from_buffer_name_that_is_not_a_path(self):
        sample = PATH_TO_SAMPLES / 'sample.vtt'
        stdin = io.BytesIO(sample.read_bytes())
        stdin.name = '<stdin>'

        flags = os.O_RDONLY | getattr(os, 'O_BINARY', 0)
        with open(os.open(sample, flags), 'rb') as from_descriptor:
            for buffer in (stdin, from_descriptor,
                           io.BytesIO(sample.read_bytes()),
                           io.StringIO(sample.read_text())):
                with self.subTest(name=getattr(buffer, 'name', None)):
                    vtt = webvtt.from_buffer(buffer)

                    self.assertIsNone(vtt.file)
                    self.assertTrue(vtt.captions)
                    with self.assertRaises(MissingFilenameError):
                        vtt.save()
                    with tempfile.TemporaryDirectory() as td, \
                            self.assertRaises(MissingFilenameError):
                        vtt.save(td)

    def test_from_buffer_name_as_bytes_or_path(self):
        sample = PATH_TO_SAMPLES / 'sample.vtt'

        with open(os.fsencode(sample), 'rb') as f:
            self.assertEqual(webvtt.from_buffer(f).file, str(sample))

        buffer = io.BytesIO(sample.read_bytes())
        buffer.name = sample
        self.assertEqual(webvtt.from_buffer(buffer).file, str(sample))

    @unittest.skipIf(os.name == 'nt',
                     'Windows file names cannot have angle brackets')
    def test_read_file_named_in_angle_brackets(self):
        cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as td:
            os.chdir(td)
            try:
                shutil.copy(PATH_TO_SAMPLES / 'sample.vtt', '<draft>')

                vtt = webvtt.read('<draft>')
                self.assertEqual(vtt.file, '<draft>')

                vtt.save()
                self.assertEqual(sorted(os.listdir(td)),
                                 ['<draft>', '<draft>.vtt'])
            finally:
                os.chdir(cwd)

    def test_from_buffer_binary_with_bom(self):
        content = 'WEBVTT\n\n00:00:00.500 --> 00:00:07.000\nCaption ñ\n'
        for encoding in CODEC_BOMS:
            with self.subTest(encoding=encoding):
                vtt = webvtt.from_buffer(io.BytesIO(
                    CODEC_BOMS[encoding] + content.encode(encoding)
                    ))

                self.assertEqual(vtt[0].text, 'Caption ñ')
                self.assertEqual(vtt.encoding, encoding)
                self.assertEqual(vtt.content, content)

    def test_from_buffer_binary_with_bom_saves_bom(self):
        content = 'WEBVTT\n\n00:00:00.500 --> 00:00:07.000\nCaption ñ\n'
        vtt = webvtt.from_buffer(io.BytesIO(
            codecs.BOM_UTF16_LE + content.encode('utf-16-le')
            ))
        with tempfile.TemporaryDirectory() as td:
            output = os.path.join(td, 'captions.vtt')
            vtt.save(output)

            self.assertTrue(
                pathlib.Path(output).read_bytes().startswith(
                    codecs.BOM_UTF16_LE
                    )
                )

    def test_from_buffer_binary_encoding(self):
        content = 'WEBVTT\n\n00:00:00.500 --> 00:00:07.000\nCaption ñ\n'
        buffer = io.BytesIO(content.encode('latin-1'))

        vtt = webvtt.from_buffer(buffer, encoding='latin-1')

        self.assertEqual(vtt[0].text, 'Caption ñ')
        self.assertEqual(vtt.encoding, webvtt.webvtt.DEFAULT_ENCODING)

        buffer.seek(0)
        with self.assertRaises(UnicodeDecodeError):
            webvtt.from_buffer(buffer)

    def test_from_buffer_bom_before_encoding(self):
        content = 'WEBVTT\n\n00:00:00.500 --> 00:00:07.000\nCaption ñ\n'
        vtt = webvtt.from_buffer(
            io.BytesIO(codecs.BOM_UTF8 + content.encode('utf-8')),
            encoding='latin-1'
            )

        self.assertEqual(vtt[0].text, 'Caption ñ')
        self.assertEqual(vtt.encoding, 'utf-8')

    def test_read_errors(self):
        vtt = 'WEBVTT\n\n00:00:00.500 --> 00:00:07.000\nCaf\xe9\n'
        srt = '1\n00:00:00,500 --> 00:00:07,000\nCaf\xe9\n'
        sbv = '0:00:00.500,0:00:07.000\nCaf\xe9\n'
        with tempfile.TemporaryDirectory() as td:
            for name, content, read in (
                    ('in.vtt', vtt, webvtt.read),
                    ('in.srt', srt, webvtt.from_srt),
                    ('in.sbv', sbv, webvtt.from_sbv)):
                with self.subTest(name=name):
                    path = pathlib.Path(td, name)
                    path.write_bytes(content.encode('cp1252'))

                    with self.assertRaises(UnicodeDecodeError):
                        read(path)
                    with self.assertRaises(UnicodeDecodeError):
                        read(path, errors='strict')

                    self.assertEqual(
                        read(path, errors='replace')[0].text,
                        'Caf\ufffd'
                        )
                    self.assertEqual(
                        read(path, errors='ignore')[0].text,
                        'Caf'
                        )

    def test_from_buffer_binary_errors(self):
        content = 'WEBVTT\n\n00:00:00.500 --> 00:00:07.000\nCaf\xe9\n'
        buffer = io.BytesIO(content.encode('cp1252'))

        with self.assertRaises(UnicodeDecodeError):
            webvtt.from_buffer(buffer)

        buffer.seek(0)
        vtt = webvtt.from_buffer(buffer, errors='replace')
        self.assertEqual(vtt[0].text, 'Caf\ufffd')

        buffer.seek(0)
        vtt = webvtt.from_buffer(buffer, format='vtt', errors='ignore')
        self.assertEqual(vtt[0].text, 'Caf')

    def test_from_buffer_binary_errors_srt_and_sbv(self):
        srt = b'1\n00:00:00,500 --> 00:00:07,000\nCaf\xe9\n'
        sbv = b'0:00:00.500,0:00:07.000\nCaf\xe9\n'
        for format, content in (('srt', srt), ('sbv', sbv)):
            with self.subTest(format=format):
                vtt = webvtt.from_buffer(
                    io.BytesIO(content), format=format, errors='replace'
                    )
                self.assertEqual(vtt[0].text, 'Caf�')

                vtt = webvtt.from_buffer(
                    io.BytesIO(content), format=format, errors='ignore'
                    )
                self.assertEqual(vtt[0].text, 'Caf')

    def test_read_errors_with_bom(self):
        content = (b'\xef\xbb\xbfWEBVTT\n\n'
                   b'00:00:00.500 --> 00:00:07.000\nCaf\xe9\n')
        with tempfile.TemporaryDirectory() as td:
            path = pathlib.Path(td, 'in.vtt')
            path.write_bytes(content)
            vtt = webvtt.read(path, errors='replace')
        self.assertEqual(vtt[0].text, 'Caf�')
        self.assertEqual(vtt.encoding, 'utf-8')

        vtt = webvtt.from_buffer(io.BytesIO(content), errors='ignore')
        self.assertEqual(vtt[0].text, 'Caf')
        self.assertEqual(vtt.encoding, 'utf-8')

    def test_errors_none_is_strict(self):
        content = b'WEBVTT\n\n00:00:00.500 --> 00:00:07.000\nCaf\xe9\n'
        with tempfile.TemporaryDirectory() as td:
            path = pathlib.Path(td, 'in.vtt')
            path.write_bytes(content)
            with self.assertRaises(UnicodeDecodeError):
                webvtt.read(path, errors=None)
        with self.assertRaises(UnicodeDecodeError):
            webvtt.from_buffer(io.BytesIO(content), errors=None)

        valid = 'WEBVTT\n\n00:00:00.500 --> 00:00:07.000\nCafé\n'
        vtt = webvtt.from_buffer(
            io.BytesIO(valid.encode('utf-8')), errors=None
            )
        self.assertEqual(vtt[0].text, 'Café')

    def test_unknown_errors_handler(self):
        vtt = b'WEBVTT\n\n00:00:00.500 --> 00:00:07.000\nCaption\n'
        srt = b'1\n00:00:00,500 --> 00:00:07,000\nCaption\n'
        sbv = b'0:00:00.500,0:00:07.000\nCaption\n'
        with tempfile.TemporaryDirectory() as td:
            for name, content, read in (
                    ('in.vtt', vtt, webvtt.read),
                    ('in.srt', srt, webvtt.from_srt),
                    ('in.sbv', sbv, webvtt.from_sbv)):
                with self.subTest(name=name):
                    path = pathlib.Path(td, name)
                    path.write_bytes(content)
                    with self.assertRaises(LookupError):
                        read(path, errors='unknown')

        for buffer in (io.BytesIO(vtt), io.StringIO(vtt.decode('utf-8'))):
            with self.subTest(buffer=type(buffer).__name__):
                with self.assertRaises(LookupError):
                    webvtt.from_buffer(buffer, errors='unknown')

    def test_from_buffer_errors_has_no_effect_on_text(self):
        with tempfile.TemporaryDirectory() as td:
            path = pathlib.Path(td, 'in.vtt')
            path.write_bytes(
                b'WEBVTT\n\n00:00:00.500 --> 00:00:07.000\nCaf\xe9\n'
                )
            with open(path, encoding='utf-8') as f:
                with self.assertRaises(UnicodeDecodeError):
                    webvtt.from_buffer(f, errors='replace')

    def test_save_as_srt_replaced_bytes_in_encoding_of_file(self):
        content = b'1\n00:00:00,500 --> 00:00:07,000\nCaf\x81\n'
        with tempfile.TemporaryDirectory() as td:
            path = pathlib.Path(td, 'in.srt')
            path.write_bytes(content)
            vtt = webvtt.from_srt(path, encoding='cp1252', errors='replace')
            self.assertEqual(vtt[0].text, 'Caf�')

            with self.assertRaises(UnicodeEncodeError):
                vtt.save_as_srt()
            self.assertEqual(path.read_bytes(), content)

            output = pathlib.Path(td, 'out.srt')
            vtt.save_as_srt(output, encoding='utf-8')
            self.assertIn('Caf�', output.read_text(encoding='utf-8'))

    def test_errors_in_timing_line(self):
        content = (b'WEBVTT\n\n00:00:0\xe91.000 --> 00:00:07.000\nOne\n\n'
                   b'00:00:08.000 --> 00:00:09.000\nTwo\n')

        vtt = webvtt.from_buffer(io.BytesIO(content), errors='replace')
        self.assertEqual([c.text for c in vtt], ['Two'])

        with self.assertRaises(MalformedCaptionError):
            webvtt.from_buffer(
                io.BytesIO(content), strict=True, errors='replace'
                )

        vtt = webvtt.from_buffer(io.BytesIO(content), errors='ignore')
        self.assertEqual(vtt[0].start, '00:00:01.000')

    def test_from_buffer_string(self):
        content = 'WEBVTT\n\n00:00:00.500 --> 00:00:07.000\nCaption\n'
        for buffer, hint in (
                (content, 'use from_string'),
                (content.encode('utf-8'), 'use io.BytesIO'),
                (bytearray(content.encode('utf-8')), 'use io.BytesIO')
                ):
            with self.subTest(buffer=type(buffer)):
                with self.assertRaises(TypeError) as cm:
                    webvtt.from_buffer(buffer)

                self.assertIn(hint, str(cm.exception))

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
            'line 1\u2028still line 1\nline 2\n'
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

    def test_list_arguments_are_kept(self):
        for name, item in (('captions', Caption()),
                           ('styles', Style('::cue {}')),
                           ('header_comments', 'comment'),
                           ('footer_comments', 'comment'),
                           ('metadata', 'Kind: captions'),
                           ('regions', Region(id='fred'))):
            for items in ([], [item]):
                with self.subTest(name=name, items=items):
                    vtt = webvtt.WebVTT(**{name: items})
                    items.append(item)

                    self.assertIs(getattr(vtt, name), items)

    def test_list_arguments_default_to_new_lists(self):
        first, second = webvtt.WebVTT(), webvtt.WebVTT()
        for name in ('captions', 'styles', 'header_comments',
                     'footer_comments', 'metadata', 'regions'):
            with self.subTest(name=name):
                self.assertListEqual(getattr(first, name), [])
                self.assertIsNot(getattr(first, name), getattr(second, name))

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
            '1\n00:00:01,000 --> 00:00:03,000\nTop left\n'
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
            '<font color="yellow">Hello <b>world</b></font>\n'
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
            63.8
            )

    def test_total_length_no_captions(self):
        self.assertEqual(
            webvtt.WebVTT().total_length,
            0.0
            )

    def test_total_length_keeps_milliseconds(self):
        vtt = webvtt.WebVTT(captions=[
            webvtt.Caption('00:00:00.900', '00:00:01.100', 'Hello')
            ])
        self.assertEqual(vtt.total_length, 0.2)

    def test_total_length_captions_out_of_order(self):
        vtt = webvtt.WebVTT(captions=[
            webvtt.Caption('00:00:10.000', '00:00:12.000', 'Second'),
            webvtt.Caption('00:00:01.000', '00:00:02.000', 'First')
            ])
        self.assertEqual(vtt.total_length, 11.0)

    def test_total_length_longest_caption_not_last(self):
        vtt = webvtt.WebVTT(captions=[
            webvtt.Caption('00:00:01.000', '00:00:20.000', 'Long'),
            webvtt.Caption('00:00:05.000', '00:00:06.000', 'Short')
            ])
        self.assertEqual(vtt.total_length, 19.0)

    def test_total_length_caption_ends_before_start(self):
        vtt = webvtt.WebVTT(captions=[
            webvtt.Caption('00:00:05.000', '00:00:01.000', 'x')
            ])
        self.assertEqual(vtt.total_length, 0.0)

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

    def test_shift_from_start_of_other_types(self):
        for start in (47, 47.0, Timestamp(0, 0, 47, 0),
                      datetime.timedelta(seconds=47)):
            with self.subTest(start=start):
                vtt = webvtt.read(PATH_TO_SAMPLES / 'sample.vtt')
                before = [(c.start, c.end) for c in vtt]

                vtt.shift(3, start=start)

                after = [(c.start, c.end) for c in vtt]
                self.assertEqual(after[:11], before[:11])
                self.assertEqual(after[11], ('00:00:50.000', '00:00:53.970'))

    def test_shift_from_start_invalid(self):
        for start in ('47 seconds', -1, float('nan'), True):
            with self.subTest(start=start):
                vtt = webvtt.read(PATH_TO_SAMPLES / 'sample.vtt')
                before = [(c.start, c.end) for c in vtt]

                with self.assertRaises(MalformedCaptionError):
                    vtt.shift(3, start=start)

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
                (((1, 2), (3, Timestamp(0, 0, -4, 0))), ValueError),
                (((1, 2), (3, Timestamp(0, 0, 4.5, 0))), TypeError),
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

    def test_caption_without_timeframe_strict(self):
        with self.assertRaises(MalformedCaptionError) as cm:
            webvtt.read(PATH_TO_SAMPLES / 'missing_timeframe.vtt',
                        strict=True)
        self.assertIn('Caption text #2', str(cm.exception))

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
            '1\n00:00:00,500 --> 00:00:07,000\nCaption #1\n'
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
            23.38
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
            16.165
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

    def test_save_encoding_names(self):
        with_bom = webvtt.read(PATH_TO_SAMPLES / 'captions_with_bom.vtt')
        without_bom = webvtt.read(PATH_TO_SAMPLES / 'one_caption.vtt')
        for vtt, encoding, add_bom, expected in (
                (with_bom, 'UTF-8', None, 'utf-8'),
                (with_bom, 'utf8', None, 'utf-8'),
                (without_bom, 'UTF-16LE', True, 'utf-16-le'),
                (without_bom, 'utf_32_be', True, 'utf-32-be')):
            with self.subTest(encoding=encoding), \
                    tempfile.TemporaryDirectory() as td:
                path = os.path.join(td, 'captions.vtt')
                vtt.save(path, encoding=encoding, add_bom=add_bom)

                data = pathlib.Path(path).read_bytes()
                self.assertTrue(data.startswith(CODEC_BOMS[expected]))
                self.assertTrue(
                    data[len(CODEC_BOMS[expected]):].decode(expected)
                    .startswith('WEBVTT')
                    )

    def test_save_codecs_writing_bom(self):
        with_bom = webvtt.read(PATH_TO_SAMPLES / 'captions_with_bom.vtt')
        without_bom = webvtt.read(PATH_TO_SAMPLES / 'one_caption.vtt')
        for encoding in ('utf-8-sig', 'UTF-16', 'utf_32'):
            for vtt, add_bom in ((without_bom, None),
                                 (without_bom, True),
                                 (with_bom, None)):
                with self.subTest(encoding=encoding, add_bom=add_bom,
                                  file=vtt.file), \
                        tempfile.TemporaryDirectory() as td:
                    path = os.path.join(td, 'captions.vtt')
                    vtt.save(path, encoding=encoding, add_bom=add_bom)

                    # a single Byte Order Mark, written by the codec
                    self.assertTrue(
                        pathlib.Path(path).read_bytes()
                        .decode(encoding).startswith('WEBVTT')
                        )

    def test_save_codecs_writing_bom_without_bom(self):
        vtt = webvtt.read(PATH_TO_SAMPLES / 'one_caption.vtt')
        for encoding in ('utf-8-sig', 'utf-16', 'utf-32'):
            with self.subTest(encoding=encoding), \
                    tempfile.TemporaryDirectory() as td:
                path = pathlib.Path(td, 'captions.vtt')
                path.write_text('original')

                with self.assertRaises(ValueError) as cm:
                    vtt.save(path, encoding=encoding, add_bom=False)

                self.assertIn('always writes a Byte Order Mark',
                              str(cm.exception))
                self.assertEqual(path.read_text(), 'original')

    def test_save_encoding_without_bom(self):
        with tempfile.TemporaryDirectory() as td:
            path = pathlib.Path(td, 'captions.vtt')
            path.write_text('original')
            vtt = webvtt.read(PATH_TO_SAMPLES / 'captions_with_bom.vtt')

            with self.assertRaises(ValueError) as cm:
                vtt.save(path, encoding='latin-1', add_bom=True)

            self.assertIn('The latin-1 encoding has no Byte Order Mark',
                          str(cm.exception))
            self.assertEqual(path.read_text(), 'original')

            # the Byte Order Mark of the file that was read is left out
            vtt.save(path, encoding='latin-1')
            self.assertTrue(path.read_bytes().startswith(b'WEBVTT'))

    def test_save_unknown_encoding(self):
        with tempfile.TemporaryDirectory() as td:
            path = pathlib.Path(td, 'captions.vtt')
            path.write_text('original')

            with self.assertRaises(LookupError):
                webvtt.read(PATH_TO_SAMPLES / 'one_caption.vtt').save(
                    path, encoding='unknown'
                    )

            self.assertEqual(path.read_text(), 'original')

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

    def _iter_slice_captions(self):
        return webvtt.WebVTT(captions=[
            Caption('00:00:01.000', '00:00:05.000', 'a'),
            Caption('00:00:03.000', '00:00:04.000', 'b'),
            Caption('00:00:05.000', '00:00:09.000', 'c'),
            Caption('00:00:09.000', '00:00:10.000', 'd')
            ])

    def test_iter_slice_default_leaves_out_overlapping_captions(self):
        vtt = self._iter_slice_captions()
        self.assertEqual(
            [c.text for c in vtt.iter_slice('00:00:02.000', '00:00:06.000')],
            ['b']
            )

    def test_iter_slice_overlapping(self):
        vtt = self._iter_slice_captions()
        for start, end, expected in (
                ('00:00:02.000', '00:00:06.000', ['a', 'b', 'c']),
                ('00:00:03.500', '00:00:03.600', ['a', 'b']),
                (None, '00:00:02.000', ['a']),
                ('00:00:08.000', None, ['c', 'd']),
                (None, None, ['a', 'b', 'c', 'd']),
                ('00:00:20.000', None, [])):
            with self.subTest(start=start, end=end):
                self.assertEqual(
                    [c.text for c in
                     vtt.iter_slice(start, end, overlapping=True)],
                    expected
                    )

    def test_iter_slice_overlapping_returns_the_captions(self):
        vtt = self._iter_slice_captions()
        captions = list(vtt.iter_slice('00:00:02.000', '00:00:06.000',
                                       overlapping=True
                                       ))
        self.assertEqual(len(captions), 3)
        for caption, expected in zip(captions, vtt.captions):
            self.assertIs(caption, expected)

    def test_iter_slice_overlapping_caption_only_touching_the_range(self):
        vtt = self._iter_slice_captions()
        for start, end, expected in (
                ('00:00:05.000', '00:00:09.000', ['c']),
                ('00:00:04.000', '00:00:05.000', ['a']),
                ('00:00:10.000', None, []),
                (None, '00:00:01.000', [])):
            with self.subTest(start=start, end=end):
                self.assertEqual(
                    [c.text for c in
                     vtt.iter_slice(start, end, overlapping=True)],
                    expected
                    )

    def test_iter_slice_overlapping_includes_what_the_default_returns(self):
        vtt = webvtt.WebVTT(captions=[
            Caption('00:00:02.000', '00:00:02.000', 'at start'),
            Caption('00:00:04.000', '00:00:04.000', 'inside'),
            Caption('00:00:06.000', '00:00:06.000', 'at end'),
            Caption('00:00:07.000', '00:00:07.000', 'after')
            ])
        range_ = ('00:00:02.000', '00:00:06.000')
        self.assertEqual(
            list(vtt.iter_slice(*range_, overlapping=True)),
            list(vtt.iter_slice(*range_))
            )
        self.assertEqual(
            [c.text for c in vtt.iter_slice(*range_, overlapping=True)],
            ['at start', 'inside', 'at end']
            )

    def test_iter_slice_overlapping_range_without_duration(self):
        vtt = self._iter_slice_captions()
        for start, end in (('00:00:03.500', '00:00:03.500'),
                           ('00:00:06.000', '00:00:02.000')):
            with self.subTest(start=start, end=end):
                self.assertEqual(
                    list(vtt.iter_slice(start, end, overlapping=True)),
                    []
                    )

    def test_iter_slice_clip(self):
        vtt = self._iter_slice_captions()
        self.assertEqual(
            [(c.start, c.end, c.text) for c in vtt.iter_slice(
                '00:00:02.000', '00:00:06.000', overlapping=True, clip=True
                )],
            [('00:00:02.000', '00:00:05.000', 'a'),
             ('00:00:03.000', '00:00:04.000', 'b'),
             ('00:00:05.000', '00:00:06.000', 'c')]
            )

    def test_iter_slice_clip_open_range(self):
        vtt = self._iter_slice_captions()
        for start, end, expected in (
                (None, '00:00:02.000', [('00:00:01.000', '00:00:02.000')]),
                ('00:00:09.500', None, [('00:00:09.500', '00:00:10.000')])):
            with self.subTest(start=start, end=end):
                self.assertEqual(
                    [(c.start, c.end) for c in vtt.iter_slice(
                        start, end, overlapping=True, clip=True
                        )],
                    expected
                    )

    def test_iter_slice_clip_inside_a_caption(self):
        vtt = self._iter_slice_captions()
        caption = next(vtt.iter_slice('00:00:01.500', '00:00:02.500',
                                      overlapping=True, clip=True
                                      ))
        self.assertEqual(
            (caption.start, caption.end),
            ('00:00:01.500', '00:00:02.500')
            )

    def test_iter_slice_clip_keeps_the_rest_of_the_caption(self):
        original = Caption('00:00:01.000', '00:00:05.000',
                           ['<v Bob>one', 'two'], 'cue-1', 'line:0'
                           )
        original.comments = ['comment']
        vtt = webvtt.WebVTT(captions=[original])
        caption = next(vtt.iter_slice('00:00:02.000', overlapping=True,
                                      clip=True
                                      ))
        self.assertEqual(caption.raw_text, original.raw_text)
        self.assertEqual(caption.identifier, 'cue-1')
        self.assertEqual(str(caption.settings), 'line:0')
        self.assertEqual(caption.comments, ['comment'])

    def test_iter_slice_clip_leaves_the_captions_unchanged(self):
        vtt = self._iter_slice_captions()
        expected = [(c.start, c.end) for c in vtt.captions]
        copies = list(vtt.iter_slice('00:00:02.000', '00:00:06.000',
                                     overlapping=True, clip=True
                                     ))
        self.assertEqual([(c.start, c.end) for c in vtt.captions], expected)

        self.assertEqual(len(copies), 3)
        for caption, source in zip(copies, vtt.captions):
            self.assertIsNot(caption, source)

        # also a copy with nothing to trim
        copies[1].lines.append('changed')
        copies[1].comments.append('changed')
        copies[1].settings.line = '0'
        copies[1].start_time.seconds = 1
        self.assertEqual(vtt.captions[1].text, 'b')
        self.assertEqual(vtt.captions[1].comments, [])
        self.assertFalse(vtt.captions[1].settings)
        self.assertEqual(vtt.captions[1].start, '00:00:03.000')

    def test_iter_slice_clip_copies_do_not_share_their_times(self):
        vtt = webvtt.WebVTT(captions=[
            Caption('00:00:01.000', '00:00:03.000', 'x'),
            Caption('00:00:01.000', '00:00:03.000', 'y')
            ])
        x, y = vtt.iter_slice('00:00:02.000', '00:00:02.500',
                              overlapping=True, clip=True
                              )
        x.start_time.seconds = 0
        x.end_time.seconds = 0
        self.assertEqual((y.start, y.end), ('00:00:02.000', '00:00:02.500'))

    def test_iter_slice_clip_needs_overlapping(self):
        vtt = self._iter_slice_captions()
        with self.assertRaises(ValueError):
            list(vtt.iter_slice('00:00:02.000', clip=True))

    def test_iter_slice_new_arguments_are_keyword_only(self):
        vtt = self._iter_slice_captions()
        with self.assertRaises(TypeError):
            vtt.iter_slice('00:00:02.000', '00:00:06.000', True)

    def test_iter_slice_times_of_other_types(self):
        vtt = self._iter_slice_captions()
        for start, end in (
                (2, 6),
                (2.0, 6.0),
                (Timestamp(0, 0, 2, 0), Timestamp(0, 0, 6, 0)),
                (datetime.timedelta(seconds=2),
                 datetime.timedelta(seconds=6)),
                ('00:00:02.000', 6)):
            with self.subTest(start=start, end=end):
                self.assertEqual(
                    [c.text for c in vtt.iter_slice(start, end)],
                    ['b']
                    )
                self.assertEqual(
                    [(c.start, c.end) for c in vtt.iter_slice(
                        start, end, overlapping=True, clip=True)],
                    [('00:00:02.000', '00:00:05.000'),
                     ('00:00:03.000', '00:00:04.000'),
                     ('00:00:05.000', '00:00:06.000')]
                    )

    def test_iter_slice_zero(self):
        vtt = webvtt.WebVTT(captions=[
            Caption('00:00:00.000', '00:00:00.000', 'a'),
            Caption('00:00:00.000', '00:00:01.000', 'b')
            ])
        for value in (0, 0.0, datetime.timedelta(0), Timestamp(),
                      '00:00:00.000'):
            with self.subTest(value=value):
                self.assertEqual(
                    [c.text for c in vtt.iter_slice(end=value)],
                    ['a']
                    )
                self.assertEqual(
                    [c.text for c in vtt.iter_slice(start=value)],
                    ['a', 'b']
                    )

    def test_iter_slice_no_limits(self):
        vtt = self._iter_slice_captions()
        for value in (None, ''):
            with self.subTest(value=value):
                self.assertEqual(
                    [c.text for c in vtt.iter_slice(value, value)],
                    ['a', 'b', 'c', 'd']
                    )

    def test_iter_slice_invalid_times_of_other_types(self):
        vtt = self._iter_slice_captions()
        for value in (-1, float('nan'), True, datetime.timedelta(seconds=-1),
                      Timestamp(0, 0, -1, 0), b'00:00:02.000'):
            for kwargs in ({'start': value}, {'end': value}):
                with self.subTest(kwargs=kwargs):
                    with self.assertRaises(MalformedCaptionError):
                        list(vtt.iter_slice(**kwargs))

    def test_iter_slice_invalid_timestamp(self):
        vtt = self._iter_slice_captions()
        for kwargs in ({'overlapping': True},
                       {'overlapping': True, 'clip': True}):
            with self.subTest(kwargs=kwargs):
                with self.assertRaises(MalformedCaptionError):
                    list(vtt.iter_slice('invalid', **kwargs))

    def test_iter_slice_clip_can_be_saved(self):
        vtt = webvtt.from_string(
            'WEBVTT\n\nREGION\nid:r\n\nSTYLE\n::cue(.a) {color:red}\n\n'
            '00:00:01.000 --> 00:00:05.000 region:r\n<c.a>one</c>\n\n'
            '00:00:05.000 --> 00:00:09.000\ntwo\n'
            )
        clip = webvtt.WebVTT(
            captions=list(vtt.iter_slice('00:00:02.000', '00:00:06.000',
                                         overlapping=True, clip=True
                                         )),
            styles=vtt.styles,
            regions=vtt.regions
            )
        clip.shift(-2)

        self.assertEqual(
            [(c.start, c.end) for c in clip],
            [('00:00:00.000', '00:00:03.000'),
             ('00:00:03.000', '00:00:04.000')]
            )
        self.assertEqual(
            [(c.start, c.end) for c in vtt],
            [('00:00:01.000', '00:00:05.000'),
             ('00:00:05.000', '00:00:09.000')]
            )

        saved = webvtt.from_string(clip.content, strict=True)
        self.assertEqual(saved.captions, clip.captions)
        self.assertEqual(len(saved.regions), 1)
        self.assertEqual(len(saved.styles), 1)
