"""CLI module."""

import argparse
import codecs
import errno
import fractions
import io
import math
import os
import pathlib
import sys
import typing
from collections.abc import Callable, Sequence

from . import __version__, segmenter
from .webvtt import WebVTT, _FORMAT_EXTENSIONS, _FORMATS
from .models import Timestamp, _sync_mapping
from .errors import (
    MalformedFileError, MalformedCaptionError, MissingFilenameError
    )

# the path that reads the captions from standard input
_STDIN = '-'

_FORMAT_NAMES = {'vtt': 'WebVTT', 'srt': 'SRT', 'sbv': 'SBV'}

# the format of a file with each extension
_EXTENSION_FORMATS = {
    extension: format
    for format, extensions in _FORMAT_EXTENSIONS.items()
    for extension in extensions
    }


def main(argv: Sequence[str] | None = None) -> None:
    """
    Segment, shift, sync, validate or convert captions from command line.

    :param argv: command line arguments
    """
    arguments = argparse.ArgumentParser(
        prog='webvtt',
        description=('Segment, shift, sync, validate and convert WebVTT, '
                     'SRT and SBV caption files.')
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
        help='segment captions for HLS',
        description=('Segment captions into WebVTT files for HTTP Live '
                     'Streaming (HLS).'),
        epilog=(
            'The output directory will contain a playlist named '
            'prog_index.m3u8 and one fileSequenceN.webvtt file per segment. '
            'Captions spanning multiple segments are included in each of '
            'them. An output directory with the files of an earlier run is '
            'an error unless --overwrite is given.'
            )
        )
    _add_input_arguments(segment_command)
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
        help='shift the timestamps of captions',
        description='Shift the timestamps of the captions in a file.',
        epilog=(
            'The offset is rounded to the nearest millisecond, halves away '
            'from zero, and a timestamp that would fall before zero is set '
            'to 00:00:00.000, so captions that end at or before zero are '
            'kept at 00:00:00.000 unless --drop-before-zero is given. '
            + _OUTPUT_EPILOG
            )
        )
    _add_input_arguments(shift_command)
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
        help=('output file, can be the same as the input file, in the '
              'format of its extension, or else of the input')
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
        help='synchronize captions that drift out of sync',
        description=(
            'Synchronize the captions in a file to two or more points or to '
            'a different frame rate.'
            ),
        epilog=(
            'Times between two points are moved along the line between them, '
            'and times before the first or after the last point along the '
            'line of the outermost points. Times are rounded to the nearest '
            'millisecond, halves away from zero, and a time that would fall '
            'before zero is set to 00:00:00.000. ' + _OUTPUT_EPILOG
            )
        )
    _add_input_arguments(sync_command)
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
        help=('output file, can be the same as the input file, in the '
              'format of its extension, or else of the input')
        )
    sync_command.set_defaults(run=_sync)

    validate_command = commands.add_parser(
        'validate',
        help='check captions for problems',
        description='Check the captions in a file for problems.',
        epilog=(
            'Each problem is printed on its own line: the blocks skipped '
            'when reading the file, and the captions out of order, not '
            'ending after they start or in a region that is not defined, '
            'which are errors, and the captions that overlap or have no '
            'text, which are warnings. When there is no other error, a '
            'WebVTT file is also read with strict parsing, and its first '
            'error is printed. The exit status is 1 if there is any error, '
            'and 0 otherwise.'
            )
        )
    _add_input_arguments(validate_command)
    validate_command.set_defaults(run=_validate)

    _add_convert_command(commands)

    args = arguments.parse_args(argv)
    _check_arguments(arguments, sync_command, args)
    args.input_format = _input_format(args)

    name = _input_name(args.file)
    try:
        args.run(args)
    except OSError as error:
        message = f'{error.filename or name}: {error.strerror or error}'
    except UnicodeDecodeError as error:
        message = f'{name}: cannot be decoded as {error.encoding}'
    except MalformedFileError:
        message = (f'{name}: not a valid '
                   f'{_FORMAT_NAMES[args.input_format]} file')
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


_OUTPUT_EPILOG = (
    'The captions are written to standard output, in the format of the '
    'input, unless an output file is given. The formatting of the cue text '
    'is kept when writing SRT.'
    )


