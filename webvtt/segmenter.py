"""Segmenter module."""

import typing
import os
import pathlib
import re

from . import utils, vtt
from .models import Caption, Region, Style
from .webvtt import WebVTT

DEFAULT_MPEGTS = 900000
DEFAULT_SECONDS = 10  # default number of seconds per segment

# MPEG-TS timestamps have 33 bits
_MAX_MPEGTS = 2 ** 33 - 1

_MANIFEST_NAME = 'prog_index.m3u8'
_SEGMENT_NAME_PATTERN = re.compile(r'fileSequence(0|[1-9][0-9]*)\.webvtt')
# ignoring case, as on case-insensitive file systems these are the names
# that would be written over
_EARLIER_OUTPUT_PATTERN = re.compile(
    r'prog_index\.m3u8|fileSequence(0|[1-9][0-9]*)\.webvtt', re.IGNORECASE
    )


def segment(
        webvtt_path: str,
        output: str,
        seconds: int = DEFAULT_SECONDS,
        mpegts: int = DEFAULT_MPEGTS,
        *,
        overwrite: bool = False
        ):
    """
    Segment a WebVTT captions file.

    Each segment has the styles and regions of the file and the captions
    shown during the segment, with their identifiers and cue settings.
    Comments are not written to the segments.

    :param webvtt_path: the path to the file
    :param output: the path to the destination folder
    :param seconds: the number of seconds for each segment, a whole number
        above zero
    :param mpegts: value for the MPEG-TS, from 0 to 2**33 - 1
    :param overwrite: replace the playlist and segments of an earlier run in
        the destination folder, deleting the segments the new playlist does
        not have. Other files in the folder are left alone.

    :raises TypeError: if seconds or mpegts is not an integer
    :raises ValueError: if seconds is not above zero or mpegts is out of
        range
    :raises FileExistsError: if the destination folder has the playlist or
        segments of an earlier run and overwrite is false
    """
    _check_seconds(seconds)
    _check_mpegts(mpegts)

    captions_file = WebVTT.read(webvtt_path)

    output_folder = pathlib.Path(output)
    if not overwrite:
        earlier_file = _earlier_output(output_folder)
        if earlier_file:
            raise FileExistsError(
                f'{str(output_folder)!r} has the files of an earlier '
                f'segmentation, such as {earlier_file!r}; use '
                'overwrite=True to replace them'
                )
    os.makedirs(output_folder, exist_ok=True)

    segments = slice_segments(captions_file.captions, seconds)
    write_segments(output_folder, segments, mpegts,
                   styles=captions_file.styles,
                   regions=captions_file.regions
                   )
    write_manifest(output_folder, segments, seconds)
    if overwrite:
        _remove_segments_from(output_folder, len(segments))


def _earlier_output(output_folder: pathlib.Path) -> typing.Optional[str]:
    """
    Find the playlist or a segment of an earlier run in the folder.

    :returns: the name of the first one, None if there is none or the
        folder does not exist
    """
    if not output_folder.is_dir():
        return None

    return next(
        (name for name in sorted(p.name for p in output_folder.iterdir())
         if _EARLIER_OUTPUT_PATTERN.fullmatch(name)),
        None
        )


def _remove_segments_from(output_folder: pathlib.Path, index: int):
    """Delete the segment files numbered from index onwards."""
    for path in output_folder.iterdir():
        match = _SEGMENT_NAME_PATTERN.fullmatch(path.name)
        if match and int(match.group(1)) >= index and path.is_file():
            path.unlink(missing_ok=True)


def _check_seconds(seconds: int):
    """
    Validate the number of seconds of each segment.

    :raises TypeError: if it is not an integer
    :raises ValueError: if it is not above zero
    """
    if type(seconds) is bool or not isinstance(seconds, int):
        raise TypeError(f'Invalid segment duration {seconds!r}')

    if seconds <= 0:
        raise ValueError(f'Invalid segment duration {seconds!r}')


