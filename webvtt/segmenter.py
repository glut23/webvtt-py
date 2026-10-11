"""Segmenter module."""

import typing
import os
import pathlib
from math import ceil, floor

from .webvtt import WebVTT, Caption

DEFAULT_MPEGTS = 900000
DEFAULT_SECONDS = 10  # default number of seconds per segment


def segment(
        webvtt_path: str,
        output: str,
        seconds: int = DEFAULT_SECONDS,
        mpegts: int = DEFAULT_MPEGTS
        ):
    """
    Segment a WebVTT captions file.

    :param webvtt_path: the path to the file
    :param output: the path to the destination folder
    :param seconds: the number of seconds for each segment
    :param mpegts: value for the MPEG-TS
    """
    captions = WebVTT.read(webvtt_path).captions

    output_folder = pathlib.Path(output)
    os.makedirs(output_folder, exist_ok=True)

    segments = slice_segments(captions, seconds)
    write_segments(output_folder, segments, mpegts)
    write_manifest(output_folder, segments, seconds)


def slice_segments(
        captions: typing.Sequence[Caption],
        seconds: int
        ) -> typing.List[typing.List[Caption]]:
    """
    Slice segments of captions based on seconds per segment.

    :param captions: the captions
    :param seconds: seconds per segment
    :returns: list of lists of `Caption` objects
    """
    total_segments = (
        0
        if not captions else
        int(ceil(captions[-1].end_in_seconds / seconds))
    )

    segments: typing.List[typing.List[Caption]] = [
        [] for _ in range(total_segments)
        ]

    for c in captions:
        segment_index_start = floor(c.start_in_seconds / seconds)
        segments[segment_index_start].append(c)

        # Also include a caption in other segments based on the end time.
        segment_index_end = floor(c.end_in_seconds / seconds)
        if segment_index_end > segment_index_start:
            for i in range(segment_index_start + 1, segment_index_end + 1):
                segments[i].append(c)

    return segments


def write_segments(
        output_folder: pathlib.Path,
        segments: typing.Iterable[typing.Iterable[Caption]],
        mpegts: int
        ):
    """
    Write the segments to the output folder.

    :param output_folder: folder where the segment files will be stored
    :param segments: the segments of `Caption` objects
    :param mpegts: value for the MPEG-TS
    """
    for index, segment in enumerate(segments):
        segment_file = output_folder / f'fileSequence{index}.webvtt'

        with open(segment_file, 'w', encoding='utf-8') as f:
            f.write('WEBVTT\n')
            f.write(f'X-TIMESTAMP-MAP=MPEGTS:{mpegts},'
                    'LOCAL:00:00:00.000\n'
                    )

            for caption in segment:
                f.write('\n{} --> {}\n'.format(caption.start, caption.end))
                f.writelines(f'{line}\n' for line in caption.lines)


def write_manifest(
        output_folder: pathlib.Path,
        segments: typing.Iterable[typing.Iterable[Caption]],
        seconds: int
        ):
    """
    Write the manifest in the output folder.

    :param output_folder: folder where the manifest will be stored
    :param segments: the segments of `Caption` objects
    :param seconds: the seconds per segment
    """
    manifest_file = output_folder / 'prog_index.m3u8'
    with open(manifest_file, 'w', encoding='utf-8') as f:
        f.write('#EXTM3U\n')
        f.write(f'#EXT-X-TARGETDURATION:{seconds}\n')
        f.write('#EXT-X-VERSION:3\n')
        f.write('#EXT-X-PLAYLIST-TYPE:VOD\n')

        for index, _ in enumerate(segments):
            f.write(f'#EXTINF:{seconds:.5f},\n')
            f.write(f'fileSequence{index}.webvtt\n')

        f.write('#EXT-X-ENDLIST\n')
