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
                              "value: 'x'")):
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
                 'Time after the largest timestamp 9999999999:59:59.999'),
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
