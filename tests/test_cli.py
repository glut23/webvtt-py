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
