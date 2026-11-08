import unittest
import errno
import contextlib
import importlib
import io
import tempfile
import os
import pathlib
import runpy
import sys
import textwrap
from unittest import mock

import webvtt
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

    def test_cli_segment_duration_and_mpegts(self):
        vtt_file = str(
            pathlib.Path(__file__).resolve().parent
            / 'samples' / 'one_caption.vtt'
            )

        for mpegts in ('0', '8589934591'):
            with self.subTest(mpegts=mpegts):
                with tempfile.TemporaryDirectory() as temp_dir:
                    main(['segment', vtt_file, '-o', temp_dir,
                          '-d', '5', '-m', mpegts])

                    output = pathlib.Path(temp_dir)
                    self.assertIn(
                        '#EXT-X-TARGETDURATION:5',
                        (output / 'prog_index.m3u8').read_text()
                        )
                    self.assertIn(
                        f'X-TIMESTAMP-MAP=MPEGTS:{mpegts},',
                        (output / 'fileSequence0.webvtt').read_text()
                        )

    def test_cli_segment_with_duration(self):
        vtt_file = str(
            pathlib.Path(__file__).resolve().parent
            / 'samples' / 'sample.vtt'
            )

        for duration in ('00:01:25.500', '01:25.500', '85.5'):
            with self.subTest(duration=duration):
                with tempfile.TemporaryDirectory() as temp_dir:
                    main(['segment', vtt_file, '-o', temp_dir,
                          '--duration', duration])

                    manifest = (
                        pathlib.Path(temp_dir) / 'prog_index.m3u8'
                        ).read_text()
                    self.assertEqual(
                        [line for line in manifest.splitlines()
                         if line.startswith('#EXTINF:')],
                        ['#EXTINF:10.00000,'] * 8 + ['#EXTINF:5.50000,']
                        )
                    self.assertEqual(len(os.listdir(temp_dir)), 10)

    def test_cli_segment_caption_after_duration(self):
        vtt_file = str(
            pathlib.Path(__file__).resolve().parent
            / 'samples' / 'sample.vtt'
            )

        with tempfile.TemporaryDirectory() as temp_dir:
            output = os.path.join(temp_dir, 'output')

            self.assert_cli_error(
                ['segment', vtt_file, '-o', output, '--duration', '30'],
                f'{vtt_file}: Caption at 00:00:30.280 does not start before '
                'the end of the media at 00:00:30.000'
                )
            self.assertFalse(os.path.exists(output))

    def test_cli_segment_invalid_arguments(self):
        vtt_file = str(
            pathlib.Path(__file__).resolve().parent
            / 'samples' / 'sample.vtt'
            )

        for argv, expected_message in (
                (['-d', '0'], "argument -d/--target-duration: invalid "
                              "duration: '0'"),
                (['-d', '-5'], "argument -d/--target-duration: invalid "
                               "duration: '-5'"),
                (['-d', '2.5'], "argument -d/--target-duration: invalid "
                                "duration: '2.5'"),
                (['-m', '-1'], "argument -m/--mpegts: invalid MPEG-TS "
                               "value: '-1'"),
                (['-m', '8589934592'], "argument -m/--mpegts: invalid "
                                       "MPEG-TS value: '8589934592'"),
                (['-m', 'x'], "argument -m/--mpegts: invalid MPEG-TS "
                              "value: 'x'"),
                (['--duration', '0'], "argument --duration: invalid "
                                      "duration: '0'"),
                (['--duration', '-5'], "argument --duration: invalid "
                                       "duration: '-5'"),
                (['--duration', 'x'], "argument --duration: invalid "
                                      "duration: 'x'")):
            with self.subTest(argv=argv):
                with tempfile.TemporaryDirectory() as temp_dir:
                    output = os.path.join(temp_dir, 'output')
                    with contextlib.redirect_stderr(io.StringIO()) as stderr:
                        with self.assertRaises(SystemExit) as cm:
                            main(['segment', vtt_file, '-o', output, *argv])

                    self.assertEqual(cm.exception.code, 2)
                    self.assertIn(expected_message, stderr.getvalue())
                    self.assertFalse(os.path.exists(output))

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
            # the message of the error depends on the platform
            with self.assertRaises(FileExistsError) as cm:
                os.makedirs(output, exist_ok=True)

            self.assert_cli_error(
                ['segment', vtt_file, '-o', output],
                f'{output}: {cm.exception.strerror}'
                )

    def test_cli_segment_into_folder_with_earlier_segments(self):
        vtt_file = str(
            pathlib.Path(__file__).resolve().parent
            / 'samples' / 'sample.vtt'
            )

        with tempfile.TemporaryDirectory() as temp_dir:
            main(['segment', vtt_file, '-o', temp_dir])
            earlier_files = sorted(os.listdir(temp_dir))

            self.assert_cli_error(
                ['segment', vtt_file, '-o', temp_dir],
                f'{temp_dir}: has the files of an earlier segmentation, '
                'such as fileSequence0.webvtt; use --overwrite to replace '
                'them'
                )
            self.assertEqual(sorted(os.listdir(temp_dir)), earlier_files)

            main(['segment', vtt_file, '-o', temp_dir, '-d', '20',
                  '--overwrite'])

            self.assertEqual(
                sorted(os.listdir(temp_dir)),
                [f'fileSequence{index}.webvtt' for index in range(4)]
                + ['prog_index.m3u8']
                )
            self.assertIn(
                '#EXT-X-TARGETDURATION:20',
                (pathlib.Path(temp_dir) / 'prog_index.m3u8').read_text()
                )

    def test_cli_segment_output_cannot_be_listed(self):
        vtt_file = str(
            pathlib.Path(__file__).resolve().parent
            / 'samples' / 'sample.vtt'
            )

        with tempfile.TemporaryDirectory() as temp_dir:
            error = PermissionError(
                errno.EACCES, os.strerror(errno.EACCES), temp_dir
                )
            with mock.patch.object(pathlib.Path, 'iterdir',
                                   side_effect=error):
                self.assert_cli_error(
                    ['segment', vtt_file, '-o', temp_dir],
                    f'{temp_dir}: {os.strerror(errno.EACCES)}'
                    )

    def test_cli_version(self):
        with contextlib.redirect_stdout(io.StringIO()) as stdout:
            with self.assertRaises(SystemExit) as cm:
                main(['--version'])

        self.assertEqual(cm.exception.code, 0)
        self.assertEqual(stdout.getvalue(), f'webvtt {webvtt.__version__}\n')

    def test_man_page_version(self):
        # the man page is shipped as it is, run make man after a new version
        man_page = pathlib.Path(__file__).parent.parent / 'man' / 'webvtt.1'
        header = next(
            line for line in man_page.read_text(encoding='utf-8').splitlines()
            if line.startswith('.TH')
            )
        self.assertIn(f'"{webvtt.__version__}"', header)

    def test_cli_as_module(self):
        vtt_file = str(
            pathlib.Path(__file__).resolve().parent
            / 'samples' / 'one_caption.vtt'
            )

        with mock.patch.object(sys, 'argv', ['webvtt', 'shift', vtt_file,
                                             '1']), \
                contextlib.redirect_stdout(io.StringIO()) as stdout:
            runpy.run_module('webvtt', run_name='__main__')

        self.assertIn('00:00:01.500 --> 00:00:08.000', stdout.getvalue())

    def test_cli_module_import_does_not_run(self):
        with mock.patch.object(sys, 'argv', ['webvtt', '--version']), \
                mock.patch.dict(sys.modules), \
                contextlib.redirect_stdout(io.StringIO()) as stdout:
            # import it again, also when another test or tool imported it
            sys.modules.pop('webvtt.__main__', None)
            importlib.import_module('webvtt.__main__')

        self.assertEqual(stdout.getvalue(), '')

    def test_cli_requires_command(self):
        with contextlib.redirect_stderr(io.StringIO()) as stderr:
            with self.assertRaises(SystemExit) as cm:
                main([])

        self.assertEqual(cm.exception.code, 2)
        self.assertIn(
            'the following arguments are required: command',
            stderr.getvalue()
            )