def _check_mpegts(mpegts: int):
    """
    Validate the MPEG-TS value of the segments.

    :raises TypeError: if it is not an integer
    :raises ValueError: if it is not from 0 to 2**33 - 1
    """
    if type(mpegts) is bool or not isinstance(mpegts, int):
        raise TypeError(f'Invalid MPEG-TS value {mpegts!r}')

    if not 0 <= mpegts <= _MAX_MPEGTS:
        raise ValueError(f'Invalid MPEG-TS value {mpegts!r}')


def slice_segments(
        captions: typing.Sequence[Caption],
        seconds: int
        ) -> typing.List[typing.List[Caption]]:
    """
    Slice segments of captions based on seconds per segment.

    :param captions: the captions
    :param seconds: seconds per segment, a whole number above zero
    :returns: list of lists of `Caption` objects

    :raises TypeError: if seconds is not an integer
    :raises ValueError: if seconds is not above zero
    """
    _check_seconds(seconds)

    segment_milliseconds = seconds * 1000
    # the first and the last segment of each caption, the end time
    # exclusive, so a caption ending on a boundary is not in the next one
    indexes = [
        (c.start_time.in_milliseconds() // segment_milliseconds,
         (c.end_time.in_milliseconds() - 1) // segment_milliseconds)
        for c in captions
        ]
    # one segment at least, so the playlist is not empty
    total_segments = max(
        (max(first, last) for first, last in indexes), default=0
        ) + 1

    segments: typing.List[typing.List[Caption]] = [
        [] for _ in range(total_segments)
        ]

    for c, (first, last) in zip(captions, indexes):
        # a caption ending before it starts is in the segment it starts in
        for i in range(first, max(first, last) + 1):
            segments[i].append(c)

    return segments


def write_segments(
        output_folder: pathlib.Path,
        segments: typing.Iterable[typing.Iterable[Caption]],
        mpegts: int,
        styles: typing.Iterable[Style] = (),
        regions: typing.Iterable[Region] = ()
        ):
    """
    Write the segments to the output folder.

    Every segment is built before any is written, so a caption or style
    that cannot be written leaves the files of the folder unchanged.

    :param output_folder: folder where the segment files will be stored
    :param segments: the segments of `Caption` objects
    :param mpegts: value for the MPEG-TS, from 0 to 2**33 - 1
    :param styles: the styles written to every segment
    :param regions: the regions written to every segment, which the
        ``region`` cue setting of the captions refers to

    :raises TypeError: if mpegts is not an integer
    :raises ValueError: if mpegts is out of range, or the text of a caption
        or style could not be read back
    """
    _check_mpegts(mpegts)
    styles = list(styles)
    regions = list(regions)
    metadata = [f'X-TIMESTAMP-MAP=MPEGTS:{mpegts},LOCAL:00:00:00.000']

    contents = [
        vtt._to_str(segment, styles, [], [],
                    metadata=metadata,
                    regions=regions,
                    item_comments=False
                    )
        for segment in segments
        ]

    for index, content in enumerate(contents):
        segment_file = output_folder / f'fileSequence{index}.webvtt'
        utils._write_text_file(str(segment_file), content, 'utf-8')


def write_manifest(
        output_folder: pathlib.Path,
        segments: typing.Iterable[typing.Iterable[Caption]],
        seconds: int
        ):
    """
    Write the manifest in the output folder.

    :param output_folder: folder where the manifest will be stored
    :param segments: the segments of `Caption` objects
    :param seconds: the seconds per segment, a whole number above zero

    :raises TypeError: if seconds is not an integer
    :raises ValueError: if seconds is not above zero
    """
    _check_seconds(seconds)

    manifest_file = output_folder / _MANIFEST_NAME
    with open(manifest_file, 'w', encoding='utf-8') as f:
        f.write('#EXTM3U\n')
        f.write(f'#EXT-X-TARGETDURATION:{seconds}\n')
        f.write('#EXT-X-VERSION:3\n')
        f.write('#EXT-X-PLAYLIST-TYPE:VOD\n')

        for index, _ in enumerate(segments):
            f.write(f'#EXTINF:{seconds:.5f},\n')
            f.write(f'fileSequence{index}.webvtt\n')

        f.write('#EXT-X-ENDLIST\n')
