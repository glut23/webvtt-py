"""CLI module."""

import argparse
import errno
import fractions
import math
import os
import pathlib
import sys
import typing

from . import __version__, segmenter
from .webvtt import WebVTT
from .models import Timestamp, _sync_mapping
from .errors import (
    MalformedFileError, MalformedCaptionError, MissingFilenameError
    )

# the path that reads the captions from standard input
_STDIN = '-'


def main(argv: typing.Optional[typing.Sequence] = None):
    """
    Segment, shift or sync a WebVTT file from command line.

    :param argv: command line arguments
    """
    arguments = argparse.ArgumentParser(
        prog='webvtt',
        description='Segment, shift and sync WebVTT caption files.'
        )
    arguments.add_argument(
        '--version',
        action='version',
        version=f'%(prog)s {__version__}'
        )
    commands = arguments.add_subparsers(
        dest='command',
        required=True,
        help='command to perform'
        )

    segment_command = commands.add_parser(
        'segment',
        help='segment a WebVTT file for HLS',
        description='Segment WebVTT files for HTTP Live Streaming (HLS).',
        epilog=(
            'The output directory will contain a playlist named '
            'prog_index.m3u8 and one fileSequenceN.webvtt file per segment. '
            'Captions spanning multiple segments are included in each of '
            'them. An output directory with the files of an earlier run is '
            'an error unless --overwrite is given.'
            )
        )
    segment_command.add_argument(
        'file',
        metavar='PATH',
        help='WebVTT file, or - to read standard input'
        )
    segment_command.add_argument(
        '-o', '--output',
        metavar='PATH',
        required=True,
        help='output directory, created if it does not exist'
        )
    segment_command.add_argument(
        '-d', '--target-duration',
        metavar='NUMBER',
        type=_duration,
        default=segmenter.DEFAULT_SECONDS,
        help='target duration of each segment in seconds, default: %(default)s'
        )
    segment_command.add_argument(
        '-m', '--mpegts',
        metavar='NUMBER',
        type=_mpegts,
        default=segmenter.DEFAULT_MPEGTS,
        help=('MPEG-TS value for the X-TIMESTAMP-MAP header of each segment, '
              'default: %(default)s')
        )
    segment_command.add_argument(
        '--duration',
        metavar='TIME',
        type=_media_duration,
        help=('length of the media, as a timestamp or a number of seconds, '
              'so the playlist covers all of it and its last segment ends '
              'with it')
        )
    segment_command.add_argument(
        '--overwrite',
        action='store_true',
        help=('replace the playlist and segments of an earlier run in the '
              'output directory')
        )
    segment_command.set_defaults(run=_segment)

    shift_command = commands.add_parser(
        'shift',
        help='shift the timestamps of a WebVTT file',
        description='Shift the timestamps of the captions in a WebVTT file.',
        epilog=(
            'The offset is rounded to the nearest millisecond, halves away '
            'from zero, and a timestamp that would fall before zero is set '
            'to 00:00:00.000, so captions that end at or before zero are '
            'kept at 00:00:00.000 unless --drop-before-zero is given. '
            'The captions are written to standard output unless an output '
            'file is given.'
            )
        )
    shift_command.add_argument(
        'file',
        metavar='PATH',
        help='WebVTT file, or - to read standard input'
        )
    shift_command.add_argument(
        'offset',
        metavar='OFFSET',
        type=_offset,
        help=('seconds to shift the captions by, negative values move them '
              'earlier, e.g. 2 or -1.5')
        )
    shift_command.add_argument(
        '-o', '--output',
        metavar='PATH',
        help='output file, can be the same as the input file'
        )
    shift_command.add_argument(
        '-s', '--start',
        metavar='TIMESTAMP',
        type=_timestamp,
        help='only shift the captions starting at or after this timestamp'
        )
    shift_command.add_argument(
        '--drop-before-zero',
        action='store_true',
        help=('remove the captions that end at or before 00:00:00.000 after '
              'shifting them, as they are never shown')
        )
    shift_command.set_defaults(run=_shift)

    sync_command = commands.add_parser(
        'sync',
        help='synchronize a WebVTT file that drifts out of sync',
        description=(
            'Synchronize the captions in a WebVTT file to two or more points '
            'or to a different frame rate.'
            ),
        epilog=(
            'Times between two points are moved along the line between them, '
            'and times before the first or after the last point along the '
            'line of the outermost points. Times are rounded to the nearest '
            'millisecond, halves away from zero, and a time that would fall '
            'before zero is set to 00:00:00.000. The captions are written to '
            'standard output unless an output file is given.'
            )
        )
    sync_command.add_argument(
        'file',
        metavar='PATH',
        help='WebVTT file, or - to read standard input'
        )
    timing = sync_command.add_mutually_exclusive_group(required=True)
    timing.add_argument(
        '-p', '--point',
        metavar=('FROM', 'TO'),
        nargs=2,
        type=_position,
        action='append',
        dest='points',
        help=('move the time FROM in the captions to TO, as a timestamp or '
              'seconds; repeat it for two or more points')
        )
    timing.add_argument(
        '--fps',
        metavar=('FROM', 'TO'),
        nargs=2,
        type=_fps,
        help=('change the timing from the frame rate FROM to TO, '
              'e.g. 25 23.976 or 25 24000/1001')
        )
    sync_command.add_argument(
        '-o', '--output',
        metavar='PATH',
        help='output file, can be the same as the input file'
        )
    sync_command.set_defaults(run=_sync)

    args = arguments.parse_args(argv)
    _check_arguments(arguments, sync_command, args)

    name = 'standard input' if args.file == _STDIN else args.file
    try:
        args.run(args)
    except OSError as error:
        message = f'{error.filename or name}: {error.strerror or error}'
    except UnicodeDecodeError as error:
        message = f'{name}: cannot be decoded as {error.encoding}'
    except MalformedFileError:
        message = f'{name}: not a valid WebVTT file'
    except ValueError as error:
        # the captions cannot be moved as asked, e.g. after the largest
        # timestamp
        message = f'{name}: {error}'
    except MissingFilenameError:
        # the output is a directory, and standard input has no file name
        # to save to in it
        message = (f'{args.output}: is a directory, give a file name to '
                   'save the captions read from standard input')
    else:
        return

    arguments.exit(1, f'{arguments.prog}: error: {message}\n')


