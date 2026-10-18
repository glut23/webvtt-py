"""CLI module."""

import argparse
import math
import sys
import typing

from . import segmenter
from .webvtt import WebVTT
from .models import Timestamp
from .errors import MalformedFileError, MalformedCaptionError


def main(argv: typing.Optional[typing.Sequence] = None):
    """
    Segment or shift a WebVTT file from command line.

    :param argv: command line arguments
    """
    arguments = argparse.ArgumentParser(
        prog='webvtt',
        description='Segment and shift WebVTT caption files.'
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
            'them.'
            )
        )
    segment_command.add_argument(
        'file',
        metavar='PATH',
        help='WebVTT file'
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
        type=int,
        default=segmenter.DEFAULT_SECONDS,
        help='target duration of each segment in seconds, default: %(default)s'
        )
    segment_command.add_argument(
        '-m', '--mpegts',
        metavar='NUMBER',
        type=int,
        default=segmenter.DEFAULT_MPEGTS,
        help=('MPEG-TS value for the X-TIMESTAMP-MAP header of each segment, '
              'default: %(default)s')
        )
    segment_command.set_defaults(run=_segment)

    shift_command = commands.add_parser(
        'shift',
        help='shift the timestamps of a WebVTT file',
        description='Shift the timestamps of the captions in a WebVTT file.',
        epilog=(
            'The offset is rounded to the nearest millisecond and a '
            'timestamp that would fall before zero is set to 00:00:00.000. '
            'The captions are written to standard output unless an output '
            'file is given.'
            )
        )
    shift_command.add_argument(
        'file',
        metavar='PATH',
        help='WebVTT file'
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
    shift_command.set_defaults(run=_shift)

    args = arguments.parse_args(argv)

    try:
        args.run(args)
    except OSError as error:
        message = f'{error.filename or args.file}: {error.strerror or error}'
    except UnicodeDecodeError as error:
        message = f'{args.file}: cannot be decoded as {error.encoding}'
    except MalformedFileError:
        message = f'{args.file}: not a valid WebVTT file'
    else:
        return

    arguments.exit(1, f'{arguments.prog}: error: {message}\n')


def _segment(args: argparse.Namespace):
    """Run the segment command."""
    segmenter.segment(
        args.file,
        args.output,
        args.target_duration,
        args.mpegts
        )


def _shift(args: argparse.Namespace):
    """Run the shift command."""
    vtt = WebVTT.read(args.file)
    vtt.shift(args.offset, start=args.start)

    if args.output:
        vtt.save(args.output)
    else:
        sys.stdout.write(vtt.content)


def _offset(value: str) -> float:
    """Return the offset in seconds of a command line argument."""
    try:
        offset = float(value)
    except ValueError:
        offset = math.nan

    if not math.isfinite(offset):
        raise argparse.ArgumentTypeError(f'invalid offset: {value!r}')

    return offset


def _timestamp(value: str) -> str:
    """Return a command line argument after validating the timestamp."""
    try:
        Timestamp.from_string(value)
    except MalformedCaptionError:
        raise argparse.ArgumentTypeError(f'invalid timestamp: {value!r}')

    return value


if __name__ == '__main__':
    main()  # pragma: no cover
