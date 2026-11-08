"""Segmenter module."""

import os
import pathlib
import re
from collections.abc import Iterable, Sequence

from . import utils, vtt
from .models import (
    Caption, Region, Style, Timestamp, _Position, _position_in_milliseconds
    )
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
        webvtt_path: str | WebVTT,
        output: str,
        seconds: int = DEFAULT_SECONDS,
        mpegts: int = DEFAULT_MPEGTS,
        *,
        overwrite: bool = False,
        duration: _Position | None = None
        ):
    """
    Segment a WebVTT captions file, or captions already read.

    Each segment has the styles and regions of the file and the captions
    shown during the segment, with their identifiers and cue settings.
    Comments are not written to the segments.

    :param webvtt_path: the path to the file, or a `WebVTT` instance, such
        as captions edited or read from another format, which is not
        changed
    :param output: the path to the destination folder
    :param seconds: the number of seconds for each segment, a whole number
        above zero
    :param mpegts: value for the MPEG-TS, from 0 to 2**33 - 1
    :param overwrite: replace the playlist and segments of an earlier run in
        the destination folder, deleting the segments the new playlist does
        not have. Other files in the folder are left alone.
    :param duration: the length of the media, as a timestamp, a number of
        seconds or a ``timedelta``, so the playlist covers all of it and its
        last segment ends with it. Without it, the playlist ends with the
        segment of the last caption, and every segment lasts the number of
        seconds.

    :raises TypeError: if seconds or mpegts is not an integer, or duration
        is not of a supported type
    :raises ValueError: if seconds is not above zero, mpegts is out of
        range, duration is not above zero or a caption does not start
        before it
    :raises FileExistsError: if the destination folder has the playlist or
        segments of an earlier run and overwrite is false
    """
    _check_seconds(seconds)
    _check_mpegts(mpegts)
    if duration is not None:
        _duration_in_milliseconds(duration)

    captions_file = (webvtt_path if isinstance(webvtt_path, WebVTT)
                     else WebVTT.read(webvtt_path))
    segments = slice_segments(captions_file.captions, seconds,
                              duration=duration)

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

    write_segments(output_folder, segments, mpegts,
                   styles=captions_file.styles,
                   regions=captions_file.regions
                   )
    write_manifest(output_folder, segments, seconds, duration=duration)
    if overwrite:
        _remove_segments_from(output_folder, len(segments))


def _earlier_output(output_folder: pathlib.Path) -> str | None:
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


def _duration_in_milliseconds(duration: _Position) -> int:
    """
    Return the length of the media in milliseconds.

    :param duration: a timestamp, as a string or a `Timestamp`, a number of
        seconds or a ``timedelta``
    :returns: the duration rounded to the nearest millisecond, halves away
        from zero

    :raises TypeError: if it is not of a supported type
    :raises ValueError: if it is not a valid timestamp or not above zero
    """
    try:
        milliseconds = _position_in_milliseconds(duration)
    except TypeError:
        raise TypeError(f'Invalid duration {duration!r}') from None
    except ValueError:
        milliseconds = 0

    if milliseconds <= 0:
        raise ValueError(f'Invalid duration {duration!r}')

    return milliseconds


def slice_segments(
        captions: Sequence[Caption],
        seconds: int,
        *,
        duration: _Position | None = None
        ) -> list[list[Caption]]:
    """
    Slice segments of captions based on seconds per segment.

    :param captions: the captions
    :param seconds: seconds per segment, a whole number above zero
    :param duration: the length of the media, as a timestamp, a number of
        seconds or a ``timedelta``, so the segments cover all of it, with a
        caption ending after it in the last segment. Without it, the
        segments end with the segment of the last caption.
    :returns: list of lists of `Caption` objects

    :raises TypeError: if seconds is not an integer, or duration is not of
        a supported type
    :raises ValueError: if seconds is not above zero, duration is not above
        zero or a caption does not start before it
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
    if duration is None:
        # one segment at least, so the playlist is not empty
        total_segments = max(
            (max(first, last) for first, last in indexes), default=0
            ) + 1
    else:
        duration_milliseconds = _duration_in_milliseconds(duration)
        for c in captions:
            if c.start_time.in_milliseconds() >= duration_milliseconds:
                end = Timestamp._from_milliseconds(duration_milliseconds)
                raise ValueError(
                    f'Caption at {c.start} does not start before the end '
                    f'of the media at {end}'
                    )
        total_segments = -(-duration_milliseconds // segment_milliseconds)
        # a caption ending after the media is in the last segment
        indexes = [(first, min(last, total_segments - 1))
                   for first, last in indexes]

    segments: list[list[Caption]] = [
        [] for _ in range(total_segments)
        ]

    for c, (first, last) in zip(captions, indexes):
        # a caption ending before it starts is in the segment it starts in
        for i in range(first, max(first, last) + 1):
            segments[i].append(c)

    return segments


def write_segments(
        output_folder: pathlib.Path,
        segments: Iterable[Iterable[Caption]],
        mpegts: int,
        styles: Iterable[Style] = (),
        regions: Iterable[Region] = ()
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
        segments: Iterable[Iterable[Caption]],
        seconds: int,
        *,
        duration: _Position | None = None
        ):
    """
    Write the manifest in the output folder.

    :param output_folder: folder where the manifest will be stored
    :param segments: the segments of `Caption` objects
    :param seconds: the seconds per segment, a whole number above zero
    :param duration: the length of the media, as a timestamp, a number of
        seconds or a ``timedelta``, for the duration of the last segment,
        which ends with it. Without it, every segment lasts the number of
        seconds.

    :raises TypeError: if seconds is not an integer, or duration is not of
        a supported type
    :raises ValueError: if seconds is not above zero, or duration is not
        above zero or does not end in the last segment
    """
    _check_seconds(seconds)
    segment_milliseconds = seconds * 1000
    durations = [segment_milliseconds for _ in segments]
    if duration is not None:
        duration_milliseconds = _duration_in_milliseconds(duration)
        last_start = (len(durations) - 1) * segment_milliseconds
        if not (last_start < duration_milliseconds
                <= last_start + segment_milliseconds):
            end = Timestamp._from_milliseconds(duration_milliseconds)
            raise ValueError(
                f'Duration {end} does not end in the last of '
                f'{len(durations)} segments of {seconds} seconds'
                )
        durations[-1] = duration_milliseconds - last_start

    manifest_file = output_folder / _MANIFEST_NAME
    with open(manifest_file, 'w', encoding='utf-8') as f:
        f.write('#EXTM3U\n')
        f.write(f'#EXT-X-TARGETDURATION:{seconds}\n')
        f.write('#EXT-X-VERSION:3\n')
        f.write('#EXT-X-PLAYLIST-TYPE:VOD\n')

        for index, milliseconds in enumerate(durations):
            f.write(f'#EXTINF:{milliseconds / 1000:.5f},\n')
            f.write(f'fileSequence{index}.webvtt\n')

        f.write('#EXT-X-ENDLIST\n')