def _check_arguments(
        parser: argparse.ArgumentParser,
        sync_parser: argparse.ArgumentParser,
        args: argparse.Namespace
        ):
    """Exit with an error if the arguments cannot be used."""
    if args.command == 'sync':
        _check_sync_points(sync_parser, args.points)
    elif args.command == 'segment' and not args.overwrite:
        _check_output(parser, args.output)


def _check_sync_points(
        parser: argparse.ArgumentParser,
        points: typing.Optional[typing.List[typing.List[typing.Any]]]
        ):
    """Exit with a usage error if the sync points cannot be used."""
    try:
        if points:
            _sync_mapping(points)
    except ValueError as error:
        parser.error(str(error))


def _check_output(parser: argparse.ArgumentParser, output: str):
    """Exit with an error if the output has the files of an earlier run."""
    try:
        earlier_file = segmenter._earlier_output(pathlib.Path(output))
    except OSError:
        # reported as the other errors when segmenting
        return
    if earlier_file:
        parser.exit(
            1,
            f'{parser.prog}: error: {output}: has the files of an earlier '
            f'segmentation, such as {earlier_file}; use --overwrite to '
            'replace them\n'
            )


def _segment(args: argparse.Namespace):
    """Run the segment command."""
    segmenter.segment(
        _read(args.file),
        args.output,
        args.target_duration,
        args.mpegts,
        overwrite=args.overwrite,
        duration=args.duration
        )


def _shift(args: argparse.Namespace):
    """Run the shift command."""
    vtt = _read(args.file)
    vtt.shift(args.offset, start=args.start,
              drop_before_zero=args.drop_before_zero)
    _write(vtt, args.output)


def _sync(args: argparse.Namespace):
    """Run the sync command."""
    vtt = _read(args.file)
    if args.points:
        vtt.sync(*args.points)
    else:
        vtt.change_framerate(*args.fps)
    _write(vtt, args.output)