def _add_input_arguments(parser: argparse.ArgumentParser) -> None:
    """Add the arguments of the input of a command."""
    parser.add_argument(
        'file',
        metavar='PATH',
        help='caption file, or - to read standard input'
        )
    parser.add_argument(
        '-f', '--format',
        choices=_FORMATS,
        help=('format of the input, default: from the extension of PATH, '
              '.srt for srt and .sbv for sbv, or else vtt')
        )
    parser.add_argument(
        '--encoding',
        metavar='ENCODING',
        type=_encoding,
        help=('encoding of an input without a Byte Order Mark, '
              'default: utf-8')
        )


def _add_convert_command(commands: typing.Any) -> None:
    """Add the convert command."""
    convert_command = commands.add_parser(
        'convert',
        help='convert captions to another format',
        description='Convert captions between WebVTT, SRT and SBV.',
        epilog=(
            'The output format is the one given with --to, or else the one '
            'of the extension of the output file, or else vtt. The captions '
            'are written to standard output unless an output file is given.'
            )
        )
    _add_input_arguments(convert_command)
    convert_command.add_argument(
        '-o', '--output',
        metavar='PATH',
        help='output file'
        )
    convert_command.add_argument(
        '-t', '--to',
        choices=_FORMATS,
        help='format of the output'
        )
    convert_command.add_argument(
        '--keep-formatting',
        action='store_true',
        help=('when writing SRT, keep bold, italic, underline and the '
              'colours of the styles, instead of removing the cue tags')
        )
    convert_command.set_defaults(run=_convert)


def _check_arguments(
        parser: argparse.ArgumentParser,
        sync_parser: argparse.ArgumentParser,
        args: argparse.Namespace
        ) -> None:
    """Exit with an error if the arguments cannot be used."""
    if args.command == 'sync':
        _check_sync_points(sync_parser, args.points)
    elif args.command == 'segment' and not args.overwrite:
        _check_output(parser, args.output)


def _check_sync_points(
        parser: argparse.ArgumentParser,
        points: list[list[typing.Any]] | None
        ) -> None:
    """Exit with a usage error if the sync points cannot be used."""
    try:
        if points:
            _sync_mapping(points)
    except ValueError as error:
        parser.error(str(error))


def _check_output(parser: argparse.ArgumentParser, output: str) -> None:
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


def _segment(args: argparse.Namespace) -> None:
    """Run the segment command."""
    segmenter.segment(
        _read(args),
        args.output,
        args.target_duration,
        args.mpegts,
        overwrite=args.overwrite,
        duration=args.duration
        )


def _shift(args: argparse.Namespace) -> None:
    """Run the shift command."""
    vtt = _read(args)
    vtt.shift(args.offset, start=args.start,
              drop_before_zero=args.drop_before_zero)
    _write(vtt, args.output, _edited_format(args), keep_formatting=True)


def _sync(args: argparse.Namespace) -> None:
    """Run the sync command."""
    vtt = _read(args)
    if args.points:
        vtt.sync(*args.points)
    else:
        vtt.change_framerate(*args.fps)
    _write(vtt, args.output, _edited_format(args), keep_formatting=True)


def _convert(args: argparse.Namespace) -> None:
    """Run the convert command."""
    output_format = (args.to or
                     (args.output and _path_format(args.output)) or
                     'vtt')
    _write(_read(args), args.output, output_format, args.keep_formatting)


def _input_format(args: argparse.Namespace) -> str:
    """Return the format of the input, given or of its extension."""
    return args.format or _path_format(args.file) or 'vtt'


def _edited_format(args: argparse.Namespace) -> str:
    """Return the format to write the edited captions in."""
    return ((args.output and _path_format(args.output)) or
            args.input_format)


def _path_format(path: str) -> str | None:
    """Return the format of the extension of a path, if it has one."""
    return _EXTENSION_FORMATS.get(os.path.splitext(path)[1].lower())


def _validate(args: argparse.Namespace) -> None:
    """Run the validate command, exiting with status 1 if there are errors."""
    read = _reader(args)
    name = _input_name(args.file)
    vtt = read(False)
    issues = vtt.validate()

    lines = [
        f'{name}: line {issue.line}: error: {issue.message}'
        for issue in vtt.parse_issues
        ]
    lines.extend(f'{name}: {issue}' for issue in issues)
    has_errors = bool(vtt.parse_issues) or any(
        issue.severity == 'error' for issue in issues
        )

    if not has_errors:
        # strict parsing also finds problems in blocks that are still read,
        # such as cue settings that are not valid, but stops at the first
        # one, so it is only needed when nothing else is an error
        strict_error = _strict_error(read, args.input_format)
        if strict_error:
            lines.append(f'{name}: {strict_error}')
            has_errors = True

    if lines:
        _write_stdout(''.join(f'{line}\n' for line in lines))
    if has_errors:
        sys.exit(1)


