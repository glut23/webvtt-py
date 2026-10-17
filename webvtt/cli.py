"""CLI module."""

import argparse
import typing

from . import segmenter
from .errors import MalformedFileError


def main(argv: typing.Optional[typing.Sequence] = None):
    """
    Segment WebVTT file from command line.

    :param argv: command line arguments
    """
    arguments = argparse.ArgumentParser(
        prog='webvtt',
        description='Segment WebVTT files for HTTP Live Streaming (HLS).',
        epilog=(
            'The output directory will contain a playlist named '
            'prog_index.m3u8 and one fileSequenceN.webvtt file per segment. '
            'Captions spanning multiple segments are included in each of '
            'them.'
            )
        )
    arguments.add_argument(
        'command',
        choices=['segment'],
        help='command to perform'
        )
    arguments.add_argument(
        'file',
        metavar='PATH',
        help='WebVTT file'
        )
    arguments.add_argument(
        '-o', '--output',
        metavar='PATH',
        required=True,
        help='output directory, created if it does not exist'
        )
    arguments.add_argument(
        '-d', '--target-duration',
        metavar='NUMBER',
        type=int,
        default=segmenter.DEFAULT_SECONDS,
        help='target duration of each segment in seconds, default: %(default)s'
        )
    arguments.add_argument(
        '-m', '--mpegts',
        metavar='NUMBER',
        type=int,
        default=segmenter.DEFAULT_MPEGTS,
        help=('MPEG-TS value for the X-TIMESTAMP-MAP header of each segment, '
              'default: %(default)s')
        )

    args = arguments.parse_args(argv)

    try:
        segmenter.segment(
            args.file,
            args.output,
            args.target_duration,
            args.mpegts
            )
    except OSError as error:
        message = f'{error.filename or args.file}: {error.strerror or error}'
    except UnicodeDecodeError as error:
        message = f'{args.file}: cannot be decoded as {error.encoding}'
    except MalformedFileError:
        message = f'{args.file}: not a valid WebVTT file'
    else:
        return

    arguments.exit(1, f'{arguments.prog}: error: {message}\n')


if __name__ == '__main__':
    main()  # pragma: no cover