def _read(path: str) -> WebVTT:
    """Read the captions of a file, or of standard input for ``-``."""
    if path != _STDIN:
        return WebVTT.read(path)

    if sys.stdin is None:
        # standard input is closed, as in ``webvtt shift - 1 <&-``
        raise OSError(errno.EBADF, os.strerror(errno.EBADF))

    # read the bytes, decoded as UTF-8 as WebVTT requires, whatever the
    # encoding of standard input is
    return WebVTT.from_buffer(getattr(sys.stdin, 'buffer', sys.stdin))


def _write(vtt: WebVTT, output: typing.Optional[str]):
    """Save the captions to the output file or standard output."""
    if output:
        vtt.save(output)
    else:
        _write_stdout(vtt.content)


def _write_stdout(content: str):
    """
    Write WebVTT content to standard output.

    The content is encoded in UTF-8 as WebVTT requires, whatever the
    encoding of standard output is.
    """
    try:
        if hasattr(sys.stdout, 'buffer'):
            sys.stdout.flush()
            sys.stdout.buffer.write(content.encode('utf-8'))
        else:
            sys.stdout.write(content)
        sys.stdout.flush()
    except BrokenPipeError:
        # the reader stopped early, as in ``webvtt shift ... | head``;
        # point standard output to devnull so Python does not fail again
        # flushing it at exit
        os.dup2(os.open(os.devnull, os.O_WRONLY), sys.stdout.fileno())
        sys.exit(1)


def _offset(value: str) -> float:
    """
    Return the offset in seconds of a command line argument.

    ``WebVTT.shift`` rounds the offset to the nearest millisecond as
    written, e.g. ``1.0005`` is 1001 milliseconds.
    """
    offset = _number(value)
    if not math.isfinite(offset):
        raise argparse.ArgumentTypeError(f'invalid offset: {value!r}')

    return offset


def _position(value: str) -> typing.Union[str, float]:
    """Return a timestamp or a number of seconds of a command line argument."""
    try:
        return _timestamp(value)
    except argparse.ArgumentTypeError:
        seconds = _number(value)

    if not math.isfinite(seconds) or seconds < 0:
        raise argparse.ArgumentTypeError(f'invalid timestamp: {value!r}')

    return seconds


def _fps(value: str) -> fractions.Fraction:
    """
    Return the frame rate of a command line argument.

    The frame rate is read exactly as written, as a number such as
    ``23.976`` or a ratio such as ``24000/1001``.
    """
    try:
        fps = fractions.Fraction(value)
    except (ValueError, ZeroDivisionError):
        fps = fractions.Fraction(0)

    if fps <= 0:
        raise argparse.ArgumentTypeError(f'invalid frame rate: {value!r}')

    return fps


def _duration(value: str) -> int:
    """Return the segment duration of a command line argument."""
    try:
        seconds = int(value)
        segmenter._check_seconds(seconds)
    except ValueError:
        raise argparse.ArgumentTypeError(f'invalid duration: {value!r}')

    return seconds


def _media_duration(value: str) -> typing.Union[str, float]:
    """Return the length of the media of a command line argument."""
    try:
        duration = _position(value)
        segmenter._duration_in_milliseconds(duration)
    except (argparse.ArgumentTypeError, ValueError):
        raise argparse.ArgumentTypeError(f'invalid duration: {value!r}')

    return duration


def _mpegts(value: str) -> int:
    """Return the MPEG-TS value of a command line argument."""
    try:
        mpegts = int(value)
        segmenter._check_mpegts(mpegts)
    except ValueError:
        raise argparse.ArgumentTypeError(f'invalid MPEG-TS value: {value!r}')

    return mpegts


def _number(value: str) -> float:
    """Return a command line argument as a float, NaN if not a number."""
    try:
        return float(value)
    except ValueError:
        return math.nan


def _timestamp(value: str) -> str:
    """Return a command line argument after validating the timestamp."""
    try:
        Timestamp.from_string(value)
    except MalformedCaptionError:
        raise argparse.ArgumentTypeError(f'invalid timestamp: {value!r}')

    return value


if __name__ == '__main__':
    main()  # pragma: no cover
