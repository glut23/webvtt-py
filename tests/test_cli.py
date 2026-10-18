import unittest
import errno
import contextlib
import io
import tempfile
import os
import pathlib
import textwrap

from webvtt.cli import main


class CLITestCase(unittest.TestCase):

    def test_cli(self):
        vtt_file = (
            pathlib.Path(__file__).resolve().parent
            / 'samples' / 'sample.vtt'
            )

        with tempfile.TemporaryDirectory() as temp_dir:

            main(['segment', str(vtt_file.resolve()), '-o', temp_dir])
            _, dirs, files = next(os.walk(temp_dir))

            self.assertEqual(len(dirs), 0)
            self.assertEqual(len(files), 8)
            for expected_file in ('prog_index.m3u8',
                                  'fileSequence0.webvtt',
                                  'fileSequence1.webvtt',
                                  'fileSequence2.webvtt',
                                  'fileSequence3.webvtt',
                                  'fileSequence4.webvtt',
                                  'fileSequence5.webvtt',
                                  'fileSequence6.webvtt',
                                  ):
                self.assertIn(expected_file, files)

            self.assertEqual(
                (pathlib.Path(temp_dir) / 'prog_index.m3u8').read_text(),
                textwrap.dedent(
                '''
                #EXTM3U
                #EXT-X-TARGETDURATION:10
                #EXT-X-VERSION:3
                #EXT-X-PLAYLIST-TYPE:VOD
                #EXTINF:10.00000,
                fileSequence0.webvtt
                #EXTINF:10.00000,
                fileSequence1.webvtt
                #EXTINF:10.00000,
                fileSequence2.webvtt
                #EXTINF:10.00000,
                fileSequence3.webvtt
                #EXTINF:10.00000,
                fileSequence4.webvtt
                #EXTINF:10.00000,
                fileSequence5.webvtt
                #EXTINF:10.00000,
                fileSequence6.webvtt
                #EXT-X-ENDLIST
                '''
                ).lstrip())
            self.assertEqual(
                (pathlib.Path(temp_dir) / 'fileSequence0.webvtt').read_text(),
                textwrap.dedent(
                '''
                WEBVTT
                X-TIMESTAMP-MAP=MPEGTS:900000,LOCAL:00:00:00.000

                00:00:00.500 --> 00:00:07.000
                Caption text #1

                00:00:07.000 --> 00:00:11.890
                Caption text #2
                '''
                ).lstrip())
            self.assertEqual(
                (pathlib.Path(temp_dir) / 'fileSequence1.webvtt').read_text(),
                textwrap.dedent(
                    '''
                    WEBVTT
                    X-TIMESTAMP-MAP=MPEGTS:900000,LOCAL:00:00:00.000

                    00:00:07.000 --> 00:00:11.890
                    Caption text #2

                    00:00:11.890 --> 00:00:16.320
                    Caption text #3

                    00:00:16.320 --> 00:00:21.580
                    Caption text #4
                    '''
                ).lstrip())
            self.assertEqual(
                (pathlib.Path(temp_dir) / 'fileSequence2.webvtt').read_text(),
                textwrap.dedent(
                    '''
                    WEBVTT
                    X-TIMESTAMP-MAP=MPEGTS:900000,LOCAL:00:00:00.000

                    00:00:16.320 --> 00:00:21.580
                    Caption text #4

                    00:00:21.580 --> 00:00:23.880
                    Caption text #5

                    00:00:23.880 --> 00:00:27.280
                    Caption text #6

                    00:00:27.280 --> 00:00:30.280
                    Caption text #7
                    '''
                ).lstrip())
            self.assertEqual(
                (pathlib.Path(temp_dir) / 'fileSequence3.webvtt').read_text(),
                textwrap.dedent(
                    '''
                    WEBVTT
                    X-TIMESTAMP-MAP=MPEGTS:900000,LOCAL:00:00:00.000

                    00:00:27.280 --> 00:00:30.280
                    Caption text #7

                    00:00:30.280 --> 00:00:36.510
                    Caption text #8

                    00:00:36.510 --> 00:00:38.870
                    Caption text #9

                    00:00:38.870 --> 00:00:45.000
                    Caption text #10
                    '''
                ).lstrip())
            self.assertEqual(
                (pathlib.Path(temp_dir) / 'fileSequence4.webvtt').read_text(),
                textwrap.dedent(
                    '''
                    WEBVTT
                    X-TIMESTAMP-MAP=MPEGTS:900000,LOCAL:00:00:00.000

                    00:00:38.870 --> 00:00:45.000
                    Caption text #10

                    00:00:45.000 --> 00:00:47.000
                    Caption text #11

                    00:00:47.000 --> 00:00:50.970
                    Caption text #12
                    '''
                ).lstrip())
            self.assertEqual(
                (pathlib.Path(temp_dir) / 'fileSequence5.webvtt').read_text(),
                textwrap.dedent(
                    '''
                    WEBVTT
                    X-TIMESTAMP-MAP=MPEGTS:900000,LOCAL:00:00:00.000

                    00:00:47.000 --> 00:00:50.970
                    Caption text #12

                    00:00:50.970 --> 00:00:54.440
                    Caption text #13

                    00:00:54.440 --> 00:00:58.600
                    Caption text #14

                    00:00:58.600 --> 00:01:01.350
                    Caption text #15
                    '''
                ).lstrip())
            self.assertEqual(
                (pathlib.Path(temp_dir) / 'fileSequence6.webvtt').read_text(),
                textwrap.dedent(
                    '''
                    WEBVTT
                    X-TIMESTAMP-MAP=MPEGTS:900000,LOCAL:00:00:00.000

                    00:00:58.600 --> 00:01:01.350
                    Caption text #15

                    00:01:01.350 --> 00:01:04.300
                    Caption text #16
                    '''
                ).lstrip())

    def test_cli_requires_output(self):
        vtt_file = (
            pathlib.Path(__file__).resolve().parent
            / 'samples' / 'sample.vtt'
            )

        with contextlib.redirect_stderr(io.StringIO()) as stderr:
            with self.assertRaises(SystemExit) as cm:
                main(['segment', str(vtt_file)])

        self.assertEqual(cm.exception.code, 2)
        self.assertIn(
            'the following arguments are required: -o/--output',
            stderr.getvalue()
            )

    def assert_cli_error(self, argv, expected_message):
        with contextlib.redirect_stderr(io.StringIO()) as stderr:
            with self.assertRaises(SystemExit) as cm:
                main(argv)

        self.assertEqual(cm.exception.code, 1)
        self.assertEqual(
            stderr.getvalue(),
            f'webvtt: error: {expected_message}\n'
            )

    def test_cli_missing_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            vtt_file = os.path.join(temp_dir, 'missing.vtt')

            self.assert_cli_error(
                ['segment', vtt_file, '-o', temp_dir],
                f'{vtt_file}: {os.strerror(errno.ENOENT)}'
                )

    def test_cli_invalid_file(self):
        vtt_file = str(
            pathlib.Path(__file__).resolve().parent
            / 'samples' / 'invalid.vtt'
            )

        with tempfile.TemporaryDirectory() as temp_dir:
            self.assert_cli_error(
                ['segment', vtt_file, '-o', temp_dir],
                f'{vtt_file}: not a valid WebVTT file'
                )

    def test_cli_file_not_utf8(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            vtt_file = os.path.join(temp_dir, 'captions.vtt')
            pathlib.Path(vtt_file).write_bytes(b'WEBVTT\n\n\xff\xfe\xfd')

            self.assert_cli_error(
                ['segment', vtt_file, '-o', temp_dir],
                f'{vtt_file}: cannot be decoded as utf-8'
                )

    def test_cli_output_is_a_file(self):
        vtt_file = str(
            pathlib.Path(__file__).resolve().parent
            / 'samples' / 'sample.vtt'
            )

        with tempfile.TemporaryDirectory() as temp_dir:
            output = os.path.join(temp_dir, 'output')
            pathlib.Path(output).touch()

            self.assert_cli_error(
                ['segment', vtt_file, '-o', output],
                f'{output}: {os.strerror(errno.EEXIST)}'
                )

    def test_cli_requires_command(self):
        with contextlib.redirect_stderr(io.StringIO()) as stderr:
            with self.assertRaises(SystemExit) as cm:
                main([])

        self.assertEqual(cm.exception.code, 2)
        self.assertIn(
            'the following arguments are required: command',
            stderr.getvalue()
            )


class CLIShiftTestCase(unittest.TestCase):

    CAPTIONS = textwrap.dedent(
        '''
        WEBVTT

        00:00:00.500 --> 00:00:01.000
        Credits

        00:00:01.500 --> 00:00:04.000
        Caption #1

        00:00:04.000 --> 00:00:07.000
        Caption #2
        '''
        ).lstrip()

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.vtt_file = os.path.join(self.temp_dir.name, 'captions.vtt')
        pathlib.Path(self.vtt_file).write_text(self.CAPTIONS)

    def run_cli(self, argv):
        with contextlib.redirect_stdout(io.StringIO()) as stdout:
            main(argv)
        return stdout.getvalue()

    def assert_usage_error(self, argv, expected_message):
        with contextlib.redirect_stderr(io.StringIO()) as stderr:
            with self.assertRaises(SystemExit) as cm:
                main(argv)

        self.assertEqual(cm.exception.code, 2)
        self.assertIn(expected_message, stderr.getvalue())

    def test_shift_to_stdout(self):
        self.assertEqual(
            self.run_cli(['shift', self.vtt_file, '1.25']),
            textwrap.dedent(
                '''
                WEBVTT

                00:00:01.750 --> 00:00:02.250
                Credits

                00:00:02.750 --> 00:00:05.250
                Caption #1

                00:00:05.250 --> 00:00:08.250
                Caption #2
                '''
                ).lstrip()
            )
        self.assertEqual(
            pathlib.Path(self.vtt_file).read_text(),
            self.CAPTIONS
            )

    def test_shift_negative_clamps_to_zero(self):
        self.assertEqual(
            self.run_cli(['shift', self.vtt_file, '-2']),
            textwrap.dedent(
                '''
                WEBVTT

                00:00:00.000 --> 00:00:00.000
                Credits

                00:00:00.000 --> 00:00:02.000
                Caption #1

                00:00:02.000 --> 00:00:05.000
                Caption #2
                '''
                ).lstrip()
            )

    def test_shift_from_start(self):
        self.assertEqual(
            self.run_cli(
                ['shift', self.vtt_file, '-0.5', '--start', '00:00:01.500']
                ),
            textwrap.dedent(
                '''
                WEBVTT

                00:00:00.500 --> 00:00:01.000
                Credits

                00:00:01.000 --> 00:00:03.500
                Caption #1

                00:00:03.500 --> 00:00:06.500
                Caption #2
                '''
                ).lstrip()
            )

    def test_shift_to_output_file(self):
        output = os.path.join(self.temp_dir.name, 'shifted.vtt')

        self.assertEqual(
            self.run_cli(['shift', self.vtt_file, '3', '-o', output]),
            ''
            )
        self.assertEqual(
            pathlib.Path(output).read_text(),
            textwrap.dedent(
                '''
                WEBVTT

                00:00:03.500 --> 00:00:04.000
                Credits

                00:00:04.500 --> 00:00:07.000
                Caption #1

                00:00:07.000 --> 00:00:10.000
                Caption #2
                '''
                ).lstrip()
            )
        self.assertEqual(
            pathlib.Path(self.vtt_file).read_text(),
            self.CAPTIONS
            )

    def test_shift_in_place(self):
        self.run_cli(['shift', self.vtt_file, '-s', '00:00:04.000', '1',
                      '-o', self.vtt_file])

        self.assertEqual(
            pathlib.Path(self.vtt_file).read_text(),
            self.CAPTIONS.replace(
                '00:00:04.000 --> 00:00:07.000',
                '00:00:05.000 --> 00:00:08.000'
                )
            )

    def test_shift_keeps_bom(self):
        pathlib.Path(self.vtt_file).write_bytes(
            b'\xef\xbb\xbf' + self.CAPTIONS.encode('utf-8')
            )

        self.run_cli(['shift', self.vtt_file, '1', '-o', self.vtt_file])

        self.assertTrue(
            pathlib.Path(self.vtt_file).read_bytes().startswith(
                b'\xef\xbb\xbfWEBVTT\n\n00:00:01.500 --> 00:00:02.000'
                )
            )

    def test_shift_invalid_offset(self):
        for value in ('abc', 'nan', 'inf', '1e400', ''):
            with self.subTest(value=value):
                self.assert_usage_error(
                    ['shift', self.vtt_file, value],
                    f'argument OFFSET: invalid offset: {value!r}'
                    )

    def test_shift_invalid_start(self):
        self.assert_usage_error(
            ['shift', self.vtt_file, '1', '--start', '1:2'],
            "argument -s/--start: invalid timestamp: '1:2'"
            )

    def test_shift_requires_offset(self):
        self.assert_usage_error(
            ['shift', self.vtt_file],
            'the following arguments are required: OFFSET'
            )

    def test_shift_missing_file(self):
        vtt_file = os.path.join(self.temp_dir.name, 'missing.vtt')

        with contextlib.redirect_stderr(io.StringIO()) as stderr:
            with self.assertRaises(SystemExit) as cm:
                main(['shift', vtt_file, '1'])

        self.assertEqual(cm.exception.code, 1)
        self.assertEqual(
            stderr.getvalue(),
            f'webvtt: error: {vtt_file}: {os.strerror(errno.ENOENT)}\n'
            )

    def test_shift_invalid_file(self):
        vtt_file = str(
            pathlib.Path(__file__).resolve().parent
            / 'samples' / 'invalid.vtt'
            )

        with contextlib.redirect_stderr(io.StringIO()) as stderr:
            with self.assertRaises(SystemExit) as cm:
                main(['shift', vtt_file, '1'])

        self.assertEqual(cm.exception.code, 1)
        self.assertEqual(
            stderr.getvalue(),
            f'webvtt: error: {vtt_file}: not a valid WebVTT file\n'
            )