def _reader(args: argparse.Namespace) -> Callable[[bool], WebVTT]:
    """
    Return a function reading the captions of the input, strict or not.

    The input is read in its format and encoding. Standard input is read
    once, as it cannot be read again, and the function reads its content
    each time. Strict parsing is only for WebVTT.
    """
    path, format, encoding = args.file, args.input_format, args.encoding
    if path != _STDIN:
        if format == 'srt':
            return lambda strict: WebVTT.from_srt(path, encoding)
        if format == 'sbv':
            return lambda strict: WebVTT.from_sbv(path, encoding)
        return lambda strict: WebVTT.read(path, encoding, strict)

    data = _stdin().read()
    return lambda strict: WebVTT.from_buffer(
        io.BytesIO(data) if isinstance(data, bytes) else io.StringIO(data),
        format=format,
        strict=strict,
        encoding=encoding
        )


def _strict_error(
        read: Callable[[bool], WebVTT],
        format: str
        ) -> str | None:
    """
    Return the first error of strict parsing, as ``line N: error: MESSAGE``.

    :param read: the function reading the captions, strict or not
    :param format: the format of the captions
    :returns: the error, or None if strict parsing reads the captions or
        the format is not WebVTT, as SRT and SBV have no strict parsing
    """
    if format != 'vtt':
        return None
    try:
        read(True)
    except (MalformedFileError, MalformedCaptionError) as error:
        # the messages start with the line number, as in "line 3: ..."
        location, _, message = str(error).partition(': ')
        return f'{location}: error: {message}'
    return None


def _input_name(path: str) -> str:
    """Return how the input is named in messages."""
    return 'standard input' if path == _STDIN else path


def _stdin() -> typing.IO[typing.Any]:
    """
    Return standard input to read the captions from.

    The bytes are read when possible, decoded as UTF-8, or the encoding
    given, whatever the encoding of standard input is.

    :raises OSError: if standard input is closed
    """
    if sys.stdin is None:
        # standard input is closed, as in ``webvtt shift - 1 <&-``
        raise OSError(errno.EBADF, os.strerror(errno.EBADF))

    return getattr(sys.stdin, 'buffer', sys.stdin)


def _read(args: argparse.Namespace) -> WebVTT:
    """Read the captions of a file, or of standard input for ``-``."""
    return _reader(args)(False)


def _write(
        vtt: WebVTT,
        output: str | None,
        format: str,
        keep_formatting: bool
        ) -> None:
    """
    Save the captions to the output file or standard output in a format.

    :param vtt: the captions
    :param output: the output file, or None for standard output
    :param format: the format to write
    :param keep_formatting: keep the formatting when writing SRT
    """
    if not output:
        _write_stdout(vtt.to_string(format, keep_formatting))
    elif format == 'srt':
        vtt.save_as_srt(output, keep_formatting=keep_formatting)
    elif format == 'sbv':
        vtt.save_as_sbv(output)
    else:
        vtt.save(output)


def _write_stdout(content: str) -> None:
    """
    Write content to standard output.

    The content is encoded in UTF-8, whatever the encoding of standard
    output is.
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


def _position(value: str) -> str | float:
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


def _media_duration(value: str) -> str | float:
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


def _encoding(value: str) -> str:
    """
    Return an encoding of a command line argument after looking it up.

    Codecs such as ``hex`` are found but cannot decode text, as
    ``bytes.decode`` tells by the same flag of the codec.
    """
    try:
        codec = codecs.lookup(value)
    except LookupError:
        codec = None
    if codec is None or not getattr(codec, '_is_text_encoding', True):
        raise argparse.ArgumentTypeError(f'unknown encoding: {value!r}')

    return value


def _timestamp(value: str) -> str:
    """Return a command line argument after validating the timestamp."""
    try:
        Timestamp.from_string(value)
    except MalformedCaptionError:
        raise argparse.ArgumentTypeError(f'invalid timestamp: {value!r}')

    return value


if __name__ == '__main__':
    main()  # pragma: no cover
