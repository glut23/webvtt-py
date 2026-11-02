import os
import unittest
import tempfile
import pathlib
import textwrap
import datetime
import math

import webvtt
from webvtt import segmenter
from webvtt.models import Caption, Timestamp

PATH_TO_SAMPLES = pathlib.Path(__file__).resolve().parent / 'samples'


class TestSegmenter(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.temp_dir.cleanup()

    def read_folder(self, folder):
        return {path.name: path.read_text()
                for path in pathlib.Path(folder).iterdir()}

    def test_segmentation_with_defaults(self):
        segmenter.segment(PATH_TO_SAMPLES / 'sample.vtt', self.temp_dir.name)

        _, dirs, files = next(os.walk(self.temp_dir.name))

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

        output_path = pathlib.Path(self.temp_dir.name)

        self.assertEqual(
            (output_path / 'prog_index.m3u8').read_text(),
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
                ).lstrip()
            )
        self.assertEqual(
            (output_path / 'fileSequence0.webvtt').read_text(),
            textwrap.dedent(
                '''
                WEBVTT
                X-TIMESTAMP-MAP=MPEGTS:900000,LOCAL:00:00:00.000

                00:00:00.500 --> 00:00:07.000
                Caption text #1

                00:00:07.000 --> 00:00:11.890
                Caption text #2
                '''
                ).lstrip()
            )
        self.assertEqual(
            (output_path / 'fileSequence1.webvtt').read_text(),
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
                ).lstrip()
            )
        self.assertEqual(
            (output_path / 'fileSequence2.webvtt').read_text(),
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
                ).lstrip()
            )
        self.assertEqual(
            (output_path / 'fileSequence3.webvtt').read_text(),
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
                ).lstrip()
            )
        self.assertEqual(
            (output_path / 'fileSequence4.webvtt').read_text(),
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
                ).lstrip()
            )
        self.assertEqual(
            (output_path / 'fileSequence5.webvtt').read_text(),
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
                ).lstrip()
            )
        self.assertEqual(
            (output_path / 'fileSequence6.webvtt').read_text(),
            textwrap.dedent(
                '''
                WEBVTT
                X-TIMESTAMP-MAP=MPEGTS:900000,LOCAL:00:00:00.000

                00:00:58.600 --> 00:01:01.350
                Caption text #15

                00:01:01.350 --> 00:01:04.300
                Caption text #16
                '''
                ).lstrip()
            )

    def test_segmentation_with_custom_values(self):
        segmenter.segment(
            webvtt_path=PATH_TO_SAMPLES / 'sample.vtt',
            output=self.temp_dir.name,
            seconds=30,
            mpegts=800000
            )

        _, dirs, files = next(os.walk(self.temp_dir.name))

        self.assertEqual(len(dirs), 0)
        self.assertEqual(len(files), 4)

        for expected_file in ('prog_index.m3u8',
                              'fileSequence0.webvtt',
                              'fileSequence1.webvtt',
                              'fileSequence2.webvtt',
                              ):
            self.assertIn(expected_file, files)

        output_path = pathlib.Path(self.temp_dir.name)

        self.assertEqual(
            (output_path / 'prog_index.m3u8').read_text(),
            textwrap.dedent(
                '''
                #EXTM3U
                #EXT-X-TARGETDURATION:30
                #EXT-X-VERSION:3
                #EXT-X-PLAYLIST-TYPE:VOD
                #EXTINF:30.00000,
                fileSequence0.webvtt
                #EXTINF:30.00000,
                fileSequence1.webvtt
                #EXTINF:30.00000,
                fileSequence2.webvtt
                #EXT-X-ENDLIST
                '''
                ).lstrip()
            )
        self.assertEqual(
            (output_path / 'fileSequence0.webvtt').read_text(),
            textwrap.dedent(
                '''
                WEBVTT
                X-TIMESTAMP-MAP=MPEGTS:800000,LOCAL:00:00:00.000

                00:00:00.500 --> 00:00:07.000
                Caption text #1

                00:00:07.000 --> 00:00:11.890
                Caption text #2

                00:00:11.890 --> 00:00:16.320
                Caption text #3

                00:00:16.320 --> 00:00:21.580
                Caption text #4

                00:00:21.580 --> 00:00:23.880
                Caption text #5

                00:00:23.880 --> 00:00:27.280
                Caption text #6

                00:00:27.280 --> 00:00:30.280
                Caption text #7
                '''
                ).lstrip()
            )
        self.assertEqual(
            (output_path / 'fileSequence1.webvtt').read_text(),
            textwrap.dedent(
                '''
                WEBVTT
                X-TIMESTAMP-MAP=MPEGTS:800000,LOCAL:00:00:00.000

                00:00:27.280 --> 00:00:30.280
                Caption text #7

                00:00:30.280 --> 00:00:36.510
                Caption text #8

                00:00:36.510 --> 00:00:38.870
                Caption text #9

                00:00:38.870 --> 00:00:45.000
                Caption text #10

                00:00:45.000 --> 00:00:47.000
                Caption text #11

                00:00:47.000 --> 00:00:50.970
                Caption text #12

                00:00:50.970 --> 00:00:54.440
                Caption text #13

                00:00:54.440 --> 00:00:58.600
                Caption text #14

                00:00:58.600 --> 00:01:01.350
                Caption text #15
                '''
                ).lstrip()
            )
        self.assertEqual(
            (output_path / 'fileSequence2.webvtt').read_text(),
            textwrap.dedent(
                '''
                WEBVTT
                X-TIMESTAMP-MAP=MPEGTS:800000,LOCAL:00:00:00.000

                00:00:58.600 --> 00:01:01.350
                Caption text #15

                00:01:01.350 --> 00:01:04.300
                Caption text #16
                '''
                ).lstrip()
            )

    def test_manifest_uses_segment_duration(self):
        for seconds in (5, 10, 30, 45):
            with self.subTest(seconds=seconds):
                segmenter.write_manifest(
                    pathlib.Path(self.temp_dir.name), [[], []], seconds
                    )
                manifest = (
                    pathlib.Path(self.temp_dir.name) / 'prog_index.m3u8'
                    ).read_text()
                self.assertIn(
                    f'#EXT-X-TARGETDURATION:{seconds}\n', manifest
                    )
                self.assertEqual(
                    [line for line in manifest.splitlines()
                     if line.startswith('#EXTINF:')],
                    [f'#EXTINF:{seconds:.5f},'] * 2
                    )

    def test_manifest_with_duration(self):
        output_folder = pathlib.Path(self.temp_dir.name)

        for duration, last in ((25.5, '5.50000'), (30, '10.00000'),
                               (20.001, '0.00100')):
            with self.subTest(duration=duration):
                segmenter.write_manifest(output_folder, [[], [], []], 10,
                                         duration=duration)

                manifest = (output_folder / 'prog_index.m3u8').read_text()
                self.assertIn('#EXT-X-TARGETDURATION:10\n', manifest)
                self.assertEqual(
                    [line for line in manifest.splitlines()
                     if line.startswith('#EXTINF:')],
                    ['#EXTINF:10.00000,', '#EXTINF:10.00000,',
                     f'#EXTINF:{last},']
                    )

    def test_manifest_duration_not_in_last_segment(self):
        output_folder = pathlib.Path(self.temp_dir.name)

        for segments, duration, message in (
                ([[], [], []], 20,
                 'Duration 00:00:20.000 does not end in the last of 3 '
                 'segments of 10 seconds'),
                ([[], [], []], 30.001,
                 'Duration 00:00:30.001 does not end in the last of 3 '
                 'segments of 10 seconds'),
                ([], 5,
                 'Duration 00:00:05.000 does not end in the last of 0 '
                 'segments of 10 seconds')):
            with self.subTest(segments=segments, duration=duration):
                with self.assertRaises(ValueError) as cm:
                    segmenter.write_manifest(output_folder, segments, 10,
                                             duration=duration)

                self.assertEqual(str(cm.exception), message)
                self.assertEqual(os.listdir(output_folder), [])

    def test_slice_segments_with_duration(self):
        captions = [
            Caption('00:00:00.500', '00:00:07.000', 'first'),
            Caption('00:00:22.000', '00:00:40.000', 'past the end'),
            ]

        for duration in (25.5, 25.5004, '00:00:25.500', '00:25.500',
                         Timestamp(0, 0, 25, 500),
                         datetime.timedelta(seconds=25.5)):
            with self.subTest(duration=duration):
                segments = segmenter.slice_segments(captions, 10,
                                                    duration=duration)

                self.assertEqual(
                    [[c.text for c in segment] for segment in segments],
                    [['first'], [], ['past the end']]
                    )

    def test_slice_segments_with_duration_and_no_captions(self):
        self.assertEqual(segmenter.slice_segments([], 10, duration=1), [[]])
        self.assertEqual(segmenter.slice_segments([], 10, duration=30),
                         [[], [], []])

    def test_slice_segments_caption_not_before_duration(self):
        for start in ('00:00:25.000', '00:01:00.000'):
            with self.subTest(start=start):
                captions = [
                    Caption('00:00:01.000', '00:00:02.000', 'first'),
                    Caption(start, '00:02:00.000', 'after the end'),
                    ]

                with self.assertRaises(ValueError) as cm:
                    segmenter.slice_segments(captions, 10, duration=25)

                self.assertEqual(
                    str(cm.exception),
                    f'Caption at {start} does not start before the end of '
                    'the media at 00:00:25.000'
                    )

    def test_slice_segments_invalid_duration(self):
        for duration, error in ((0, ValueError),
                                (-1, ValueError),
                                (0.0004, ValueError),
                                (math.nan, ValueError),
                                (math.inf, ValueError),
                                ('00:00:00.000', ValueError),
                                ('25 seconds', ValueError),
                                (True, TypeError),
                                ([25], TypeError)):
            with self.subTest(duration=duration):
                with self.assertRaises(error) as cm:
                    segmenter.slice_segments([], 10, duration=duration)

                self.assertEqual(str(cm.exception),
                                 f'Invalid duration {duration!r}')

    def test_slice_segments_last_caption_ends_on_segment_boundary(self):
        captions = [
            Caption('00:00.000', '00:09.000', 'first'),
            Caption('00:09.000', '00:10.000', 'second'),
            ]

        segments = segmenter.slice_segments(captions, 10)

        self.assertEqual(
            [[c.text for c in segment] for segment in segments],
            [['first', 'second']]
            )

    def test_slice_segments_caption_ends_on_internal_boundary(self):
        captions = [
            Caption('00:01.000', '00:10.000', 'first'),
            Caption('00:10.000', '00:10.001', 'second'),
            ]

        segments = segmenter.slice_segments(captions, 10)

        self.assertEqual(
            [[c.text for c in segment] for segment in segments],
            [['first'], ['second']]
            )

    def test_slice_segments_last_caption_ends_mid_second(self):
        for end in ('00:10.001', '00:10.500'):
            with self.subTest(end=end):
                captions = [Caption('00:00.000', end, 'only')]

                segments = segmenter.slice_segments(captions, 10)

                self.assertEqual(
                    [[c.text for c in segment] for segment in segments],
                    [['only'], ['only']]
                    )

    def test_slice_segments_zero_duration_caption_on_boundary(self):
        captions = [Caption('00:10.000', '00:10.000', 'only')]

        segments = segmenter.slice_segments(captions, 10)

        self.assertEqual(
            [[c.text for c in segment] for segment in segments],
            [[], ['only']]
            )

    def test_slice_segments_caption_ends_after_last_caption(self):
        captions = [
            Caption('00:00.000', '00:35.000', 'long'),
            Caption('00:01.000', '00:05.000', 'short'),
            ]

        segments = segmenter.slice_segments(captions, 10)

        self.assertEqual(
            [[c.text for c in segment] for segment in segments],
            [['long', 'short'], ['long'], ['long'], ['long']]
            )

    def test_slice_segments_caption_ends_before_it_starts(self):
        captions = [Caption('00:25.000', '00:05.000', 'backwards')]

        segments = segmenter.slice_segments(captions, 10)

        self.assertEqual(
            [[c.text for c in segment] for segment in segments],
            [[], [], ['backwards']]
            )

    def test_slice_segments_caption_ends_before_it_starts_with_others(self):
        captions = [
            Caption('00:01.000', '00:15.000', 'first'),
            Caption('00:12.000', '00:11.000', 'backwards'),
            Caption('00:30.000', '00:29.000', 'last'),
            ]

        segments = segmenter.slice_segments(captions, 10)

        self.assertEqual(
            [[c.text for c in segment] for segment in segments],
            [['first'], ['first', 'backwards'], [], ['last']]
            )

    def test_segmentation_keeps_cue_settings(self):
        webvtt_path = pathlib.Path(self.temp_dir.name) / 'captions.vtt'
        webvtt_path.write_text(textwrap.dedent('''
            WEBVTT

            00:00:00.500 --> 00:00:07.000 line:0 align:start
            Caption text #1
            ''').lstrip())
        output_path = pathlib.Path(self.temp_dir.name) / 'output'

        segmenter.segment(webvtt_path, output_path)

        self.assertEqual(
            (output_path / 'fileSequence0.webvtt').read_text(),
            textwrap.dedent(
                '''
                WEBVTT
                X-TIMESTAMP-MAP=MPEGTS:900000,LOCAL:00:00:00.000

                00:00:00.500 --> 00:00:07.000 line:0 align:start
                Caption text #1
                '''
                ).lstrip()
            )

    def test_segmentation_keeps_styles_regions_and_identifiers(self):
        webvtt_path = pathlib.Path(self.temp_dir.name) / 'captions.vtt'
        webvtt_path.write_text(textwrap.dedent('''
            WEBVTT

            REGION
            id:fred
            width:40%

            NOTE comment of the style

            STYLE
            ::cue(.yellow) {
              color: yellow;
            }

            NOTE comment of the first caption

            intro
            00:00:00.500 --> 00:00:07.000 region:fred
            <c.yellow>Caption text #1</c>

            00:00:12.000 --> 00:00:14.000
            Caption text #2
            ''').lstrip())
        output_path = pathlib.Path(self.temp_dir.name) / 'output'

        segmenter.segment(webvtt_path, output_path)

        header = textwrap.dedent('''
            WEBVTT
            X-TIMESTAMP-MAP=MPEGTS:900000,LOCAL:00:00:00.000

            REGION
            id:fred
            width:40%

            STYLE
            ::cue(.yellow) {
              color: yellow;
            }
            ''').lstrip()
        self.assertEqual(
            (output_path / 'fileSequence0.webvtt').read_text(),
            header + textwrap.dedent('''
                intro
                00:00:00.500 --> 00:00:07.000 region:fred
                <c.yellow>Caption text #1</c>
                ''')
            )
        self.assertEqual(
            (output_path / 'fileSequence1.webvtt').read_text(),
            header + textwrap.dedent('''
                00:00:12.000 --> 00:00:14.000
                Caption text #2
                ''')
            )

    def test_segment_invalid_arguments(self):
        webvtt_path = PATH_TO_SAMPLES / 'sample.vtt'
        output_path = pathlib.Path(self.temp_dir.name) / 'output'

        for arguments, error in (({'seconds': 0}, ValueError),
                                 ({'seconds': -10}, ValueError),
                                 ({'seconds': 2.5}, TypeError),
                                 ({'seconds': '10'}, TypeError),
                                 ({'seconds': True}, TypeError),
                                 ({'mpegts': -1}, ValueError),
                                 ({'mpegts': 2 ** 33}, ValueError),
                                 ({'mpegts': 9e5}, TypeError),
                                 ({'mpegts': None}, TypeError),
                                 ({'duration': 0}, ValueError),
                                 ({'duration': 1}, ValueError),
                                 ({'duration': b'25'}, TypeError)):
            with self.subTest(arguments=arguments):
                with self.assertRaises(error):
                    segmenter.segment(webvtt_path, output_path, **arguments)
                self.assertFalse(output_path.exists())

    def test_segment_functions_validate_arguments(self):
        output_folder = pathlib.Path(self.temp_dir.name)
        captions = [Caption('00:00:00.500', '00:00:07.000', 'Caption')]

        for call, error in (
                (lambda: segmenter.slice_segments(captions, 0), ValueError),
                (lambda: segmenter.write_manifest(output_folder, [], 2.5),
                 TypeError),
                (lambda: segmenter.write_segments(output_folder, [captions],
                                                  -1), ValueError)):
            with self.assertRaises(error):
                call()

        self.assertEqual(os.listdir(output_folder), [])

    def test_write_segments_rejected_caption_writes_no_files(self):
        output_folder = pathlib.Path(self.temp_dir.name)
        for index in range(3):
            (output_folder / f'fileSequence{index}.webvtt').write_text(
                f'previous run {index}'
                )

        with self.assertRaises(ValueError):
            segmenter.write_segments(
                output_folder,
                [[Caption('00:00:01.000', '00:00:02.000', 'Caption')],
                 [],
                 [Caption('00:00:21.000', '00:00:22.000', 'a\n\nb')]],
                segmenter.DEFAULT_MPEGTS
                )

        for index in range(3):
            self.assertEqual(
                (output_folder / f'fileSequence{index}.webvtt').read_text(),
                f'previous run {index}'
                )

    def test_segment_into_folder_with_earlier_segments(self):
        output_folder = pathlib.Path(self.temp_dir.name)
        segmenter.segment(PATH_TO_SAMPLES / 'sample.vtt', output_folder)
        earlier_files = self.read_folder(output_folder)

        with self.assertRaises(FileExistsError) as cm:
            segmenter.segment(PATH_TO_SAMPLES / 'one_caption.vtt',
                              output_folder)

        self.assertEqual(
            str(cm.exception),
            f'{str(output_folder)!r} has the files of an earlier '
            "segmentation, such as 'fileSequence0.webvtt'; use "
            'overwrite=True to replace them'
            )
        self.assertEqual(self.read_folder(output_folder), earlier_files)

    def test_segment_into_folder_with_earlier_playlist(self):
        output_folder = pathlib.Path(self.temp_dir.name)
        (output_folder / 'prog_index.m3u8').write_text('video playlist')

        with self.assertRaisesRegex(FileExistsError, "'prog_index.m3u8'"):
            segmenter.segment(PATH_TO_SAMPLES / 'one_caption.vtt',
                              output_folder)

        self.assertEqual(os.listdir(output_folder), ['prog_index.m3u8'])
        self.assertEqual((output_folder / 'prog_index.m3u8').read_text(),
                         'video playlist')

    def test_segment_into_folder_with_earlier_files_in_other_case(self):
        output_folder = pathlib.Path(self.temp_dir.name)
        for name in ['PROG_INDEX.M3U8', 'FileSequence3.WebVTT']:
            (output_folder / name).write_text('earlier run')

            with self.assertRaisesRegex(FileExistsError, repr(name)):
                segmenter.segment(PATH_TO_SAMPLES / 'one_caption.vtt',
                                  output_folder)

            (output_folder / name).unlink()

    def test_segment_into_folder_with_other_files(self):
        output_folder = pathlib.Path(self.temp_dir.name)
        others = ['fileSequence01.webvtt', 'fileSequence5.vtt',
                  'fileSequence-1.webvtt', 'notes.txt']
        for name in others:
            (output_folder / name).write_text('other file')

        segmenter.segment(PATH_TO_SAMPLES / 'one_caption.vtt', output_folder)

        self.assertEqual(
            sorted(os.listdir(output_folder)),
            sorted(others + ['fileSequence0.webvtt', 'prog_index.m3u8'])
            )

    def test_segment_overwrite(self):
        output_folder = pathlib.Path(self.temp_dir.name)
        segmenter.segment(PATH_TO_SAMPLES / 'sample.vtt', output_folder)
        self.assertIn('fileSequence6.webvtt', os.listdir(output_folder))
        others = ['fileSequence01.webvtt', 'fileSequence5.vtt',
                  'fileSequence-1.webvtt', 'notes.txt']
        for name in others:
            (output_folder / name).write_text('other file')
        (output_folder / 'fileSequence9.webvtt').mkdir()

        segmenter.segment(PATH_TO_SAMPLES / 'one_caption.vtt', output_folder,
                          overwrite=True)

        self.assertEqual(
            sorted(os.listdir(output_folder)),
            sorted(others + ['fileSequence0.webvtt', 'fileSequence9.webvtt',
                             'prog_index.m3u8'])
            )
        for name in others:
            self.assertEqual((output_folder / name).read_text(), 'other file')
        manifest = (output_folder / 'prog_index.m3u8').read_text()
        self.assertIn('fileSequence0.webvtt', manifest)
        self.assertNotIn('fileSequence1.webvtt', manifest)
        self.assertIn('00:00:00.500 --> 00:00:07.000',
                      (output_folder / 'fileSequence0.webvtt').read_text())

    def test_segment_overwrite_without_earlier_files(self):
        output_folder = pathlib.Path(self.temp_dir.name) / 'output'

        segmenter.segment(PATH_TO_SAMPLES / 'one_caption.vtt', output_folder,
                          overwrite=True)

        self.assertEqual(sorted(os.listdir(output_folder)),
                         ['fileSequence0.webvtt', 'prog_index.m3u8'])

    def test_segmentation_mpegts_range(self):
        output_path = pathlib.Path(self.temp_dir.name) / 'output'

        segmenter.segment(PATH_TO_SAMPLES / 'one_caption.vtt', output_path,
                          mpegts=2 ** 33 - 1)

        self.assertIn(
            'X-TIMESTAMP-MAP=MPEGTS:8589934591,LOCAL:00:00:00.000',
            (output_path / 'fileSequence0.webvtt').read_text()
            )

    def test_segment_with_duration(self):
        output_folder = pathlib.Path(self.temp_dir.name)

        segmenter.segment(PATH_TO_SAMPLES / 'one_caption.vtt', output_folder,
                          duration='00:00:25.500')

        self.assertEqual(
            sorted(os.listdir(output_folder)),
            ['fileSequence0.webvtt', 'fileSequence1.webvtt',
             'fileSequence2.webvtt', 'prog_index.m3u8']
            )
        self.assertEqual(
            (output_folder / 'fileSequence2.webvtt').read_text(),
            'WEBVTT\n'
            'X-TIMESTAMP-MAP=MPEGTS:900000,LOCAL:00:00:00.000\n'
            )
        self.assertEqual(
            (output_folder / 'prog_index.m3u8').read_text(),
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
                #EXTINF:5.50000,
                fileSequence2.webvtt
                #EXT-X-ENDLIST
                '''
                ).lstrip()
            )

    def test_segment_invalid_duration_before_reading_file(self):
        with self.assertRaises(ValueError):
            segmenter.segment(PATH_TO_SAMPLES / 'missing.vtt',
                              self.temp_dir.name, duration=0)

    def test_segment_webvtt_instance(self):
        from_path = pathlib.Path(self.temp_dir.name) / 'from_path'
        from_instance = pathlib.Path(self.temp_dir.name) / 'from_instance'
        vtt = webvtt.read(PATH_TO_SAMPLES / 'regions.vtt')
        captions = [(c.start, c.end, c.raw_text) for c in vtt.captions]

        segmenter.segment(PATH_TO_SAMPLES / 'regions.vtt', from_path)
        segmenter.segment(vtt, from_instance)

        self.assertEqual(self.read_folder(from_instance),
                         self.read_folder(from_path))
        self.assertEqual(
            [(c.start, c.end, c.raw_text) for c in vtt.captions], captions
            )
        self.assertEqual(vtt.file, str(PATH_TO_SAMPLES / 'regions.vtt'))

    def test_segment_captions_in_memory(self):
        vtt = webvtt.WebVTT(captions=[
            Caption('00:00:01.000', '00:00:04.000', 'Hello'),
            Caption('00:00:12.000', '00:00:13.000', 'World'),
            ])
        vtt.shift(1)

        segmenter.segment(vtt, self.temp_dir.name, seconds=5)

        self.assertEqual(
            self.read_folder(self.temp_dir.name)['fileSequence2.webvtt'],
            'WEBVTT\n'
            'X-TIMESTAMP-MAP=MPEGTS:900000,LOCAL:00:00:00.000\n'
            '\n'
            '00:00:13.000 --> 00:00:14.000\n'
            'World\n'
            )
        self.assertIsNone(vtt.file)

    def test_segment_captions_read_from_srt(self):
        from_vtt = pathlib.Path(self.temp_dir.name) / 'from_vtt'
        from_srt = pathlib.Path(self.temp_dir.name) / 'from_srt'
        srt_captions = webvtt.from_srt(PATH_TO_SAMPLES / 'sample.srt')

        segmenter.segment(srt_captions, from_srt)
        segmenter.segment(webvtt.from_string(srt_captions.content), from_vtt)

        self.assertEqual(self.read_folder(from_srt),
                         self.read_folder(from_vtt))

    def test_segment_with_no_captions(self):
        segmenter.segment(
            webvtt_path=PATH_TO_SAMPLES / 'no_captions.vtt',
            output=self.temp_dir.name
            )

        _, dirs, files = next(os.walk(self.temp_dir.name))

        self.assertEqual(len(dirs), 0)
        self.assertEqual(len(files), 2)
        self.assertIn('prog_index.m3u8', files)
        self.assertIn('fileSequence0.webvtt', files)

        self.assertEqual(
            (pathlib.Path(self.temp_dir.name) / 'fileSequence0.webvtt').read_text(),
            'WEBVTT\n'
            'X-TIMESTAMP-MAP=MPEGTS:900000,LOCAL:00:00:00.000\n'
            )

        self.assertEqual(
            (pathlib.Path(self.temp_dir.name) / 'prog_index.m3u8').read_text(),
            textwrap.dedent(
                '''
                #EXTM3U
                #EXT-X-TARGETDURATION:10
                #EXT-X-VERSION:3
                #EXT-X-PLAYLIST-TYPE:VOD
                #EXTINF:10.00000,
                fileSequence0.webvtt
                #EXT-X-ENDLIST
                '''
                ).lstrip()
            )

    def test_write_segments_error_keeps_file(self):
        output_folder = pathlib.Path(self.temp_dir.name)
        segment_file = output_folder / 'fileSequence0.webvtt'
        segment_file.write_text('old')

        with self.assertRaises(UnicodeEncodeError):
            segmenter.write_segments(
                output_folder,
                [[Caption('00:00:00.000', '00:00:01.000', '\ud800')]],
                segmenter.DEFAULT_MPEGTS
                )

        self.assertEqual(segment_file.read_text(), 'old')
