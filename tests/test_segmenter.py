import os
import unittest
import tempfile
import pathlib
import textwrap

from webvtt import segmenter
from webvtt.models import Caption

PATH_TO_SAMPLES = pathlib.Path(__file__).resolve().parent / 'samples'


class TestSegmenter(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.temp_dir.cleanup()

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

    def test_slice_segments_last_caption_ends_on_segment_boundary(self):
        captions = [
            Caption('00:00.000', '00:09.000', 'first'),
            Caption('00:09.000', '00:10.000', 'second'),
            ]

        segments = segmenter.slice_segments(captions, 10)

        self.assertEqual(
            [[c.text for c in segment] for segment in segments],
            [['first', 'second'], ['second']]
            )

    def test_slice_segments_last_caption_ends_mid_second(self):
        captions = [Caption('00:00.000', '00:10.500', 'only')]

        segments = segmenter.slice_segments(captions, 10)

        self.assertEqual(
            [[c.text for c in segment] for segment in segments],
            [['only'], ['only']]
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
                                 ({'mpegts': None}, TypeError)):
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

    def test_segmentation_mpegts_range(self):
        output_path = pathlib.Path(self.temp_dir.name) / 'output'

        segmenter.segment(PATH_TO_SAMPLES / 'one_caption.vtt', output_path,
                          mpegts=2 ** 33 - 1)

        self.assertIn(
            'X-TIMESTAMP-MAP=MPEGTS:8589934591,LOCAL:00:00:00.000',
            (output_path / 'fileSequence0.webvtt').read_text()
            )

    def test_segment_with_no_captions(self):
        segmenter.segment(
            webvtt_path=PATH_TO_SAMPLES / 'no_captions.vtt',
            output=self.temp_dir.name
            )

        _, dirs, files = next(os.walk(self.temp_dir.name))

        self.assertEqual(len(dirs), 0)
        self.assertEqual(len(files), 1)
        self.assertIn('prog_index.m3u8', files)

        self.assertEqual(
            (pathlib.Path(self.temp_dir.name) / 'prog_index.m3u8').read_text(),
            textwrap.dedent(
                '''
                #EXTM3U
                #EXT-X-TARGETDURATION:10
                #EXT-X-VERSION:3
                #EXT-X-PLAYLIST-TYPE:VOD
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