class CLICommandTestCase(unittest.TestCase):

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


class CLIShiftTestCase(CLICommandTestCase):

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

    def test_shift_rounds_offset_as_written(self):
        for offset, expected in (('1.0005', '00:00:01.501 --> 00:00:02.001'),
                                 ('-0.0005', '00:00:00.499 --> 00:00:00.999'),
                                 ('0.0025', '00:00:00.503 --> 00:00:01.003'),
                                 ('0.0004999',
                                  '00:00:00.500 --> 00:00:01.000'),
                                 ('2e-3', '00:00:00.502 --> 00:00:01.002'),
                                 ('259.0395',
                                  '00:04:19.540 --> 00:04:20.040')):
            with self.subTest(offset=offset):
                self.assertIn(
                    expected,
                    self.run_cli(['shift', self.vtt_file, offset])
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

    def test_shift_to_output_file_with_other_extension(self):
        output = os.path.join(self.temp_dir.name, 'shifted.txt')

        self.run_cli(['shift', self.vtt_file, '3', '-o', output])

        self.assertTrue(os.path.exists(output))
        self.assertFalse(os.path.exists(f'{output}.vtt'))

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

        # lines end with the line separator of the platform
        self.assertTrue(
            pathlib.Path(self.vtt_file).read_bytes().startswith(
                b'\xef\xbb\xbfWEBVTT' + os.linesep.encode() * 2 +
                b'00:00:01.500 --> 00:00:02.000'
                )
            )

    def test_shift_to_stdout_in_utf8(self):
        pathlib.Path(self.vtt_file).write_text(
            self.CAPTIONS.replace('Caption #1', 'Subtítulo #1'),
            encoding='utf-8'
            )
        stdout = io.TextIOWrapper(io.BytesIO(), encoding='ascii')

        with contextlib.redirect_stdout(stdout):
            main(['shift', self.vtt_file, '0'])

        self.assertEqual(
            stdout.buffer.getvalue().decode('utf-8'),
            self.CAPTIONS.replace('Caption #1', 'Subtítulo #1')
            )

    def test_shift_to_closed_pipe(self):
        class ClosedPipe(io.StringIO):
            def __init__(self, fd):
                super().__init__()
                self.fd = fd

            def write(self, s):
                raise BrokenPipeError

            def fileno(self):
                return self.fd

        with tempfile.TemporaryFile() as f:
            with contextlib.redirect_stdout(ClosedPipe(f.fileno())), \
                    contextlib.redirect_stderr(io.StringIO()) as stderr:
                with self.assertRaises(SystemExit) as cm:
                    main(['shift', self.vtt_file, '1'])

        self.assertEqual(cm.exception.code, 1)
        self.assertEqual(stderr.getvalue(), '')

    def test_shift_invalid_offset(self):
        for value in ('abc', 'nan', 'sNaN', 'inf', '1e400', ''):
            with self.subTest(value=value):
                self.assert_usage_error(
                    ['shift', self.vtt_file, value],
                    f'argument OFFSET: invalid offset: {value!r}'
                    )

    def test_shift_drop_before_zero(self):
        self.assertEqual(
            self.run_cli(['shift', self.vtt_file, '-2', '--drop-before-zero']),
            textwrap.dedent(
                '''
                WEBVTT

                00:00:00.000 --> 00:00:02.000
                Caption #1

                00:00:02.000 --> 00:00:05.000
                Caption #2
                '''
                ).lstrip()
            )

    def test_shift_drop_before_zero_from_start(self):
        self.assertEqual(
            self.run_cli(['shift', self.vtt_file, '-5', '--start',
                          '00:00:01.500', '--drop-before-zero']),
            textwrap.dedent(
                '''
                WEBVTT

                00:00:00.500 --> 00:00:01.000
                Credits

                00:00:00.000 --> 00:00:02.000
                Caption #2
                '''
                ).lstrip()
            )

    def test_shift_from_start_in_seconds(self):
        expected = self.run_cli(
            ['shift', self.vtt_file, '-0.5', '--start', '00:00:01.500']
            )
        # rounded to the nearest millisecond
        for start in ('1.5', '1.5e0', '1.5004'):
            with self.subTest(start=start):
                self.assertEqual(
                    self.run_cli(
                        ['shift', self.vtt_file, '-0.5', '-s', start]
                        ),
                    expected
                    )

    def test_shift_invalid_start(self):
        for start in ('1:2', '-5', 'x', 'nan', 'inf', '1e300'):
            with self.subTest(start=start):
                self.assert_usage_error(
                    ['shift', self.vtt_file, '1', '--start', start],
                    f"argument -s/--start: invalid timestamp: '{start}'"
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

    def test_after_largest_timestamp(self):
        for argv in (['shift', self.vtt_file, '1e300', '-o', self.vtt_file],
                     ['sync', self.vtt_file, '--fps', '1e300', '1',
                      '-o', self.vtt_file]):
            with self.subTest(command=argv[0]):
                with contextlib.redirect_stderr(io.StringIO()) as stderr:
                    with self.assertRaises(SystemExit) as cm:
                        main(argv)

                self.assertEqual(cm.exception.code, 1)
                self.assertEqual(
                    stderr.getvalue(),
                    f'webvtt: error: {self.vtt_file}: Time after the '
                    'largest timestamp 9999999999:59:59.999\n'
                    )
                self.assertEqual(
                    pathlib.Path(self.vtt_file).read_text(),
                    self.CAPTIONS
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


class CLIStdinTestCase(CLICommandTestCase):

    def run_cli_stdin(self, argv, data, stdin_encoding='ascii'):
        stdin = io.TextIOWrapper(io.BytesIO(data), encoding=stdin_encoding)
        with mock.patch.object(sys, 'stdin', stdin):
            return self.run_cli(argv)

    def assert_cli_stdin_error(self, argv, data, expected_message):
        with contextlib.redirect_stderr(io.StringIO()) as stderr:
            with self.assertRaises(SystemExit) as cm:
                self.run_cli_stdin(argv, data)

        self.assertEqual(cm.exception.code, 1)
        self.assertEqual(stderr.getvalue(),
                         f'webvtt: error: {expected_message}\n')

    def test_shift_and_sync_from_stdin(self):
        for argv in (['shift', '{}', '1.25'],
                     ['shift', '{}', '1', '--start', '00:00:01.500'],
                     ['sync', '{}', '--fps', '25', '24'],
                     ['sync', '{}', '-p', '1', '2', '-p', '4', '6']):
            with self.subTest(argv=argv):
                self.assertEqual(
                    self.run_cli_stdin(
                        [arg.format('-') for arg in argv],
                        self.CAPTIONS.encode('utf-8')
                        ),
                    self.run_cli([arg.format(self.vtt_file) for arg in argv])
                    )

    def test_segment_from_stdin(self):
        from_file = os.path.join(self.temp_dir.name, 'from_file')
        from_stdin = os.path.join(self.temp_dir.name, 'from_stdin')

        main(['segment', self.vtt_file, '-o', from_file, '-d', '2'])
        self.run_cli_stdin(['segment', '-', '-o', from_stdin, '-d', '2'],
                           self.CAPTIONS.encode('utf-8'))

        self.assertEqual(sorted(os.listdir(from_stdin)),
                         sorted(os.listdir(from_file)))
        for name in os.listdir(from_file):
            self.assertEqual(
                pathlib.Path(from_stdin, name).read_text(),
                pathlib.Path(from_file, name).read_text()
                )

    def test_segment_from_stdin_invalid_content(self):
        output = os.path.join(self.temp_dir.name, 'output')

        self.assert_cli_stdin_error(['segment', '-', '-o', output],
                                    b'not WebVTT',
                                    'standard input: not a valid WebVTT file')
        self.assertFalse(os.path.exists(output))

    def test_stdin_is_read_as_utf8(self):
        captions = self.CAPTIONS.replace('Caption #1', 'Subtítulo #1')

        for data in (captions.encode('utf-8'),
                     b'\xef\xbb\xbf' + captions.encode('utf-8'),
                     captions.replace('\n', '\r\n').encode('utf-8')):
            with self.subTest(data=data[:8]):
                self.assertEqual(
                    self.run_cli_stdin(['shift', '-', '0'], data),
                    captions
                    )

    def test_stdin_without_buffer(self):
        with mock.patch.object(sys, 'stdin', io.StringIO(self.CAPTIONS)):
            self.assertEqual(self.run_cli(['shift', '-', '0']),
                             self.CAPTIONS)

    def test_stdin_closed(self):
        with mock.patch.object(sys, 'stdin', None), \
                contextlib.redirect_stderr(io.StringIO()) as stderr:
            with self.assertRaises(SystemExit) as cm:
                main(['shift', '-', '1'])

        self.assertEqual(cm.exception.code, 1)
        self.assertEqual(
            stderr.getvalue(),
            f'webvtt: error: standard input: {os.strerror(errno.EBADF)}\n'
            )

    def test_stdin_to_output_file(self):
        output = os.path.join(self.temp_dir.name, 'shifted')

        self.assertEqual(
            self.run_cli_stdin(['shift', '-', '0', '-o', output],
                               self.CAPTIONS.encode('utf-8')),
            ''
            )

        self.assertEqual(pathlib.Path(f'{output}.vtt').read_text(),
                         self.CAPTIONS)

    def test_stdin_to_output_directory(self):
        self.assert_cli_stdin_error(
            ['shift', '-', '0', '-o', self.temp_dir.name],
            self.CAPTIONS.encode('utf-8'),
            f'{self.temp_dir.name}: is a directory, give a file name to '
            'save the captions read from standard input'
            )
        self.assertEqual(os.listdir(self.temp_dir.name), ['captions.vtt'])

    def test_stdin_invalid_content(self):
        for data, message in (
                (b'not WebVTT', 'not a valid WebVTT file'),
                (b'WEBVTT\n\n\xff\n', 'cannot be decoded as utf-8')):
            with self.subTest(data=data):
                self.assert_cli_stdin_error(['sync', '-', '--fps', '25', '24'],
                                            data,
                                            f'standard input: {message}')


class CLISyncTestCase(CLICommandTestCase):

    def test_sync_points_to_stdout(self):
        self.assertEqual(
            self.run_cli(['sync', self.vtt_file,
                          '-p', '00:00:00.500', '1',
                          '--point', '00:00:07.000', '13']),
            textwrap.dedent(
                '''
                WEBVTT

                00:00:01.000 --> 00:00:01.923
                Credits

                00:00:02.846 --> 00:00:07.462
                Caption #1

                00:00:07.462 --> 00:00:13.000
                Caption #2
                '''
                ).lstrip()
            )
        self.assertEqual(
            pathlib.Path(self.vtt_file).read_text(),
            self.CAPTIONS
            )

    def test_sync_fps(self):
        self.assertEqual(
            self.run_cli(['sync', self.vtt_file, '--fps', '25', '24']),
            textwrap.dedent(
                '''
                WEBVTT

                00:00:00.521 --> 00:00:01.042
                Credits

                00:00:01.563 --> 00:00:04.167
                Caption #1

                00:00:04.167 --> 00:00:07.292
                Caption #2
                '''
                ).lstrip()
            )

    def test_sync_fps_ratio(self):
        self.assertIn(
            '00:00:04.171 --> 00:00:07.299\nCaption #2',
            self.run_cli(['sync', self.vtt_file, '--fps', '25', '24000/1001'])
            )

    def test_sync_to_output_file(self):
        output = os.path.join(self.temp_dir.name, 'synced.vtt')

        self.assertEqual(
            self.run_cli(['sync', self.vtt_file, '-p', '0', '0',
                          '-p', '4', '8', '-o', output]),
            ''
            )
        self.assertIn(
            '00:00:03.000 --> 00:00:08.000\nCaption #1',
            pathlib.Path(output).read_text()
            )
        self.assertEqual(
            pathlib.Path(self.vtt_file).read_text(),
            self.CAPTIONS
            )

    def test_sync_in_place(self):
        self.run_cli(['sync', self.vtt_file, '--fps', '24', '24',
                      '-o', self.vtt_file])

        self.assertEqual(
            pathlib.Path(self.vtt_file).read_text(),
            self.CAPTIONS
            )

    def test_sync_invalid_arguments(self):
        for argv, expected_message in (
                (['-p', '1', '2'],
                 'At least two sync points are required'),
                (['-p', '1', '2', '-p', '1', '3'],
                 'Two sync points have the same time 00:00:01.000'),
                (['-p', '1', '5', '-p', '2', '4'],
                 'Sync points must keep the order of the captions'),
                (['-p', '1', '2', '-p', '-5', '3'],
                 "argument -p/--point: invalid timestamp: '-5'"),
                (['-p', '1', '2', '-p', 'x', '3'],
                 "argument -p/--point: invalid timestamp: 'x'"),
                (['-p', '1', '2', '-p', 'nan', '3'],
                 "argument -p/--point: invalid timestamp: 'nan'"),
                (['-p', '1', '2', '-p', '3', '1e300'],
                 "argument -p/--point: invalid timestamp: '1e300'"),
                (['-p', '1'],
                 'argument -p/--point: expected 2 arguments'),
                (['--fps', '0', '25'],
                 "argument --fps: invalid frame rate: '0'"),
                (['--fps', '25', 'inf'],
                 "argument --fps: invalid frame rate: 'inf'"),
                (['--fps', '25', '1/0'],
                 "argument --fps: invalid frame rate: '1/0'"),
                (['--fps', '25', '-24'],
                 "argument --fps: invalid frame rate: '-24'"),
                (['-p', '1', '2', '-p', '3', '4', '--fps', '25', '24'],
                 'argument --fps: not allowed with argument -p/--point'),
                ([], 'one of the arguments -p/--point --fps is required')):
            with self.subTest(argv=argv):
                self.assert_usage_error(
                    ['sync', self.vtt_file] + argv,
                    expected_message
                    )

    def test_sync_missing_file(self):
        vtt_file = os.path.join(self.temp_dir.name, 'missing.vtt')

        with contextlib.redirect_stderr(io.StringIO()) as stderr:
            with self.assertRaises(SystemExit) as cm:
                main(['sync', vtt_file, '--fps', '25', '24'])

        self.assertEqual(cm.exception.code, 1)
        self.assertEqual(
            stderr.getvalue(),
            f'webvtt: error: {vtt_file}: {os.strerror(errno.ENOENT)}\n'
            )


class CLIValidateTestCase(CLICommandTestCase):

    def validate(self, content, path=None):
        """Return the output and the exit status of validating content."""
        path = path or os.path.join(self.temp_dir.name, 'validate.vtt')
        pathlib.Path(path).write_text(content)

        with contextlib.redirect_stdout(io.StringIO()) as stdout:
            try:
                main(['validate', path])
            except SystemExit as error:
                return stdout.getvalue(), error.code

        return stdout.getvalue(), 0

    def test_validate_valid(self):
        self.assertEqual(self.validate(self.CAPTIONS), ('', 0))

    def test_validate_errors(self):
        path = os.path.join(self.temp_dir.name, 'errors.vtt')
        output, status = self.validate(
            'WEBVTT\n\n'
            '00:00:05.000 --> 00:00:06.000\na\n\n'
            '00:00:01.000 --> 00:00:02.000 region:fred\nb\n',
            path
            )

        self.assertEqual(status, 1)
        self.assertEqual(
            output,
            f'{path}: caption 2: error: starts at 00:00:01.000, before '
            'caption 1, which starts at 00:00:05.000\n'
            f"{path}: caption 2: error: is in the region 'fred', which is "
            'not defined\n'
            )

    def test_validate_warnings_only(self):
        path = os.path.join(self.temp_dir.name, 'warnings.vtt')
        output, status = self.validate(
            'WEBVTT\n\n'
            '00:00:01.000 --> 00:00:05.000\na\n\n'
            '00:00:02.000 --> 00:00:03.000\n<b></b>\n',
            path
            )

        self.assertEqual(status, 0)
        self.assertEqual(
            output,
            f'{path}: caption 2: warning: has no text\n'
            f'{path}: caption 2: warning: starts at 00:00:02.000, before '
            'caption 1 ends at 00:00:05.000\n'
            )

    def test_validate_skipped_blocks(self):
        path = os.path.join(self.temp_dir.name, 'skipped.vtt')
        output, status = self.validate(
            'WEBVTT\n\n00:00:01.000 --> 00:00:02.000\na\n\nnot a cue\n',
            path
            )

        self.assertEqual(status, 1)
        self.assertEqual(
            output,
            f"{path}: line 6: error: Invalid block ['not a cue']\n"
            )

    def test_validate_from_stdin(self):
        stdin = io.TextIOWrapper(io.BytesIO(
            b'WEBVTT\n\n00:00:01.000 --> 00:00:01.000\na\n'
            ))
        with mock.patch.object(sys, 'stdin', stdin):
            with contextlib.redirect_stdout(io.StringIO()) as stdout:
                with self.assertRaises(SystemExit) as cm:
                    main(['validate', '-'])

        self.assertEqual(cm.exception.code, 1)
        self.assertEqual(
            stdout.getvalue(),
            'standard input: caption 1: error: ends at 00:00:01.000, not '
            'after its start at 00:00:01.000\n'
            )

    def test_validate_invalid_file(self):
        vtt_file = str(
            pathlib.Path(__file__).resolve().parent
            / 'samples' / 'invalid.vtt'
            )

        with contextlib.redirect_stderr(io.StringIO()) as stderr:
            with self.assertRaises(SystemExit) as cm:
                main(['validate', vtt_file])

        self.assertEqual(cm.exception.code, 1)
        self.assertEqual(
            stderr.getvalue(),
            f'webvtt: error: {vtt_file}: not a valid WebVTT file\n'
            )

    def test_validate_requires_file(self):
        self.assert_usage_error(
            ['validate'],
            'the following arguments are required: PATH'
            )

    def test_validate_strict_parsing(self):
        for content, expected in (
                ('WEBVTTX\n\n00:00:01.000 --> 00:00:02.000\na\n',
                 "line 1: error: Invalid header 'WEBVTTX'"),
                ('WEBVTT\n\n00:00:01.000 --> 00:00:02.000 line:abc\na\n',
                 "line 3: error: Invalid cue setting 'line:abc'"),
                ('WEBVTT\n\n00:00:01.000 --> 00:00:02.000\na\n'
                 '00:00:03.000 --> 00:00:04.000\nb\n',
                 "line 5: error: Invalid cue block ['00:00:01.000 --> "
                 "00:00:02.000', 'a', '00:00:03.000 --> 00:00:04.000']")):
            with self.subTest(expected=expected):
                path = os.path.join(self.temp_dir.name, 'strict.vtt')
                self.assertEqual(
                    self.validate(content, path),
                    (f'{path}: {expected}\n', 1)
                    )

    def test_validate_strict_parsing_after_warnings(self):
        path = os.path.join(self.temp_dir.name, 'strict.vtt')
        self.assertEqual(
            self.validate(
                'WEBVTT\n\n00:00:01.000 --> 00:00:02.000 line:abc\n\n', path
                ),
            (f'{path}: caption 1: warning: has no text\n'
             f"{path}: line 3: error: Invalid cue setting 'line:abc'\n", 1)
            )

    def test_validate_strict_parsing_only_without_other_errors(self):
        path = os.path.join(self.temp_dir.name, 'strict.vtt')
        output, status = self.validate(
            'WEBVTT\n\n'
            '00:00:05.000 --> 00:00:06.000 line:abc\na\n\n'
            '00:00:01.000 --> 00:00:02.000\nb\n',
            path
            )

        self.assertEqual(status, 1)
        self.assertEqual(
            output,
            f'{path}: caption 2: error: starts at 00:00:01.000, before '
            'caption 1, which starts at 00:00:05.000\n'
            )

    def test_validate_from_stdin_strict_parsing(self):
        for stdin in (
                io.TextIOWrapper(io.BytesIO(
                    b'WEBVTT\n\n00:00:01.000 --> 00:00:02.000 line:abc\na\n'
                    )),
                io.StringIO(
                    'WEBVTT\n\n00:00:01.000 --> 00:00:02.000 line:abc\na\n'
                    )):
            with self.subTest(stdin=type(stdin).__name__):
                with mock.patch.object(sys, 'stdin', stdin):
                    with contextlib.redirect_stdout(io.StringIO()) as stdout:
                        with self.assertRaises(SystemExit) as cm:
                            main(['validate', '-'])

                self.assertEqual(cm.exception.code, 1)
                self.assertEqual(
                    stdout.getvalue(),
                    "standard input: line 3: error: Invalid cue setting "
                    "'line:abc'\n"
                    )

    def test_validate_closed_stdin(self):
        with mock.patch.object(sys, 'stdin', None):
            with contextlib.redirect_stderr(io.StringIO()) as stderr:
                with self.assertRaises(SystemExit) as cm:
                    main(['validate', '-'])

        self.assertEqual(cm.exception.code, 1)
        self.assertEqual(
            stderr.getvalue(),
            f'webvtt: error: standard input: {os.strerror(errno.EBADF)}\n'
            )


class CLIFormatsTestCase(CLICommandTestCase):

    SRT = textwrap.dedent('''\
        1
        00:00:00,500 --> 00:00:01,000
        {\\an8}<i>Credits</i>

        2
        00:00:01,500 --> 00:00:04,000
        <font color="red">Café</font>
        ''')

    SBV = textwrap.dedent('''\
        0:00:00.500,0:00:01.000
        Credits

        0:00:01.500,0:00:04.000
        Café
        ''')

    def path(self, name, content=None, encoding='utf-8'):
        path = os.path.join(self.temp_dir.name, name)
        if content is not None:
            pathlib.Path(path).write_bytes(content.encode(encoding))
        return path

    def read(self, path, encoding='utf-8'):
        return pathlib.Path(path).read_bytes().decode(encoding).replace(
            os.linesep, '\n')

    def run_error(self, argv):
        with contextlib.redirect_stderr(io.StringIO()) as stderr:
            with self.assertRaises(SystemExit) as cm:
                self.run_cli(argv)
        return cm.exception.code, stderr.getvalue()

    def test_shift_srt_keeps_format_and_formatting(self):
        srt = self.path('captions.srt', self.SRT)

        self.assertEqual(
            self.run_cli(['shift', srt, '1']),
            self.SRT.replace('00:00:00,500 --> 00:00:01,000',
                             '00:00:01,500 --> 00:00:02,000')
            .replace('00:00:01,500 --> 00:00:04,000',
                     '00:00:02,500 --> 00:00:05,000')
            )

    def test_sync_sbv_keeps_format(self):
        sbv = self.path('captions.sbv', self.SBV)

        self.assertEqual(
            self.run_cli(['sync', sbv, '-p', '0', '0', '-p', '1', '2']),
            self.SBV.replace('0:00:00.500,0:00:01.000',
                             '0:00:01.000,0:00:02.000')
            .replace('0:00:01.500,0:00:04.000', '0:00:03.000,0:00:08.000')
            )

    def test_webvtt_with_srt_extension_needs_format(self):
        srt = self.path('captions.srt', self.CAPTIONS)

        self.assertEqual(
            self.run_error(['shift', srt, '0']),
            (1, f'webvtt: error: {srt}: not a valid SRT file\n')
            )
        self.assertEqual(self.run_cli(['shift', srt, '0', '-f', 'vtt']),
                         self.CAPTIONS)

    def test_extension_is_case_insensitive(self):
        srt = self.path('CAPTIONS.SRT', self.SRT)

        self.assertTrue(self.run_cli(['shift', srt, '0']).startswith('1\n'))

    def test_shift_output_in_format_of_extension(self):
        srt = self.path('captions.srt', self.SRT)
        for name, start in (('out.vtt', 'WEBVTT\n'),
                            ('out.webvtt', 'WEBVTT\n'),
                            ('out.sbv', '0:00:00.500,'),
                            ('out.srt', '1\n'),
                            ('out', '1\n'),
                            ('out.txt', '1\n')):
            with self.subTest(name=name):
                output = self.path(name)
                self.run_cli(['shift', srt, '0', '-o', output])

                saved = output + ('.srt' if name == 'out' else '')
                self.assertTrue(self.read(saved).startswith(start))

    def test_shift_srt_in_place_keeps_encoding(self):
        srt = self.path('captions.srt', self.SRT, 'cp1252')
        self.run_cli(['shift', srt, '1', '--encoding', 'cp1252', '-o', srt])

        self.assertIn('00:00:01,500 --> 00:00:02,000',
                      self.read(srt, 'cp1252'))
        self.assertIn('Café', self.read(srt, 'cp1252'))

    def test_format_option_overrides_extension(self):
        txt = self.path('captions.txt', self.SRT)

        self.assertTrue(
            self.run_cli(['shift', txt, '0', '-f', 'srt']).startswith('1\n')
            )
        self.assertEqual(
            self.run_error(['shift', txt, '0']),
            (1, f'webvtt: error: {txt}: not a valid WebVTT file\n')
            )
        srt = self.path('captions.srt', self.SRT)
        for format, name in (('vtt', 'WebVTT'), ('sbv', 'SBV')):
            with self.subTest(format=format):
                self.assertEqual(
                    self.run_error(['shift', srt, '0', '--format', format]),
                    (1, f'webvtt: error: {srt}: not a valid {name} file\n')
                    )

    def test_invalid_format_and_encoding(self):
        srt = self.path('captions.srt', self.SRT)
        self.assert_usage_error(['shift', srt, '0', '-f', 'ass'],
                                "invalid choice: 'ass'")
        for encoding in ('nope', 'hex', 'rot13'):
            with self.subTest(encoding=encoding):
                self.assert_usage_error(
                    ['shift', srt, '0', '--encoding', encoding],
                    f"unknown encoding: '{encoding}'"
                    )

    def test_encoding_of_input(self):
        srt = self.path('captions.srt', self.SRT, 'cp1252')
        self.assertEqual(
            self.run_error(['convert', srt]),
            (1, f'webvtt: error: {srt}: cannot be decoded as utf-8\n')
            )

        self.assertIn('Café', self.run_cli(['convert', srt, '--encoding',
                                            'cp1252']))

    def test_stdin_in_format_and_encoding(self):
        argv = ['shift', '-', '0', '-f', 'srt', '--encoding', 'cp1252']
        stdin = io.TextIOWrapper(io.BytesIO(self.SRT.encode('cp1252')),
                                 encoding='ascii')
        with mock.patch.object(sys, 'stdin', stdin):
            self.assertEqual(self.run_cli(argv), self.SRT)

    def test_stdin_is_webvtt_by_default(self):
        stdin = io.TextIOWrapper(io.BytesIO(self.SRT.encode()))
        with mock.patch.object(sys, 'stdin', stdin):
            self.assertEqual(
                self.run_error(['shift', '-', '0']),
                (1, 'webvtt: error: standard input: not a valid WebVTT '
                    'file\n')
                )

    def test_segment_srt(self):
        srt = self.path('captions.srt', self.SRT)
        output = self.path('segments')
        main(['segment', srt, '-o', output])

        self.assertIn('<c.color-red>Café</c>',
                      self.read(os.path.join(output, 'fileSequence0.webvtt')))

    def test_validate_srt_and_sbv(self):
        srt = self.path('captions.srt', self.SRT +
                        '\n3\n00:00:03,000 --> 00:00:02,000\nBack\n')
        sbv = self.path('captions.sbv', self.SBV)

        with contextlib.redirect_stdout(io.StringIO()) as stdout, \
                self.assertRaises(SystemExit) as cm:
            main(['validate', srt])

        self.assertEqual(cm.exception.code, 1)
        self.assertEqual(
            stdout.getvalue(),
            f'{srt}: caption 3: error: ends at 00:00:02.000, not after its '
            'start at 00:00:03.000\n'
            )
        self.assertEqual(self.run_cli(['validate', sbv]), '')

    def test_validate_srt_skipped_blocks(self):
        srt = self.path('captions.srt',
                        self.SRT + '\n3\n00:00:03 --> 00:00:04,000\nx\n')
        with contextlib.redirect_stdout(io.StringIO()) as stdout, \
                self.assertRaises(SystemExit) as cm:
            main(['validate', srt])

        self.assertEqual(cm.exception.code, 1)
        self.assertEqual(
            stdout.getvalue(),
            f'{srt}: line 9: error: Invalid cue block '
            "['3', '00:00:03 --> 00:00:04,000', 'x']\n"
            )

    def test_validate_srt_from_stdin(self):
        stdin = io.TextIOWrapper(io.BytesIO(self.SRT.encode()))
        with mock.patch.object(sys, 'stdin', stdin):
            self.assertEqual(self.run_cli(['validate', '-', '-f', 'srt']),
                             '')

    def test_convert_to_stdout(self):
        srt = self.path('captions.srt', self.SRT)

        self.assertEqual(self.run_cli(['convert', srt]), textwrap.dedent('''\
            WEBVTT

            STYLE
            ::cue(.color-red) {
              color: red;
            }

            00:00:00.500 --> 00:00:01.000 line:0
            <i>Credits</i>

            00:00:01.500 --> 00:00:04.000
            <c.color-red>Café</c>
            '''))
        self.assertEqual(self.run_cli(['convert', srt, '-t', 'sbv']),
                         self.SBV)
        self.assertEqual(self.run_cli(['convert', srt, '--to', 'srt']),
                         self.SRT.replace('<i>Credits</i>', 'Credits')
                         .replace('<font color="red">Café</font>', 'Café'))
        self.assertEqual(
            self.run_cli(['convert', srt, '-t', 'srt', '--keep-formatting']),
            self.SRT
            )

    def test_convert_to_file(self):
        sbv = self.path('captions.sbv', self.SBV)
        for name, to, saved, start in (
                ('out.srt', None, 'out.srt', '1\n'),
                ('out.vtt', None, 'out.vtt', 'WEBVTT\n'),
                ('out', None, 'out.vtt', 'WEBVTT\n'),
                ('out.txt', None, 'out.txt', 'WEBVTT\n'),
                ('out.txt', 'srt', 'out.txt', '1\n'),
                ('out.vtt', 'sbv', 'out.vtt', '0:00:00.500,')):
            with self.subTest(name=name, to=to):
                argv = ['convert', sbv, '-o', self.path(name)]
                self.run_cli(argv + (['-t', to] if to else []))

                self.assertTrue(self.read(self.path(saved)).startswith(start))

    def test_convert_from_stdin(self):
        stdin = io.TextIOWrapper(io.BytesIO(self.SBV.encode()))
        with mock.patch.object(sys, 'stdin', stdin):
            self.assertEqual(
                self.run_cli(['convert', '-', '-f', 'sbv', '-t', 'sbv']),
                self.SBV
                )

    def test_convert_from_stdin_to_folder(self):
        stdin = io.TextIOWrapper(io.BytesIO(self.SBV.encode()))
        folder = self.path('folder')
        os.mkdir(folder)
        with mock.patch.object(sys, 'stdin', stdin):
            code, message = self.run_error(['convert', '-', '-f', 'sbv',
                                            '-o', folder])

        self.assertEqual(code, 1)
        self.assertIn(f'{folder}: is a directory', message)
